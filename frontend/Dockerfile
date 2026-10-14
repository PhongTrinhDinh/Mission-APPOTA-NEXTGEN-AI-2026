# ==============================================================================
# Frontend Dockerfile - Appota NextGen Enterprise Secure RAG (Next.js 16)
# ==============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Cài đặt dependencies
COPY package*.json ./
RUN npm ci

# Sao chép toàn bộ mã nguồn frontend và build
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 2: Production Runner
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    NEXT_TELEMETRY_DISABLED=1

# Copy các artifacts từ builder
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["npm", "start"]
