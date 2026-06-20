FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY modules/requirements-shared.txt /app/requirements-shared.txt
COPY modules/cyber-psychology/requirements.txt /app/requirements-psych.txt

RUN pip install --upgrade pip && \
    pip install -r requirements-shared.txt && \
    pip install -r requirements-psych.txt

COPY modules/cyber-psychology/ /app/modules/cyber-psychology/
COPY modules/shared/ /app/modules/shared/
COPY modules/__init__.py /app/modules/__init__.py

ENV PYTHONPATH=/app

EXPOSE 8400

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8400/health')" || exit 1

CMD ["uvicorn", "modules.cyber-psychology.api:app", "--host", "0.0.0.0", "--port", "8400", "--workers", "2"]
