FROM python:3.11-slim

LABEL maintainer="CyberThreatForge"
LABEL module="federated-learning"
LABEL description="Federated Learning Across Agencies — secure multi-agency threat model training"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    TORCH_HOME=/models/torch \
    MODEL_CACHE=/models/cache

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

RUN python -c "import torch; print(f'PyTorch {torch.__version__} ready')"

COPY __init__.py .
COPY api.py .
COPY federated/ ./federated/
COPY models/ ./models/
COPY checkpoints/ ./checkpoints/

RUN python -c "from models.malware_cnn import MalwareCNN; m = MalwareCNN(); print(f'Model ready: {m.get_parameter_count()} params')" && \
    python -c "from models.dp_engine import DifferentialPrivacyEngine; dp = DifferentialPrivacyEngine(); print('DP engine ready')" && \
    python -c "from federated.secure_aggregation import SecureAggregator; sa = SecureAggregator(); print('Secure aggregator ready')" && \
    python -c "from federated.server import FederatedServer; fs = FederatedServer(); print('FL server ready')" && \
    python -c "from federated.client import FederatedClient; print('FL client ready')"

RUN mkdir -p /app/checkpoints && chmod -R 777 /app/checkpoints

EXPOSE 8014

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8014/health').read().decode())" || exit 1

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8014", "--workers", "2"]
