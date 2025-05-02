# ──────────── builder stage ────────────
FROM python:3.13-slim AS builder

ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /build

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      gcc libc6-dev libldap2-dev libsasl2-dev python3-dev curl ca-certificates tini \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Vendor into ./vendor (no console scripts!)
RUN pip install \
      --no-cache-dir \
      --no-index \
      --find-links=/wheels \
      -r requirements.txt \
      --target ./vendor \
 && rm -rf /wheels

# ──────────── runtime stage ────────────
FROM cgr.dev/chainguard/python:latest
WORKDIR /app

COPY --from=builder /usr/bin/tini /usr/bin/tini
COPY --from=builder /build/vendor /app/vendor
ENV PYTHONPATH=/app/vendor

USER nonroot
COPY . .

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
