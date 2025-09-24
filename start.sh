#!/bin/bash
# Script de inicialização para Railway/Docker

set -e

echo "🚀 Iniciando Web Scraper Universal API v2.0.0"

# Configurar porta (Railway injeta PORT)
PORT={PORT:-8000}
HOST={HOST:-0.0.0.0}

echo "📡 Configurações:"
echo "   - Host: HOST"
echo "   - Porta: PORT"
echo "   - Ambiente: {RAILWAY_ENVIRONMENT:-local}"

# Aguardar um pouco para garantir que tudo está pronto
sleep 2

# Executar uvicorn com configurações otimizadas
exec uvicorn api:app 
    --host "HOST" 
    --port "PORT" 
    --workers 1 
    --loop uvloop 
    --http httptools 
    --log-level info 
    --access-log 
    --no-server-header
