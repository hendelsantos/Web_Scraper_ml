#!/bin/bash
# Script de inicialização para Railway/Docker

set -e

echo "🚀 Iniciando Web Scraper Universal API v2.0.0"

# Configurar porta (Railway injeta PORT automaticamente)
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

# Validar que PORT é um número
if ! echo "$PORT" | grep -q '^[0-9]\+$'; then
    echo "❌ PORT inválido: '$PORT', usando 8000"
    PORT=8000
fi

echo "📡 Configurações:"
echo "   - Host: $HOST"
echo "   - Porta: $PORT"
echo "   - Ambiente: ${RAILWAY_ENVIRONMENT:-local}"

# Aguardar um pouco para garantir que tudo está pronto
sleep 2

echo "🌐 Iniciando servidor..."

# Executar uvicorn com configurações otimizadas
exec uvicorn api:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers 1 \
    --loop uvloop \
    --http httptools \
    --log-level info \
    --access-log \
    --no-server-header
