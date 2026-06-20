FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8031

ENV MODULE_ID=autonomous-agent \
    SENTINEL_CORE_URL=http://backend:3000/api/v1 \
    PYTHONPATH=/app:${PYTHONPATH}

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8031", "--log-level", "info"]
