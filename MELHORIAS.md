# 🎯 Web Scraper Universal - Melhorias Implementadas

## ✨ Principais Melhorias

### 🔧 **1. Interface Interativa**
- ✅ Menu de seleção de sites
- ✅ Input dinâmico do termo de busca
- ✅ Confirmação das configurações
- ✅ Feedback visual com emojis

### 🌐 **2. Suporte Multi-Sites**
- ✅ Mercado Livre (funcionando)
- ✅ Amazon (estrutura preparada)
- ✅ Fácil adição de novos sites

### 🛠️ **3. Configuração Dinâmica**
- ✅ Seletores CSS configuráveis por site
- ✅ URLs de paginação customizáveis
- ✅ Tratamento de links relativos/absolutos

### 📁 **4. Melhor Organização de Arquivos**
- ✅ Nome do arquivo baseado no termo de busca
- ✅ Coluna adicional identificando o site
- ✅ Dados ordenados por site e nome

### 🛡️ **5. Tratamento de Erros**
- ✅ Try/catch para capturar erros
- ✅ Limite de páginas para evitar loops infinitos
- ✅ Interrupção por Ctrl+C
- ✅ Mensagens informativas

### 📊 **6. Feedback Melhorado**
- ✅ Amostra dos primeiros 5 produtos
- ✅ Estatísticas finais
- ✅ Progress feedback em tempo real
- ✅ Resumo da configuração

## 🚀 Como Usar

1. **Execute o script:**
   ```bash
   python Sraper_ml.py
   ```

2. **Escolha o site:**
   - Digite `1` para Mercado Livre
   - Digite `2` para Amazon (em desenvolvimento)

3. **Digite o produto:**
   - Exemplo: "iphone", "notebook", "fone bluetooth"

4. **Confirme as configurações:**
   - Digite `s` para confirmar ou `n` para reconfigurar

5. **Aguarde o scraping:**
   - O processo é automático
   - Use Ctrl+C para interromper se necessário

## 📝 Exemplo de Uso

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
[INFO] Coletando página 2...
...

🎉 1.250 produtos exportados!
📁 Arquivo: produtos_iphone_15.xlsx
```

## 🔧 Estrutura de Sites Suportados

```python
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
```

## 📋 Próximas Melhorias Sugeridas

- [ ] Implementar seletores para avaliações e reviews
- [ ] Adicionar mais sites (Submarino, Casas Bahia, etc.)
- [ ] Filtros de preço mínimo/máximo
- [ ] Exportação em outros formatos (CSV, JSON)
- [ ] Interface gráfica (GUI)
- [ ] Configuração via arquivo JSON
- [ ] Threading para scraping mais rápido
- [ ] Cache de resultados
