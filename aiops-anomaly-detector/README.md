# 🤖 AIOps Log Anomaly Detector

> **LLM-powered log anomaly detection for Kubernetes — built for production.**

Automatically fetches logs from **Grafana Loki**, analyzes them with a **local LLM (Ollama/LLaMA3)**, exposes **Prometheus metrics**, and fires alerts to **Alertmanager** when anomalies are detected — all running inside Kubernetes.

---

## Architecture

┌──────────────────────────────────────────────────────────────────┐
│  Kubernetes Cluster                                               │
│                                                                  │
│  ┌──────────────────────┐    ┌──────────────────────────────┐   │
│  │  Application Pods     │───▶│  Grafana Loki (log storage)  │   │
│  │  (production ns)      │    └──────────────┬───────────────┘   │
│  └──────────────────────┘                   │ query logs         │
│                                             ▼                    │
│                              ┌──────────────────────────────┐   │
│                              │  AIOps Anomaly Detector       │   │
│                              │  ┌──────────────────────────┐ │   │
│                              │  │  1. Fetch logs (Loki API) │ │   │
│                              │  │  2. Send to LLM (Ollama)  │ │   │
│                              │  │  3. Parse JSON response   │ │   │
│                              │  │  4. Fire alert if anomaly │ │   │
│                              │  │  5. Expose /metrics       │ │   │
│                              │  └──────────────────────────┘ │   │
│                              └──────┬───────────────┬─────────┘   │
│                                     │               │             │
│                    ┌────────────────▼─┐   ┌────────▼──────────┐  │
│                    │  Ollama (LLaMA3)  │   │  Alertmanager     │  │
│                    │  Local LLM engine │   │  → Slack / Email  │  │
│                    └──────────────────┘   └───────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Prometheus scrapes /metrics → Grafana dashboard          │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Details |
|---|---|
| **LLM Analysis** | Ollama (LLaMA3) running locally — no API costs, no data leaving cluster |
| **Structured Output** | LLM responds in strict JSON: anomaly, confidence, severity, affected services |
| **Tail Sampling aware** | Queries same Loki instance as Grafana LGTM stack |
| **Prometheus metrics** | Scans, anomalies, LLM latency, confidence scores |
| **Helm chart** | Production-ready deployment with resource limits and non-root security |
| **CI/CD** | GitHub Actions: lint → Trivy scan → build → push GHCR → Helm deploy |
| **Alert rules** | 3 Prometheus alert rules for anomaly detection, detector downtime, anomaly rate |

---

## Quick Start (Local)

```bash
# 1. Clone the repo
git clone https://github.com/Pa123313/aiops-anomaly-detector.git
cd aiops-anomaly-detector

# 2. Start the full stack (pulls LLaMA3 ~4GB on first run)
docker compose up -d

# 3. Watch detector logs
docker logs -f aiops-detector

# 4. Open Grafana
open http://localhost:3000   # admin / admin

# 5. Check Prometheus metrics
curl http://localhost:8000/metrics
```

---

## Deploy to Kubernetes (Helm)

```bash
# Add your image tag from CI
helm upgrade --install aiops-detector ./helm/aiops-detector \
  --namespace aiops \
  --create-namespace \
  --set image.tag=sha-abc1234 \
  --wait
```

---

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `LOKI_URL` | `http://loki:3100` | Loki endpoint |
| `OLLAMA_URL` | `http://ollama:11434` | Ollama LLM endpoint |
| `OLLAMA_MODEL` | `llama3` | Model to use |
| `ALERTMANAGER_URL` | `http://alertmanager:9093` | Alertmanager endpoint |
| `SCAN_INTERVAL` | `300` | Seconds between scans |
| `LOG_LOOKBACK` | `5` | Minutes of logs to fetch per scan |
| `LOKI_QUERY` | `{namespace="production"}` | LogQL query |
| `ANOMALY_THRESHOLD` | `0.7` | Minimum LLM confidence to fire alert |

---

## Prometheus Metrics

| Metric | Type | Description |
|---|---|---|
| `aiops_scans_total` | Counter | Total scan cycles run |
| `aiops_anomalies_detected` | Counter | Total anomalies found |
| `aiops_alerts_fired` | Counter | Total alerts sent to Alertmanager |
| `aiops_llm_latency_seconds` | Histogram | LLM inference time |
| `aiops_last_anomaly_score` | Gauge | Confidence score of last anomaly |
| `aiops_last_scan_timestamp` | Gauge | Unix timestamp of last scan |

---

## CI/CD Pipeline

```
Push to main
    │
    ├─ 1. Lint & Test (flake8)
    ├─ 2. Trivy container security scan (blocks on CRITICAL/HIGH CVEs)
    ├─ 3. Build & push multi-arch image to GHCR (amd64 + arm64)
    └─ 4. Helm deploy to Kubernetes with rollout verification
```

---

## Tech Stack

`Python` · `Ollama (LLaMA3)` · `Grafana Loki` · `Prometheus` · `Alertmanager` · `Grafana` · `Docker` · `Kubernetes` · `Helm` · `GitHub Actions` · `Trivy`

---

## Author

**Pavithra A S** — DevOps Engineer  
[GitHub](https://github.com/Pa123313) · [Email](mailto:Pavithraannur1234@gmail.com)
