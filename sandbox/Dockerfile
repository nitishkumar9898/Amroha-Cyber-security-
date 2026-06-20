FROM ubuntu:22.04

# A highly restricted Ubuntu container for simulated malware detonation
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    tcpdump \
    strace \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /sandbox
COPY sandbox_runner.py .

CMD ["python3", "sandbox_runner.py"]
