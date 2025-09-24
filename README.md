# Web_Scraper_ml

🎯 **Web Scraper Universal** - Uma ferramenta poderosa e interativa para fazer scraping de produtos em diferentes sites de e-commerce.

**🚀 NOVO: Agora disponível como API REST!**

## ✨ Características Principais

### 🌐 **Multi-Sites**
- ✅ **Mercado Livre** (totalmente funcional)
- 🔧 **Amazon** (estrutura preparada)
- 🚀 **Fácil adição** de novos sites

### 🎮 **Interface Interativa**
- 📋 Menu de seleção de sites
- 🔍 Input dinâmico do termo de busca
- ✅ Confirmação de configurações
- 📊 Feedback visual em tempo real

### 📡 **API REST** (NOVO!)
- ⚡ Jobs assíncronos em background
- 🌐 Endpoints RESTful completos
- 📊 Monitoramento em tempo real
- 🔧 Documentação automática (Swagger/ReDoc)

### 🛠️ **Funcionalidades Avançadas**
- 🎯 Configuração dinâmica de seletores CSS
- 📁 Nomenclatura automática de arquivos
- 🛡️ Tratamento robusto de erros
- ⏸️ Suporte a interrupção (Ctrl+C)
- 📈 Amostra dos resultados coletados

## 🚀 Como Usar

### 1. **Instalação das Dependências**
```bash
pip install requests beautifulsoup4 pandas openpyxl
```

### 2. **Execução**
```bash
python Sraper_ml.py
```

### 3. **Uso Interativo**
```
🎯 WEB SCRAPER UNIVERSAL
==================================================

🌐 SITES DISPONÍVEIS:
1. Mercado Livre
2. Amazon

📍 Digite o número do site: 1
🔍 Digite o produto: iphone 15
❓ Confirmar configurações? (s/n): s

🕸️ INICIANDO SCRAPING...
[INFO] Coletando página 1...
...
🎉 1.250 produtos exportados!
📁 Arquivo: produtos_iphone_15.xlsx
```

## 📡 API REST (NOVIDADE!)

### 🚀 **Executar API**
```bash
# Instalar dependências da API
pip install fastapi uvicorn pydantic

# Iniciar servidor
python api.py

# Acessar documentação
# http://localhost:8000/docs
```

### 📋 **Endpoints Disponíveis**
- `GET /` - Informações da API
- `GET /sites` - Sites disponíveis
- `POST /scraping` - Iniciar job de scraping
- `GET /job/{id}` - Consultar status do job
- `GET /jobs` - Listar todos os jobs
- `DELETE /job/{id}` - Deletar job

### 💻 **Exemplo de Uso da API**
```python
import requests

# 1. Iniciar scraping
response = requests.post('http://localhost:8000/scraping', json={
    'site': 'mercado_livre',
    'termo_busca': 'notebook gamer',
    'max_paginas': 3,
    'delay': 1.0
})
job_id = response.json()['job_id']

# 2. Consultar resultado
result = requests.get(f'http://localhost:8000/job/{job_id}')
job_data = result.json()

print(f"Status: {job_data['status']}")
print(f"Produtos: {job_data['total_produtos']}")
```

### 🌐 **Via cURL**
```bash
# Iniciar scraping
curl -X POST http://localhost:8000/scraping \
  -H "Content-Type: application/json" \
  -d '{
    "site": "mercado_livre",
    "termo_busca": "smartphone",
    "max_paginas": 2
  }'

# Consultar resultado
curl http://localhost:8000/job/SEU_JOB_ID
```

### ⚡ **Vantagens da API**
- 🔄 **Processamento assíncrono** em background
- 🌐 **Acesso via HTTP** de qualquer aplicação
- 📱 **Integrável** com web, mobile, desktop
- 📊 **Monitoramento** de progresso em tempo real
- 🚀 **Jobs simultâneos** para diferentes buscas

### 🔧 **Cliente Python Interativo**
```bash
python client.py
```
O cliente oferece interface para usar a API de forma interativa.

## 📊 Dados Coletados

Para cada produto encontrado, o scraper coleta:
- 📝 **Nome** do produto
- 💰 **Preço**
- 🔗 **Link** do produto
- 🌐 **Site** de origem
- ⭐ **Avaliações** (em desenvolvimento)
- 📝 **Reviews** (em desenvolvimento)

## 📁 Arquivos Gerados

- **Formato**: Excel (.xlsx)
- **Nomenclatura**: `produtos_{termo_busca}.xlsx`
- **Organização**: Dados ordenados por site e nome
- **Colunas**: nome, preco, link, avaliacao, reviews, site

## 🔧 Arquitetura Técnica

### Sites Suportados
```python
SITES_SUPORTADOS = {
    "1": {
        "nome": "Mercado Livre",
        "base_url": "https://lista.mercadolivre.com.br",
        "seletores": {
            "item": "li.ui-search-layout__item",
            "nome": ".poly-component__title",
            "preco": ".andes-money-amount__fraction",
            # ...
        },
        "paginacao": "_Desde_{}"
    }
}
```

### Configuração Dinâmica
- ✅ Seletores CSS configuráveis por site
- ✅ URLs de paginação customizáveis
- ✅ Tratamento de links relativos/absolutos

## 📋 Próximas Funcionalidades

- [ ] 🌟 Implementar coleta de avaliações e reviews
- [ ] 🏪 Adicionar mais sites (Submarino, Casas Bahia, etc.)
- [ ] 💸 Filtros de preço mínimo/máximo
- [ ] 📄 Exportação em outros formatos (CSV, JSON)
- [ ] 🖥️ Interface gráfica (GUI)
- [ ] ⚙️ Configuração via arquivo JSON
- [ ] ⚡ Threading para scraping mais rápido
- [ ] 💾 Cache de resultados

## 🛡️ Tratamento de Erros

- ✅ Try/catch para capturar erros inesperados
- ✅ Limite de páginas para evitar loops infinitos
- ✅ Validação de inputs do usuário
- ✅ Recuperação graceful de falhas de rede
- ✅ Mensagens informativas de erro

## 📈 Estatísticas de Exemplo

```
🎉 [SUCESSO] 2.091 produtos exportados!
📁 Arquivo salvo: produtos_cellular.xlsx
🌐 Site: Mercado Livre
🔍 Busca: cellular

📊 AMOSTRA DOS PRIMEIROS 5 PRODUTOS:
1. Smartphone Samsung Galaxy A54 5G 128GB
   💰 Preço: R$ 1.399
   🌐 Site: Mercado Livre
```

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Hendel Santos** - [GitHub](https://github.com/hendelsantos)

---

⭐ **Deixe uma estrela se este projeto foi útil para você!**
