#!/bin/bash

# Script para testar o scraper localmente

echo "🚀 Testando Web Scraper Universal"

# Ativar venv
source .venv/bin/activate

# Subir API em background
echo "📡 Subindo API..."
uvicorn api:app --host 0.0.0.0 --port 8000 --log-level info &
API_PID=$!

# Aguardar startup
sleep 3

# Testar healthz
echo "🔍 Testando /healthz..."
curl -s http://localhost:8000/healthz | python -m json.tool

# Testar sites
echo "🌐 Testando /sites..."
curl -s http://localhost:8000/sites | python -m json.tool

# Criar job
echo "🕸️ Criando job de scraping..."
JOB_ID=$(curl -s -X POST http://localhost:8000/scraping \
  -H "Content-Type: application/json" \
  -d '{"site":"mercado_livre","termo_busca":"notebook","max_paginas":1,"delay":1}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['job_id'])")

echo "Job ID: $JOB_ID"

# Aguardar conclusão
echo "⏳ Aguardando conclusão..."
for i in {1..30}; do
  STATUS=$(curl -s http://localhost:8000/job/$JOB_ID | python -c "import sys,json;print(json.load(sys.stdin)['status'])")
  PROGRESS=$(curl -s http://localhost:8000/job/$JOB_ID | python -c "import sys,json;print(json.load(sys.stdin)['progress'])")
  echo "Status: $STATUS - $PROGRESS"
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 2
done

# Resultado final
echo "📊 Resultado final:"
curl -s http://localhost:8000/job/$JOB_ID | python -m json.tool

# Matar API
kill $API_PID 2>/dev/null || true

echo "✅ Teste concluído"
