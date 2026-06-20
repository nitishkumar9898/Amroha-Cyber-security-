FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY modules/requirements-shared.txt /app/requirements-shared.txt
COPY modules/requirements-ml.txt /app/requirements-ml.txt

RUN pip install --upgrade pip && \
    pip install -r requirements-shared.txt && \
    pip install -r requirements-ml.txt && \
    pip install androguard==4.1.1 networkx==3.3.0 pyvis==0.3.2

COPY modules/mobile-iot-forensics/ /app/modules/mobile-iot-forensics/
COPY modules/shared/ /app/modules/shared/
COPY modules/__init__.py /app/modules/__init__.py

ENV PYTHONPATH=/app

EXPOSE 8300

CMD ["uvicorn", "modules.mobile-iot-forensics.api:app", "--host", "0.0.0.0", "--port", "8300", "--workers", "4"]
