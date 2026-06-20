FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements*.txt /build/
RUN pip install --no-cache-dir --user -r requirements.txt 2>/dev/null || true

FROM python:3.12-slim

WORKDIR /app

RUN groupadd -r ctf && useradd -r -g ctf -d /app -s /sbin/nologin ctf

COPY --from=builder /root/.local /root/.local

COPY modules/blockchain-ledge/ /app/modules/blockchain-ledge/
COPY modules/shared/ /app/modules/shared/
COPY modules/__init__.py /app/modules/__init__.py

RUN mkdir -p /app/modules/blockchain-ledge/data && chown -R ctf:ctf /app

ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8106

USER ctf

CMD ["uvicorn", "modules.blockchain-ledge.api:app", "--host", "0.0.0.0", "--port", "8106", "--log-level", "info"]
