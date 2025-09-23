import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# ==========================
# CONFIGURAÇÕES
# ==========================
BASE_URL = "https://lista.mercadolivre.com.br/playstation-5"  # URL de busca para PlayStation 5
DELAY = 1  # Segundos de espera entre requisições para evitar bloqueio

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
}

# ==========================
# FUNÇÃO PARA BUSCAR PRODUTOS
# ==========================
def coletar_produtos():
    produtos = []
    pagina = 1

    while True:
        url = f"{BASE_URL}_Desde_{(pagina-1)*50+1}" if pagina > 1 else BASE_URL
        print(f"[INFO] Coletando página {pagina} -> {url}")

        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print(f"[ERRO] Não foi possível acessar a página (status {resp.status_code}).")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        itens = soup.select("li.ui-search-layout__item")
        if not itens:
            print("[INFO] Não há mais produtos.")
            break

        for item in itens:
            # Seletores atualizados para a estrutura atual do ML
            nome = item.select_one(".poly-component__title")
            preco = item.select_one(".andes-money-amount__fraction")
            link = item.select_one(".poly-component__title")
            avaliacao_el = item.select_one("[class*='rating']")
            qtd_reviews_el = item.select_one("[class*='review']")

            produtos.append({
                "nome": nome.get_text(strip=True) if nome else None,
                "preco": preco.get_text(strip=True) if preco else None,
                "link": link["href"] if link and link.get("href") else None,
                "avaliacao": None,  # Temporariamente None até encontrar o seletor correto
                "reviews": None     # Temporariamente None até encontrar o seletor correto
            })

        pagina += 1
        time.sleep(DELAY)

    return produtos

# ==========================
# PROGRAMA PRINCIPAL
# ==========================
if __name__ == "__main__":
    produtos = coletar_produtos()

    if not produtos:
        print("[ERRO] Nenhum produto encontrado.")
    else:
        df = pd.DataFrame(produtos)

        # Ordena por categoria (se existir) e depois por avaliação (decrescente)
        if "avaliacao" in df.columns:
            df.sort_values(by=["avaliacao"], ascending=False, inplace=True)

        # Salva para Excel
        df.to_excel("produtos.xlsx", index=False)
        print(f"[SUCESSO] {len(produtos)} produtos exportados para produtos.xlsx")
