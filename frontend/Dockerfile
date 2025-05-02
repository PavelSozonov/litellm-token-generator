# ─────────────── Builder ───────────────
FROM node:18-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ─────────────── Runner ───────────────
FROM node:18-alpine AS runner
WORKDIR /app

RUN apk add --no-cache curl

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/package.json ./package.json

RUN npm install --omit=dev

EXPOSE 3000
CMD ["npm", "start"]
