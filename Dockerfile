## Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

## System deps (apenas o essencial)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create temp directory
RUN mkdir -p /tmp/scraping

## Definir porta padrão (Railway injeta PORT em runtime)
ENV PORT=8000

EXPOSE 8000

## Healthcheck simples (opcional para ambientes que suportam)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:${PORT}/healthz || exit 1

## Executar aplicação
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT} --log-level info"]
