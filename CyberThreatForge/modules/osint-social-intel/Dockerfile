FROM python:3.11-slim

LABEL maintainer="CyberThreatForge"
LABEL module="osint-social-intel"
LABEL description="OSINT & Social Media Intelligence module with PyTorch models"

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
    dnsutils \
    netbase \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "import torch; print(f'PyTorch {torch.__version__} ready')" && \
    python -c "import networkx; print(f'NetworkX {networkx.__version__} ready')"

COPY . .

RUN python -c "from models.entity_resolver import EntityResolver; \
    from models.sentiment_tracker import SentimentTracker; \
    print('Models loaded successfully')" && \
    python -c "from collectors.social_collector import SocialMediaCollector; \
    from collectors.domain_collector import DomainIntelligenceCollector; \
    from collectors.ip_collector import IPIntelligenceCollector; \
    print('Collectors loaded successfully')"

EXPOSE 8012

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8012", "--workers", "2"]
