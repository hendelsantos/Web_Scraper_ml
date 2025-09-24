# Usar Python 3.11 slim como base
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema necessárias para web scraping
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro para cache das dependências
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código da aplicação
COPY . .

# Criar diretório para arquivos temporários
RUN mkdir -p /tmp/scraping

# Expor a porta que a aplicação usa
EXPOSE 8000

# Comando para rodar a aplicação
CMD ["python", "api.py"]
