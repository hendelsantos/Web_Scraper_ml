#!/bin/bash

# Script de inicialização para Railway
echo "🚀 Iniciando Web Scraper Universal API..."

# Verificar se todas as dependências estão instaladas
echo "📦 Verificando dependências..."
python -c "import fastapi, uvicorn, requests, bs4, pandas, openpyxl" || {
    echo "❌ Erro: Dependências não encontradas"
    exit 1
}

# Definir variáveis de ambiente padrão
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-8000}

echo "🌐 Servidor será executado em $HOST:$PORT"
echo "📡 Interface disponível em: http://$HOST:$PORT"
echo "📚 Documentação da API: http://$HOST:$PORT/docs"

# Executar a aplicação
echo "🎯 Iniciando aplicação..."
python api.py
