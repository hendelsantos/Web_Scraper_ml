# ================================
# Web Scraper Universal - Dockerfile
# ================================
FROM python:3.11-slim

# Definir metadados
LABEL maintainer="Web Scraper API"
LABEL version="2.0.0"
LABEL description="API FastAPI para scraping de produtos em e-commerce"

# Evitar prompts interativos durante instalação
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Criar usuário não-root para segurança
RUN groupadd -r scraper && useradd -r -g scraper scraper

# Instalar dependências do sistema (apenas essenciais)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar e instalar dependências Python primeiro (para cache de layers)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Dar permissão de execução ao script de inicialização
RUN chmod +x start.sh

# Criar diretórios necessários
RUN mkdir -p /tmp/scraping && \
    mkdir -p /app/static && \
    chown -R scraper:scraper /app && \
    chown -R scraper:scraper /tmp/scraping

# Definir usuário não-root
USER scraper

# Configurar porta (Railway sobrescreve via env PORT)
ENV PORT=8000
EXPOSE ${PORT}

# Comando de inicialização otimizado
CMD ["./start.sh"]
