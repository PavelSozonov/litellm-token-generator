# tests/Dockerfile
FROM python:3.10-slim

# --- OS build dependencies once-for-all --------------------------
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      gcc libc6-dev libldap2-dev libsasl2-dev python3-dev \
 && rm -rf /var/lib/apt/lists/*

# --- Python deps --------------------------------------------------
WORKDIR /deps
COPY token-generator/requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt pytest httpx
