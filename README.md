# AIOps Log Anomaly Detector

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)
![AWS](https://img.shields.io/badge/AWS-EC2-FF9900?style=for-the-badge&logo=amazonaws)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes)

**LLM-powered log anomaly detection — deployed live on AWS EC2**

---

## 🚀 What This Project Does

Production-grade AIOps system that automatically detects anomalies in Kubernetes logs using a local LLM.

- 📥 Fetches logs from Grafana Loki every 5 minutes using LogQL queries
- 🧠 Analyzes logs using local LLM (Ollama/LLaMA3) — zero API cost, no data leaving cluster
- 📊 Returns structured JSON — anomaly detected, confidence score, severity, affected services
- 🚨 Fires alerts to Alertmanager automatically when anomalies are detected
- 📈 Exposes Prometheus metrics for full observability of the detector itself

> ✅ **Real Result:** Detected critical database failure with **0.8 confidence score**, classified as `severity=critical`, and fired alert to Alertmanager within **17 seconds**

---

## 📸 Live Demo — Running on AWS EC2

### ✅ All 6 Containers Running Healthy
![docker-ps](https://github.com/Pa123313/aiops-anomaly-detector/blob/main/docs/screenshots/docker-ps.png?raw=true)

### 🚨 Alertmanager — AIOpsAnomalyDetected Alert Fired
![alertmanager](https://github.com/Pa123313/aiops-anomaly-detector/blob/main/docs/screenshots/alertmanager-alert.png?raw=true)

### 📊 Prometheus — aiops_anomalies_detected_total = 1
![prometheus](https://github.com/Pa123313/aiops-anomaly-detector/blob/main/docs/screenshots/prometheus-metrics.png?raw=true)

---

## 🏗️ Architecture
Application Pods (production namespace)
│
│ logs via OTLP
▼
Grafana Loki :3100
│
│ LogQL query every 5 mins
▼
┌─────────────────────────────┐
│   AIOps Anomaly Detector    │
│  1. Fetch logs  (Loki API)  │
│  2. Send to LLM (Ollama)    │
│  3. Parse JSON response     │
│  4. Fire alert if anomaly   │
│  5. Expose /metrics         │
└──────────┬──────────────────┘
│
┌─────┴──────┐
▼            ▼
Alertmanager  Prometheus
(alerts)      → Grafana

---

## ✨ Features

| Feature | Details |
|---|---|
| 🧠 **Local LLM** | Ollama (LLaMA3) — runs fully offline, zero API cost |
| 📋 **Structured Output** | LLM responds in strict JSON — anomaly, confidence, severity, affected services |
| 🎯 **Smart Filtering** | Configurable confidence threshold (default 0.7) to reduce false positives |
| 📊 **Prometheus Metrics** | Scans, anomalies, LLM latency histogram, confidence scores |
| ☸️ **Kubernetes Ready** | Helm chart with resource limits, probes, non-root security context |
| 🔒 **Secure Build** | Multi-stage Docker build, non-root user (UID 1001) |
| 🔁 **CI/CD Pipeline** | GitHub Actions: lint → Trivy scan → build → GHCR push → Helm deploy |
| 🛡️ **Security Scanning** | Trivy blocks CRITICAL/HIGH CVEs before deployment |

---

## ⚡ Quick Start (Local)

```bash
# 1. Clone the repo
git clone https://github.com/Pa123313/aiops-anomaly-detector.git
cd aiops-anomaly-detector

# 2. Start the full stack
docker-compose up -d

# 3. Pull LLM model
docker exec -it ollama ollama pull llama3.2:1b

# 4. Send test logs to trigger anomaly detection
curl -X POST http://localhost:3100/loki/api/v1/push \
  -H "Content-Type: application/json" \
  -d '{"streams": [{"stream": {"namespace": "production"}, "values": [["'"$(date +%s)"'000000000", "ERROR: Database connection failed"]]}]}'

# 5. Watch the LLM detect the anomaly
docker logs -f aiops-detector

# 6. Open Grafana
open http://localhost:3000   # admin / admin
```

---

## ☸️ Deploy to Kubernetes (Helm)

```bash
helm upgrade --install aiops-detector ./helm/aiops-detector \
  --namespace aiops \
  --create-namespace \
  --set image.tag=latest \
  --wait
```

---

## 🔧 Configuration

| Variable | Default | Description |
|---|---|---|
| `LOKI_URL` | `http://loki:3100` | Loki endpoint |
| `OLLAMA_URL` | `http://ollama:11434` | Ollama LLM endpoint |
| `OLLAMA_MODEL` | `llama3.2:1b` | LLM model to use |
| `ALERTMANAGER_URL` | `http://alertmanager:9093` | Alertmanager endpoint |
| `SCAN_INTERVAL` | `300` | Seconds between scans |
| `ANOMALY_THRESHOLD` | `0.7` | Minimum confidence to fire alert |

---

## 📈 Prometheus Metrics

| Metric | Type | Description |
|---|---|---|
| `aiops_scans_total` | Counter | Total scan cycles run |
| `aiops_anomalies_detected_total` | Counter | Total anomalies detected |
| `aiops_alerts_fired_total` | Counter | Total alerts sent to Alertmanager |
| `aiops_llm_latency_seconds` | Histogram | LLM inference latency |
| `aiops_last_anomaly_score` | Gauge | Confidence score of last anomaly |

---

## 🔁 CI/CD Pipeline
Push to main
├── 1. Lint (flake8)
├── 2. Trivy security scan
├── 3. Build multi-arch image (amd64 + arm64)
├── 4. Push to GHCR
└── 5. Helm deploy to Kubernetes

---

## 🛠️ Tech Stack

`Python 3.12` · `Ollama (LLaMA3)` · `Grafana Loki` · `Prometheus` · `Alertmanager` · `Grafana` · `Docker` · `Kubernetes` · `Helm` · `GitHub Actions` · `Trivy` · `AWS EC2`

---

## 👩‍💻 Author

**Pavithra A S** — DevOps Engineer

[![GitHub](https://img.shields.io/badge/GitHub-Pa123313-181717?style=flat&logo=github)](https://github.com/Pa123313)
[![Email](https://img.shields.io/badge/Email-Contact-D14836?style=flat&logo=gmail)](mailto:Pavithraannur1234@gmail.com)
