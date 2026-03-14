FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.12-slim

LABEL org.opencontainers.image.title="Boiler HMI Bridge" \
      org.opencontainers.image.description="WebSocket to OPC UA bridge for the boiler HMI" \
      org.opencontainers.image.licenses="MIT"

RUN groupadd --gid 1001 hmi \
 && useradd  --uid 1001 --gid hmi --no-create-home hmi

WORKDIR /app

COPY --from=builder /install /usr/local

# Bridge script and static HMI file
COPY hmi_bridge.py .
COPY hmi.html      .

# WebSocket port for browser connections
EXPOSE 8765

# Static file server port (serves hmi.html)
EXPOSE 8080

USER hmi

# Start both the bridge and a static file server for hmi.html
CMD ["sh", "-c", "python -u hmi_bridge.py & python -m http.server 8080"]
