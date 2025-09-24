#!/bin/bash

# Script de inicialização para Railway
echo "🚀 Iniciando Web Scraper Universal API..."

# Verificar se todas as dependências estão instaladas
echo "📦 Verificando dependências..."
python -c "import fastapi, uvicorn, requests, bs4, pandas, openpyxl" || {
    echo "❌ Erro: Dependências não encontradas"
    echo "💡 Instalando dependências..."
    pip install -r requirements.txt
}

# Definir variáveis de ambiente padrão se não existirem
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-8000}

echo "🌐 Servidor será executado em $HOST:$PORT"
echo "📡 Interface disponível em: http://$HOST:$PORT"
echo "📚 Documentação da API: http://$HOST:$PORT/docs"

# Executar a aplicação usando uvicorn diretamente
echo "🎯 Iniciando aplicação com uvicorn..."
exec uvicorn api:app --host $HOST --port $PORT --log-level info
