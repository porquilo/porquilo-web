# Stage 1: Build the Vite frontend
FROM node:24-slim AS frontend-builder

WORKDIR /app/web-app

COPY web-app/package*.json ./
RUN npm ci

COPY web-app/ ./
RUN npm run build

# Stage 2: Python server
FROM python:3.14-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY server/pyproject.toml server/uv.lock* ./
RUN uv sync --frozen --no-dev

COPY server/ ./
COPY --from=frontend-builder /app/web-app/dist ./static

EXPOSE 4184

CMD ["uv", "run", "uvicorn", "porquilo.main:app", "--host", "0.0.0.0", "--port", "4184"]
