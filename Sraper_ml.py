import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import urllib.parse

# ==========================
# CONFIGURAÇÕES
# ==========================
DELAY = 1  # Segundos de espera entre requisições para evitar bloqueio

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
}

# Dicionário de sites suportados
SITES_SUPORTADOS = {
    "1": {
        "nome": "Mercado Livre",
        "base_url": "https://lista.mercadolivre.com.br",
        "seletores": {
            "item": "li.ui-search-layout__item",
            "nome": ".poly-component__title",
            "preco": ".andes-money-amount__fraction",
            "link": ".poly-component__title",
            "avaliacao": "[class*='rating']",
            "reviews": "[class*='review']"
        },
        "paginacao": "_Desde_{}"
    },
    "2": {
        "nome": "Amazon",
        "base_url": "https://www.amazon.com.br/s?k=",
        "seletores": {
            "item": "[data-component-type='s-search-result']",
            "nome": "h2 a span",
            "preco": ".a-price-whole",
            "link": "h2 a",
            "avaliacao": ".a-icon-alt",
            "reviews": ".a-size-base"
        },
        "paginacao": "&page={}"
    }
}

# ==========================
# FUNÇÕES INTERATIVAS
# ==========================
def mostrar_sites_disponivel():
    """Mostra os sites disponíveis para scraping"""
    print("\n🌐 SITES DISPONÍVEIS PARA SCRAPING:")
    print("="*50)
    for key, site in SITES_SUPORTADOS.items():
        print(f"{key}. {site['nome']}")
    print("="*50)

def escolher_site():
    """Permite ao usuário escolher o site para fazer scraping"""
    mostrar_sites_disponivel()
    
    while True:
        escolha = input("\n📍 Digite o número do site desejado: ").strip()
        if escolha in SITES_SUPORTADOS:
            return SITES_SUPORTADOS[escolha]
        else:
            print("❌ Opção inválida! Tente novamente.")

def obter_termo_busca():
    """Obtém o termo de busca do usuário"""
    print("\n🔍 TERMO DE BUSCA:")
    print("="*30)
    termo = input("Digite o produto que deseja buscar: ").strip()
    
    if not termo:
        print("❌ Termo de busca não pode estar vazio!")
        return obter_termo_busca()
    
    return termo

def construir_url_busca(site, termo):
    """Constrói a URL de busca baseada no site e termo"""
    if site['nome'] == "Mercado Livre":
        # Codifica o termo para URL
        termo_codificado = urllib.parse.quote_plus(termo)
        return f"{site['base_url']}/{termo_codificado}"
    elif site['nome'] == "Amazon":
        termo_codificado = urllib.parse.quote_plus(termo)
        return f"{site['base_url']}{termo_codificado}"
    
    return None

def obter_configuracoes_busca():
    """Obtém todas as configurações de busca do usuário"""
    print("\n🚀 CONFIGURADOR DE SCRAPING")
    print("="*50)
    
    # Escolher site
    site_escolhido = escolher_site()
    print(f"✅ Site selecionado: {site_escolhido['nome']}")
    
    # Obter termo de busca
    termo_busca = obter_termo_busca()
    print(f"✅ Termo de busca: {termo_busca}")
    
    # Construir URL
    url_busca = construir_url_busca(site_escolhido, termo_busca)
    print(f"✅ URL gerada: {url_busca}")
    
    # Confirmar configurações
    print(f"\n📋 RESUMO DA CONFIGURAÇÃO:")
    print(f"   🌐 Site: {site_escolhido['nome']}")
    print(f"   🔍 Busca: {termo_busca}")
    print(f"   🔗 URL: {url_busca}")
    
    confirmar = input("\n❓ Deseja continuar com essas configurações? (s/n): ").lower().strip()
    
    if confirmar == 's' or confirmar == 'sim':
        return site_escolhido, termo_busca, url_busca
    else:
        print("🔄 Reconfigurando...")
        return obter_configuracoes_busca()

# ==========================
# FUNÇÃO PARA BUSCAR PRODUTOS
# ==========================
def coletar_produtos(site_config, url_base, termo_busca):
    """Coleta produtos baseado nas configurações do site"""
    produtos = []
    pagina = 1
    
    print(f"\n🕸️ INICIANDO SCRAPING...")
    print(f"📱 Site: {site_config['nome']}")
    print(f"🔍 Busca: {termo_busca}")
    print("="*50)

    while True:
        # Construir URL da página
        if site_config['nome'] == "Mercado Livre":
            if pagina > 1:
                url = f"{url_base}_Desde_{(pagina-1)*50+1}"
            else:
                url = url_base
        elif site_config['nome'] == "Amazon":
            if pagina > 1:
                url = f"{url_base}&page={pagina}"
            else:
                url = url_base
        
        print(f"[INFO] Coletando página {pagina} -> {url}")

        try:
            resp = requests.get(url, headers=HEADERS)
            if resp.status_code != 200:
                print(f"[ERRO] Não foi possível acessar a página (status {resp.status_code}).")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            itens = soup.select(site_config['seletores']['item'])
            
            if not itens:
                print("[INFO] Não há mais produtos.")
                break

            for item in itens:
                # Extrair dados usando os seletores do site
                nome_elem = item.select_one(site_config['seletores']['nome'])
                preco_elem = item.select_one(site_config['seletores']['preco'])
                link_elem = item.select_one(site_config['seletores']['link'])
                avaliacao_elem = item.select_one(site_config['seletores']['avaliacao'])
                reviews_elem = item.select_one(site_config['seletores']['reviews'])

                # Processar dados
                nome = nome_elem.get_text(strip=True) if nome_elem else None
                preco = preco_elem.get_text(strip=True) if preco_elem else None
                
                # Processar link
                link = None
                if link_elem:
                    if link_elem.get('href'):
                        link = link_elem['href']
                        # Se for link relativo, adicionar domínio
                        if link and link.startswith('/'):
                            if site_config['nome'] == "Mercado Livre":
                                link = f"https://www.mercadolivre.com.br{link}"
                            elif site_config['nome'] == "Amazon":
                                link = f"https://www.amazon.com.br{link}"

                produtos.append({
                    "nome": nome,
                    "preco": preco,
                    "link": link,
                    "avaliacao": None,  # Para implementar futuramente
                    "reviews": None,    # Para implementar futuramente
                    "site": site_config['nome']
                })

            pagina += 1
            time.sleep(DELAY)
            
            # Limite de segurança (opcional)
            if pagina > 50:  # Máximo 50 páginas
                print("[INFO] Limite de páginas atingido.")
                break
                
        except Exception as e:
            print(f"[ERRO] Erro ao processar página {pagina}: {str(e)}")
            break

    return produtos

# ==========================
# PROGRAMA PRINCIPAL
# ==========================
if __name__ == "__main__":
    print("🎯 WEB SCRAPER UNIVERSAL")
    print("="*50)
    print("Bem-vindo ao Web Scraper Universal!")
    print("Este programa permite fazer scraping de diferentes sites de e-commerce.")
    
    try:
        # Obter configurações do usuário
        site_config, termo_busca, url_busca = obter_configuracoes_busca()
        
        # Executar scraping
        produtos = coletar_produtos(site_config, url_busca, termo_busca)

        if not produtos:
            print("\n❌ [ERRO] Nenhum produto encontrado.")
            print("💡 Dicas:")
            print("   - Verifique se o termo de busca está correto")
            print("   - Tente termos mais específicos")
            print("   - Alguns sites podem ter mudado sua estrutura")
        else:
            # Criar DataFrame
            df = pd.DataFrame(produtos)

            # Ordena por site e depois por nome
            df.sort_values(by=["site", "nome"], ascending=[True, True], inplace=True)

            # Gerar nome do arquivo baseado na busca
            nome_arquivo_limpo = "".join(c for c in termo_busca if c.isalnum() or c in (' ', '-', '_')).rstrip()
            nome_arquivo = f"produtos_{nome_arquivo_limpo.replace(' ', '_')}.xlsx"
            
            # Salvar para Excel
            df.to_excel(nome_arquivo, index=False)
            
            print(f"\n🎉 [SUCESSO] {len(produtos)} produtos exportados!")
            print(f"📁 Arquivo salvo: {nome_arquivo}")
            print(f"🌐 Site: {site_config['nome']}")
            print(f"🔍 Busca: {termo_busca}")
            
            # Mostrar amostra dos dados
            print(f"\n📊 AMOSTRA DOS PRIMEIROS 5 PRODUTOS:")
            print("="*80)
            for i, produto in enumerate(produtos[:5], 1):
                print(f"{i}. {produto['nome']}")
                print(f"   💰 Preço: R$ {produto['preco']}")
                print(f"   🌐 Site: {produto['site']}")
                print(f"   🔗 Link: {produto['link'][:60]}..." if produto['link'] else "   🔗 Link: Não encontrado")
                print("-" * 80)
                
    except KeyboardInterrupt:
        print("\n\n⏹️ Scraping interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ [ERRO INESPERADO] {str(e)}")
        print("💡 Por favor, reporte este erro para melhorias futuras.")
    
    print("\n👋 Obrigado por usar o Web Scraper HendelCode!")
