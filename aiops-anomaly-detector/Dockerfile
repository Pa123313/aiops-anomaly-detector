# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build
COPY app/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="aiops-anomaly-detector"
LABEL org.opencontainers.image.description="LLM-powered log anomaly detection for Kubernetes"
LABEL org.opencontainers.image.source="https://github.com/Pa123313/aiops-anomaly-detector"

# Non-root user for security
RUN useradd -m -u 1001 aiops
WORKDIR /app

COPY --from=builder /install /usr/local
COPY app/detector.py .

USER aiops

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/metrics', timeout=3)"

CMD ["python", "detector.py"]
