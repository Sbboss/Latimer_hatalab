# syntax=docker/dockerfile:1.7

############################################
# Frontend build stage
############################################
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

############################################
# Runtime stage (FastAPI + static frontend)
############################################
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

WORKDIR /app

# Minimal runtime deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY .env.example ./.env.example

# Static frontend assets
COPY --from=frontend-builder /app/frontend/dist ./frontend_dist

# Entrypoint script
COPY deploy/start.sh ./deploy/start.sh
RUN chmod +x ./deploy/start.sh

EXPOSE 7860
CMD ["./deploy/start.sh"]
