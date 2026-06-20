FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements*.txt /app/
RUN pip install --no-cache-dir -r requirements-shared.txt 2>/dev/null || true
RUN pip install --no-cache-dir -r requirements-ml.txt 2>/dev/null || true

COPY modules/evidence-correlation/ /app/modules/evidence-correlation/
COPY modules/shared/ /app/modules/shared/
COPY modules/__init__.py /app/modules/__init__.py

ENV PYTHONPATH=/app
ENV SENTINEL_CORE_URL=http://backend:3000/api/v1
ENV NEO4J_URI=bolt://neo4j:7687
ENV NEO4J_USER=neo4j
ENV NEO4J_PASSWORD=changeme

EXPOSE 8006

CMD ["uvicorn", "modules.evidence-correlation.api:app", "--host", "0.0.0.0", "--port", "8006", "--log-level", "info"]
