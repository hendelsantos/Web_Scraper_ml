#!/bin/bash
# Script para testar a containerização localmente

set -e

echo "🐳 Testando containerização local..."

# Construir imagem
echo "🏗️ Construindo imagem Docker..."
docker build -t scraper-api:test .

# Executar container em background
echo "🚀 Executando container..."
CONTAINER_ID=$(docker run -d -p 8000:8000 --name scraper-test scraper-api:test)

# Aguardar inicialização
echo "⏳ Aguardando inicialização..."
sleep 10

# Testar healthcheck
echo "🔍 Testando healthcheck..."
if curl -f -s http://localhost:8000/healthz > /dev/null; then
    echo "✅ Healthcheck OK"
else
    echo "❌ Healthcheck falhou"
    docker logs $CONTAINER_ID
    docker stop $CONTAINER_ID
    docker rm $CONTAINER_ID
    exit 1
fi

# Testar endpoints básicos
echo "📡 Testando endpoints..."

# /sites
if curl -f -s http://localhost:8000/sites > /dev/null; then
    echo "✅ Endpoint /sites OK"
else
    echo "❌ Endpoint /sites falhou"
fi

# /metrics
if curl -f -s http://localhost:8000/metrics > /dev/null; then
    echo "✅ Endpoint /metrics OK"
else
    echo "❌ Endpoint /metrics falhou"
fi

# Limpar
echo "🧹 Limpando container de teste..."
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID

echo "🎉 Teste de containerização concluído com sucesso!"
