# ─── Stage 1: Builder (glibc-based) ─────────────────────────
FROM node:23-slim AS builder

ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Install build deps + tini (glibc-linked)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      curl tini \
 && rm -rf /var/lib/apt/lists/*

# Install and build your frontend
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --no-fund
COPY . .
RUN npm run build \
 && npm prune --production

# ─── Stage 2: Runtime (Chainguard Node) ──────────────────────
FROM cgr.dev/chainguard/node AS runtime

WORKDIR /app

# Copy the glibc-linked tini and the built app
COPY --from=builder /usr/bin/tini /usr/bin/tini
COPY --from=builder /app /app

# 2. Expose and launch under tini
EXPOSE 3000
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["npm", "start"]
