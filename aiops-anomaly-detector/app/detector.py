"""
AIOps Log Anomaly Detector
Queries Loki for recent logs, analyzes with LLM (Ollama),
and fires alerts to Alertmanager when anomalies are detected.
"""

import os
import json
import time
import logging
import requests
from datetime import datetime, timezone, timedelta
from prometheus_client import start_http_server, Counter, Gauge, Histogram

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── Config from environment ────────────────────────────────────────────────────
LOKI_URL          = os.getenv("LOKI_URL",          "http://loki:3100")
OLLAMA_URL        = os.getenv("OLLAMA_URL",         "http://ollama:11434")
OLLAMA_MODEL      = os.getenv("OLLAMA_MODEL",       "llama3")
ALERTMANAGER_URL  = os.getenv("ALERTMANAGER_URL",   "http://alertmanager:9093")
SCAN_INTERVAL_SEC = int(os.getenv("SCAN_INTERVAL",  "300"))   # 5 minutes
LOG_LOOKBACK_MIN  = int(os.getenv("LOG_LOOKBACK",   "5"))
LOKI_QUERY        = os.getenv("LOKI_QUERY",         '{namespace="production"}')
ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "0.7"))  # LLM confidence threshold
METRICS_PORT      = int(os.getenv("METRICS_PORT",   "8000"))

# ── Prometheus metrics ─────────────────────────────────────────────────────────
scans_total        = Counter("aiops_scans_total",        "Total log scan cycles run")
anomalies_detected = Counter("aiops_anomalies_detected", "Total anomalies detected by LLM")
alerts_fired       = Counter("aiops_alerts_fired",       "Total alerts sent to Alertmanager")
llm_latency        = Histogram("aiops_llm_latency_seconds", "LLM inference latency")
anomaly_score      = Gauge("aiops_last_anomaly_score",   "Confidence score of last anomaly")
last_scan_ts       = Gauge("aiops_last_scan_timestamp",  "Unix timestamp of last scan")


# ── Loki client ────────────────────────────────────────────────────────────────
def fetch_logs_from_loki() -> list[str]:
    """Pull log lines from Loki for the last LOG_LOOKBACK_MIN minutes."""
    now   = datetime.now(timezone.utc)
    start = now - timedelta(minutes=LOG_LOOKBACK_MIN)

    params = {
        "query": LOKI_QUERY,
        "start": str(int(start.timestamp() * 1e9)),   # nanoseconds
        "end":   str(int(now.timestamp()   * 1e9)),
        "limit": "200",
        "direction": "forward",
    }
    try:
        r = requests.get(f"{LOKI_URL}/loki/api/v1/query_range", params=params, timeout=15)
        r.raise_for_status()
        data   = r.json()
        lines  = []
        for stream in data.get("data", {}).get("result", []):
            for _, line in stream.get("values", []):
                lines.append(line)
        log.info(f"Fetched {len(lines)} log lines from Loki")
        return lines
    except Exception as e:
        log.error(f"Failed to fetch logs from Loki: {e}")
        return []


# ── LLM analysis ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert SRE (Site Reliability Engineer) analyzing application logs.
Your job is to detect anomalies, errors, performance issues, and security concerns.

Respond ONLY with a valid JSON object in this exact format:
{
  "anomaly_detected": true or false,
  "confidence": 0.0 to 1.0,
  "severity": "critical" or "warning" or "info",
  "summary": "one sentence summary of the issue",
  "affected_services": ["service1", "service2"],
  "recommended_action": "what the on-call engineer should do"
}

Do not include any text outside the JSON."""

def analyze_with_llm(log_lines: list[str]) -> dict:
    """Send log lines to Ollama for anomaly analysis."""
    if not log_lines:
        return {"anomaly_detected": False, "confidence": 0.0, "summary": "No logs to analyze"}

    log_text = "\n".join(log_lines[-100:])  # last 100 lines to stay within context
    prompt   = f"Analyze these application logs for anomalies:\n\n{log_text}"

    payload = {
        "model":  OLLAMA_MODEL,
        "system": SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1}   # low temp = consistent structured output
    }

    try:
        with llm_latency.time():
            r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
            r.raise_for_status()

        raw      = r.json().get("response", "{}")
        # Strip markdown code fences if model wraps JSON
        raw      = raw.strip().strip("```json").strip("```").strip()
        result   = json.loads(raw)
        log.info(f"LLM result: anomaly={result.get('anomaly_detected')}, "
                 f"confidence={result.get('confidence')}, severity={result.get('severity')}")
        return result
    except json.JSONDecodeError:
        log.warning(f"LLM returned non-JSON response: {raw[:200]}")
        return {"anomaly_detected": False, "confidence": 0.0, "summary": "LLM parse error"}
    except Exception as e:
        log.error(f"LLM call failed: {e}")
        return {"anomaly_detected": False, "confidence": 0.0, "summary": f"LLM error: {e}"}


# ── Alertmanager ──────────────────────────────────────────────────────────────
def fire_alert(analysis: dict):
    """Push an alert to Alertmanager."""
    severity  = analysis.get("severity", "warning")
    summary   = analysis.get("summary", "Anomaly detected")
    services  = ", ".join(analysis.get("affected_services", ["unknown"]))
    action    = analysis.get("recommended_action", "Investigate logs")
    score     = analysis.get("confidence", 0.0)

    alert_payload = [{
        "labels": {
            "alertname":  "AIOpsAnomalyDetected",
            "severity":   severity,
            "source":     "aiops-detector",
            "service":    services,
        },
        "annotations": {
            "summary":     summary,
            "description": f"LLM confidence: {score:.0%}. Action: {action}",
            "runbook_url": "https://github.com/your-org/runbooks/aiops-anomaly",
        },
        "endsAt": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    }]

    try:
        r = requests.post(
            f"{ALERTMANAGER_URL}/api/v1/alerts",
            json=alert_payload, timeout=10
        )
        r.raise_for_status()
        alerts_fired.inc()
        log.info(f"Alert fired to Alertmanager — severity={severity}")
    except Exception as e:
        log.error(f"Failed to fire alert: {e}")


# ── Main loop ─────────────────────────────────────────────────────────────────
def run():
    log.info(f"Starting AIOps Anomaly Detector — model={OLLAMA_MODEL}, "
             f"interval={SCAN_INTERVAL_SEC}s, query={LOKI_QUERY}")
    start_http_server(METRICS_PORT)
    log.info(f"Prometheus metrics exposed on :{METRICS_PORT}/metrics")

    while True:
        try:
            scans_total.inc()
            last_scan_ts.set(time.time())

            log_lines = fetch_logs_from_loki()
            analysis  = analyze_with_llm(log_lines)

            score = analysis.get("confidence", 0.0)
            anomaly_score.set(score)

            if analysis.get("anomaly_detected") and score >= ANOMALY_THRESHOLD:
                anomalies_detected.inc()
                log.warning(f"ANOMALY DETECTED: {analysis.get('summary')}")
                fire_alert(analysis)
            else:
                log.info("No anomaly detected in this scan cycle.")

        except Exception as e:
            log.error(f"Scan cycle error: {e}")

        log.info(f"Sleeping {SCAN_INTERVAL_SEC}s until next scan...")
        time.sleep(SCAN_INTERVAL_SEC)


if __name__ == "__main__":
    run()
