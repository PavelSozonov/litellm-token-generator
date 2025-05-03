# ─── Stage 1: Builder (node:23-alpine) ───────────────────────
FROM node:23-alpine AS builder
WORKDIR /app

# 1. Download a statically linked tini
RUN apk add --no-cache curl \
 && curl -SL https://github.com/krallin/tini/releases/download/v0.19.0/tini-static \
     -o /tini \
 && chmod +x /tini

# 2. Install all dependencies for build
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --no-fund

# 3. Build and prune dev dependencies
COPY . .
RUN npm run build \
 && npm prune --production

# ─── Stage 2: Runtime (Chainguard Node) ──────────────────────
FROM cgr.dev/chainguard/node AS runtime
WORKDIR /app

# 1. Copy the static tini and the built app
COPY --from=builder /tini /tini
COPY --from=builder /app /app

# 2. Expose and launch under tini
EXPOSE 3000
ENTRYPOINT ["/tini", "--"]
CMD ["npm", "start"]
