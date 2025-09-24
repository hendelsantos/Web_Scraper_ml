# 🚀 Web Scraper Universal API

## 📝 Visão Geral

Esta API permite fazer scraping de produtos em diferentes sites de e-commerce de forma assíncrona via requisições HTTP.

## 🌐 Endpoints Disponíveis

### 1. **GET /** - Informações da API
```
GET http://localhost:8000/
```

### 2. **GET /sites** - Sites Disponíveis
Lista todos os sites suportados para scraping.
```
GET http://localhost:8000/sites
```

**Resposta:**
```json
{
  "sites_disponiveis": {
    "mercado_livre": "Mercado Livre",
    "amazon": "Amazon"
  }
}
```

### 3. **POST /scraping** - Iniciar Scraping
Inicia um job de scraping assíncrono.
```
POST http://localhost:8000/scraping
Content-Type: application/json

{
  "site": "mercado_livre",
  "termo_busca": "iphone 15",
  "max_paginas": 5,
  "delay": 1.0
}
```

**Resposta:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "message": "Job de scraping iniciado. Use o job_id para consultar o status."
}
```

### 4. **GET /job/{job_id}** - Consultar Status
Consulta o status e resultados de um job.
```
GET http://localhost:8000/job/123e4567-e89b-12d3-a456-426614174000
```

**Resposta:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "progress": "Concluído! 150 produtos encontrados.",
  "total_produtos": 150,
  "produtos": [
    {
      "nome": "iPhone 15 Pro Max 256GB",
      "preco": "7999",
      "link": "https://www.mercadolivre.com.br/...",
      "site": "Mercado Livre"
    }
  ],
  "erro": null,
  "created_at": "2025-01-15T10:30:00",
  "completed_at": "2025-01-15T10:32:00"
}
```

### 5. **GET /jobs** - Listar Jobs
Lista todos os jobs criados.
```
GET http://localhost:8000/jobs
```

### 6. **DELETE /job/{job_id}** - Deletar Job
Remove um job específico.
```
DELETE http://localhost:8000/job/123e4567-e89b-12d3-a456-426614174000
```

## 🚀 Como Executar

### 1. Instalar Dependências
```bash
pip install fastapi uvicorn pydantic requests beautifulsoup4
```

### 2. Executar API
```bash
python api.py
```
ou
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Acessar Documentação
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 💻 Exemplos de Uso

### Python
```python
import requests
import time

# 1. Verificar sites disponíveis
response = requests.get("http://localhost:8000/sites")
print(response.json())

# 2. Iniciar scraping
data = {
    "site": "mercado_livre",
    "termo_busca": "notebook gamer",
    "max_paginas": 3,
    "delay": 1.0
}
response = requests.post("http://localhost:8000/scraping", json=data)
job_id = response.json()["job_id"]
print(f"Job ID: {job_id}")

# 3. Aguardar conclusão
while True:
    response = requests.get(f"http://localhost:8000/job/{job_id}")
    job_data = response.json()
    
    print(f"Status: {job_data['status']}")
    print(f"Progresso: {job_data['progress']}")
    
    if job_data['status'] in ['completed', 'failed']:
        break
    
    time.sleep(5)

# 4. Ver resultados
if job_data['status'] == 'completed':
    print(f"Total de produtos: {job_data['total_produtos']}")
    for produto in job_data['produtos'][:5]:  # Primeiros 5
        print(f"- {produto['nome']} - R$ {produto['preco']}")
```

### JavaScript/Fetch
```javascript
// 1. Iniciar scraping
const startScraping = async () => {
  const response = await fetch('http://localhost:8000/scraping', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      site: 'mercado_livre',
      termo_busca: 'smartphone',
      max_paginas: 3,
      delay: 1.0
    })
  });
  
  const data = await response.json();
  return data.job_id;
};

// 2. Consultar status
const checkStatus = async (jobId) => {
  const response = await fetch(`http://localhost:8000/job/${jobId}`);
  const data = await response.json();
  return data;
};

// Uso
startScraping().then(jobId => {
  console.log('Job iniciado:', jobId);
  
  const checkInterval = setInterval(async () => {
    const status = await checkStatus(jobId);
    console.log('Status:', status.status);
    
    if (status.status === 'completed') {
      console.log('Produtos encontrados:', status.total_produtos);
      clearInterval(checkInterval);
    }
  }, 5000);
});
```

### cURL
```bash
# 1. Sites disponíveis
curl -X GET "http://localhost:8000/sites"

# 2. Iniciar scraping
curl -X POST "http://localhost:8000/scraping" \
     -H "Content-Type: application/json" \
     -d '{
       "site": "mercado_livre",
       "termo_busca": "fone bluetooth",
       "max_paginas": 2,
       "delay": 1.0
     }'

# 3. Consultar job (substitua pelo job_id retornado)
curl -X GET "http://localhost:8000/job/SEU_JOB_ID_AQUI"
```

## 📊 Status dos Jobs

- **pending**: Job criado, aguardando processamento
- **running**: Job em execução
- **completed**: Job concluído com sucesso
- **failed**: Job falhou com erro

## 🔧 Parâmetros de Configuração

| Parâmetro | Tipo | Obrigatório | Padrão | Descrição |
|-----------|------|-------------|---------|-----------|
| site | string | ✅ | - | ID do site ("mercado_livre" ou "amazon") |
| termo_busca | string | ✅ | - | Produto a ser buscado |
| max_paginas | integer | ❌ | 10 | Máximo de páginas a processar |
| delay | float | ❌ | 1.0 | Delay entre requisições (segundos) |

## 🌐 Deploy em Produção

### Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY api.py .
EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Heroku
```bash
# Criar Procfile
echo "web: uvicorn api:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku create seu-app-name
git push heroku main
```

## ⚠️ Limitações e Considerações

1. **Rate Limiting**: Respeite os limites dos sites
2. **Armazenamento**: Jobs são mantidos em memória (use Redis em produção)
3. **Timeout**: Requisições têm timeout de 10 segundos
4. **Escalabilidade**: Use Celery + Redis para maior escala
5. **Legal**: Verifique os termos de uso dos sites
