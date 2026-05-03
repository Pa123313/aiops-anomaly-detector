LLM-powered log anomaly detection for Kubernetes production environments

Grafana Loki + Ollama (LLaMA3) + Prometheus + Alertmanager + Helm
Features • Architecture • Quick Start • Screenshots • Configuration • Metrics
</div>

🚀 What This Project Does
This project is a production-grade AIOps system that:

📥 Fetches logs from Grafana Loki every 5 minutes using LogQL queries
🧠 Analyzes logs using a local LLM (Ollama/LLaMA3) — no API costs, no data leaving your cluster
📊 Returns structured JSON — anomaly detected, confidence score, severity, affected services, remediation steps
🚨 Fires alerts to Alertmanager automatically when anomalies are detected
📈 Exposes Prometheus metrics for full observability of the detector itself


Real Result: Detected a critical database failure with 0.8 confidence score and fired a severity=critical alert to Alertmanager within 17 seconds of log ingestion.


✨ Features
FeatureDetails🧠 Local LLMOllama (LLaMA3) — runs fully offline, zero API cost📋 Structured OutputLLM responds in strict JSON — anomaly, confidence, severity, affected services🎯 Smart FilteringConfigurable confidence threshold (default 0.7) to minimize false positives📊 Prometheus MetricsScans, anomalies, LLM latency histogram, confidence scores☸️ Kubernetes ReadyHelm chart with resource limits, probes, non-root security context🔒 Secure BuildMulti-stage Docker build, non-root user (UID 1001)🔁 CI/CD PipelineGitHub Actions: lint → Trivy scan → multi-arch build → GHCR push → Helm deploy🛡️ Security ScanningTrivy blocks CRITICAL/HIGH CVEs before deployment

🏗️ Architecture
┌─────────────────────────────────────────────────────────────────┐
│  Application Pods (production namespace)                         │
│  Sending logs → Grafana Loki                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │ LogQL query every 5 mins
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  AIOps Anomaly Detector (Python)                                 │
│                                                                  │
│  1. Fetch logs from Loki API          ──► Loki :3100            │
│  2. Send to local LLM for analysis    ──► Ollama :11434         │
│  3. Parse JSON response + confidence score                       │
│  4. Fire alert if anomaly detected    ──► Alertmanager :9093    │
│  5. Expose /metrics                   ──► Prometheus :9090      │
└─────────────────────────────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
     Alertmanager    Prometheus      Grafana
     (Slack/Email)   (Metrics)      (Dashboards)

📸 Live Demo Screenshots
✅ All Containers Running on AWS EC2
<img width="1363" height="367" alt="docker-ps" src="https://github.com/user-attachments/assets/eb17a023-a801-4d3e-912e-5078cdba156f" />


6 containers running healthy — Grafana, AIOps Detector, Prometheus, Ollama, Alertmanager, Loki

🚨 Alertmanager — Critical Alert Fired by LLM
<img width="1257" height="537" alt="alertmanager-alert" src="https://github.com/user-attachments/assets/f3fd5ed4-6c1d-4558-a2bc-df9397cf6b9d" />


AIOpsAnomalyDetected alert fired with severity=critical, source=aiops-detector

📊 Prometheus — Custom AIOps Metrics
<img width="1343" height="490" alt="prometheus-metrics" src="https://github.com/user-attachments/assets/84e73470-bb65-47cb-9217-d7517c9e8734" />


aiops_anomalies_detected_total = 1 — LLM detected database failure anomaly


⚡ Quick Start (Local)

bash# 1. Clone the repo
git clone https://github.com/Pa123313/aiops-anomaly-detector.git
cd aiops-anomaly-detector

# 2. Start the full stack
docker-compose up -d

# 3. Pull LLaMA3 model (first time only ~4GB)
docker exec -it ollama ollama pull llama3.2:1b

# 4. Send test logs to trigger anomaly detection
curl -X POST http://localhost:3100/loki/api/v1/push \
  -H "Content-Type: application/json" \
  -d '{
    "streams": [{
      "stream": {"namespace": "production", "app": "backend"},
      "values": [
        ["'$(date +%s)000000000'", "ERROR: Database connection failed - timeout after 30s"],
        ["'$(date +%s)000000001'", "CRITICAL: Memory usage at 95% - OOM killer may activate"]
      ]
    }]
  }'

# 5. Watch the LLM detect the anomaly!
docker logs -f aiops-detector

# 6. Open Grafana
open http://localhost:3000   # admin / admin

☸️ Deploy to Kubernetes (Helm)
bashhelm upgrade --install aiops-detector ./helm/aiops-detector \
  --namespace aiops \
  --create-namespace \
  --set image.tag=latest \
  --wait

🔧 Configuration
Environment VariableDefaultDescriptionLOKI_URLhttp://loki:3100Loki endpointOLLAMA_URLhttp://ollama:11434Ollama LLM endpointOLLAMA_MODELllama3.2:1bLLM model to useALERTMANAGER_URLhttp://alertmanager:9093Alertmanager endpointSCAN_INTERVAL300Seconds between scansLOG_LOOKBACK5Minutes of logs per scanLOKI_QUERY{namespace="production"}LogQL queryANOMALY_THRESHOLD0.7Minimum LLM confidence to fire alert

📈 Prometheus Metrics
MetricTypeDescriptionaiops_scans_totalCounterTotal scan cycles runaiops_anomalies_detected_totalCounterTotal anomalies detected by LLMaiops_alerts_fired_totalCounterTotal alerts sent to Alertmanageraiops_llm_latency_secondsHistogramLLM inference latencyaiops_last_anomaly_scoreGaugeConfidence score of last anomalyaiops_last_scan_timestampGaugeUnix timestamp of last scan

🔁 CI/CD Pipeline
Push to main
    │
    ├── 1. Lint & Test (flake8)
    ├── 2. Trivy Security Scan (blocks CRITICAL/HIGH CVEs)
    ├── 3. Build multi-arch image (amd64 + arm64)
    ├── 4. Push to GitHub Container Registry (GHCR)
    └── 5. Helm deploy to Kubernetes with rollout verification

🛠️ Tech Stack
CategoryTechnologiesLanguagePython 3.12LLM EngineOllama (LLaMA3 / LLaMA3.2)Log StorageGrafana LokiMetricsPrometheus + GrafanaAlertingAlertmanagerContainerDocker (multi-stage build)OrchestrationKubernetes + HelmCI/CDGitHub ActionsSecurityTrivy container scanningCloudAWS EC2

📁 Project Structure
aiops-anomaly-detector/
├── app/
│   ├── detector.py          # Main AIOps detection engine
│   └── requirements.txt     # Python dependencies
├── helm/
│   └── aiops-detector/      # Kubernetes Helm chart
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           └── deployment.yaml
├── alerts/
│   └── aiops_rules.yaml     # Prometheus alert rules
├── .github/
│   └── workflows/
│       └── ci-cd.yml        # GitHub Actions pipeline
├── Dockerfile               # Multi-stage secure build
├── docker-compose.yml       # Local development stack
├── prometheus.yml           # Prometheus scrape config
└── alertmanager.yml         # Alertmanager routing config

👩‍💻 Author
Pavithra A S — DevOps Engineer
