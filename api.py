from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import requests
from requests import Session
from bs4 import BeautifulSoup
import time
import urllib.parse
import uuid
import json
from datetime import datetime
import os
import pandas as pd
import random
import math
import hashlib
from itertools import cycle
import threading
import atexit

# ==========================
# CONFIGURAÇÃO DA API
# ==========================
app = FastAPI(
    title="🎯 Web Scraper Universal API",
    description="API para fazer scraping de produtos em diferentes sites de e-commerce",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para permitir requisições de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos (HTML, CSS, JS)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ==========================
# CONFIGURAÇÕES GLOBAIS
# ==========================
DELAY = 1
BASE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

USER_AGENTS = [
    # Lista reduzida (pode expandir depois)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

def build_headers():
    ua = random.choice(USER_AGENTS)
    h = BASE_HEADERS.copy()
    h["User-Agent"] = ua
    h["Referer"] = "https://www.google.com"
    return h

# ==========================
# PROXIES (opcional)
# Variável de ambiente: SCRAPER_PROXIES="host1:port,host2:port,http://user:pass@host3:3128"
# ==========================
def _carregar_proxies():
    raw = os.environ.get("SCRAPER_PROXIES", "").strip()
    if not raw:
        return []
    proxies = []
    for part in raw.split(','):
        p = part.strip()
        if not p:
            continue
        if '://' not in p:
            p = f"http://{p}"
        proxies.append(p)
    return proxies

PROXIES_LIST = _carregar_proxies()
PROXIES_CYCLE = cycle(PROXIES_LIST) if PROXIES_LIST else None

def _obter_proxy():
    if not PROXIES_CYCLE:
        return None
    try:
        return next(PROXIES_CYCLE)
    except Exception:
        return None

# Dicionário de sites suportados
SITES_SUPORTADOS = {
    "mercado_livre": {
        "nome": "Mercado Livre",
        "base_url": "https://lista.mercadolivre.com.br",
        "seletores": {
            "item": "li.ui-search-layout__item",
            "nome": ".poly-component__title",
            "preco": ".andes-money-amount__fraction",
            "link": ".poly-component__title",
            "avaliacao": "[class*='rating']",
            "reviews": "[class*='review']"
    },  # adicionaremos fallback dinâmico no código
        "paginacao": "_Desde_{}"
    },
    "amazon": {
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
    },
    "ebay": {
        "nome": "eBay",
        "base_url": "https://www.ebay.com/sch/i.html?_nkw=",
        "seletores": {
            "item": "li.s-item",
            "nome": ".s-item__title",
            "preco": ".s-item__price",
            "link": ".s-item__link",
            "avaliacao": ".x-star-rating span.clipped",
            "reviews": ".s-item__reviews-count"
        },
        "paginacao": "&_pgn={}"
    }
}

# Armazenamento em memória para jobs (em produção usaria Redis ou banco de dados)
job_storage = {}

# ==========================
# MODELOS PYDANTIC
# ==========================
class ScrapingRequest(BaseModel):
    site: str  # "mercado_livre" ou "amazon"
    termo_busca: str
    max_paginas: Optional[int] = 10
    delay: Optional[float] = 1.0

class Produto(BaseModel):
    nome: Optional[str]
    preco: Optional[str]
    preco_num: Optional[float]
    link: Optional[str]
    site: str

class ScrapingResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: Optional[str]
    total_produtos: Optional[int]
    produtos: Optional[List[Produto]]
    erro: Optional[str]
    created_at: str
    completed_at: Optional[str]

class SitesResponse(BaseModel):
    sites_disponiveis: Dict[str, str]

PERSIST_FILE = os.environ.get("SCRAPER_JOBS_FILE", "jobs_data.json")
_lock_persist = threading.Lock()

def _persist_jobs():
    try:
        with _lock_persist:
            serial = {}
            for jid, data in job_storage.items():
                serial[jid] = {
                    k: (v if k != 'produtos' else [p.dict() for p in v]) for k, v in data.items()
                }
            with open(PERSIST_FILE, 'w', encoding='utf-8') as f:
                json.dump(serial, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _load_jobs():
    if not os.path.exists(PERSIST_FILE):
        return
    try:
        with open(PERSIST_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for jid, jd in data.items():
            if 'produtos' in jd and isinstance(jd['produtos'], list):
                jd['produtos'] = [Produto(**p) for p in jd['produtos']]
            job_storage[jid] = jd
    except Exception:
        pass

_load_jobs()
atexit.register(_persist_jobs)

# ==========================
# FUNÇÕES AUXILIARES
# ==========================
def construir_url_busca(site_config, termo):
    """Constrói a URL de busca baseada no site e termo"""
    if site_config['nome'] == "Mercado Livre":
        termo_codificado = urllib.parse.quote_plus(termo)
        return f"{site_config['base_url']}/{termo_codificado}"
    elif site_config['nome'] == "Amazon":
        termo_codificado = urllib.parse.quote_plus(termo)
        return f"{site_config['base_url']}{termo_codificado}"
    elif site_config['nome'] == 'eBay':
        termo_codificado = urllib.parse.quote_plus(termo)
        return f"{site_config['base_url']}{termo_codificado}"
    return None

def _parse_preco(texto: Optional[str]) -> Optional[float]:
    if not texto:
        return None
    try:
        # Remove caracteres não numéricos exceto separadores
        t = texto.strip()
        # Mercado Livre normalmente: '1.234' (sem centavos) ou '1.234,56'
        t = t.replace('\u00a0', ' ').replace('R$','').strip()
        t = t.replace('.', '').replace(',', '.')
        # Filtrar múltiplos espaços
        t = ''.join(ch for ch in t if ch.isdigit() or ch == '.')
        if not t:
            return None
        return float(t)
    except Exception:
        return None

def _inicializar_sessao(site_config: dict) -> Session:
    s = Session()
    # Primeiro hit para obter cookies base (importante para ML)
    try:
        if site_config['nome'] == 'Mercado Livre':
            s.get("https://www.mercadolivre.com.br", headers=build_headers(), timeout=10)
    except Exception:
        pass
    return s

def _detectar_captcha(html: str) -> bool:
    padroes = [
        'captcha',
        'não é um robô',
        'verifique que você',
        'access denied',
        'temporariamente bloqueado'
    ]
    lower = html.lower()
    return any(p in lower for p in padroes)

def realizar_scraping(job_id: str, site_config: dict, url_base: str, termo_busca: str, max_paginas: int, delay: float):
    """Função para realizar o scraping em background"""
    try:
        # Atualizar status para running
        job_storage[job_id]["status"] = "running"
        job_storage[job_id]["progress"] = "Iniciando scraping..."
        
        produtos = []
        pagina = 1
        
        sessao = _inicializar_sessao(site_config)
        job_storage[job_id]['debug'] = {
            'tentativas': 0,
            'seletor_principal_hits': 0,
            'fallback_usado': None,
            'possivel_captcha': False,
            'primeira_pagina_salva': False,
            'proxies_habilitados': bool(PROXIES_LIST),
            'total_proxies': len(PROXIES_LIST),
            'ultimo_proxy': None,
            'erros_proxy': 0
        }
        while pagina <= max_paginas:
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
            elif site_config['nome'] == 'eBay':
                if pagina > 1:
                    url = f"{url_base}&_pgn={pagina}"
                else:
                    url = url_base
            
            job_storage[job_id]["progress"] = f"Processando página {pagina}..."
            
            try:
                attempt = 0
                max_retries = int(os.environ.get("SCRAPER_MAX_RETRIES", "3"))
                backoff_base = float(os.environ.get("SCRAPER_BACKOFF_BASE", "1.5"))
                while True:
                    headers = build_headers()
                    proxy = _obter_proxy()
                    req_kwargs = {"headers": headers, "timeout": 15}
                    if proxy:
                        req_kwargs["proxies"] = {"http": proxy, "https": proxy}
                        job_storage[job_id]['debug']['ultimo_proxy'] = proxy
                    try:
                        resp = sessao.get(url, **req_kwargs)
                    except Exception as proxy_err:
                        job_storage[job_id]['debug']['erros_proxy'] += 1
                        if proxy and job_storage[job_id]['debug']['erros_proxy'] < len(PROXIES_LIST) + 3:
                            # tenta próximo proxy
                            continue
                        job_storage[job_id]["progress"] = f"Erro de rede: {proxy_err}"
                        break
                    job_storage[job_id]['debug']['tentativas'] += 1
                    status = resp.status_code
                    if status == 200:
                        break
                    if status in (429, 503, 500) and attempt < max_retries:
                        sleep_for = (backoff_base ** attempt) + random.uniform(0, 0.5)
                        job_storage[job_id]["progress"] = f"Status {status} - retry {attempt+1}/{max_retries} em {sleep_for:.1f}s"
                        time.sleep(sleep_for)
                        attempt += 1
                        continue
                    # Falhou definitivo
                    job_storage[job_id]["progress"] = f"Falha HTTP {status} - encerrando"
                    # Salvar HTML para debug
                    try:
                        debug_path = f"/tmp/scraping/job_{job_id}_pagina_{pagina}_erro.html"
                        with open(debug_path, 'w', encoding='utf-8') as f:
                            f.write(resp.text[:200000])
                    except Exception:
                        pass
                    break
                if resp.status_code != 200:
                    break

                html_text = resp.text
                if pagina == 1 and not job_storage[job_id]['debug']['primeira_pagina_salva'] and os.environ.get('SCRAPER_SAVE_FIRST','1') == '1':
                    try:
                        with open(f"/tmp/scraping/job_{job_id}_pagina1.html", 'w', encoding='utf-8') as f:
                            f.write(html_text[:300000])
                        job_storage[job_id]['debug']['primeira_pagina_salva'] = True
                    except Exception:
                        pass

                if _detectar_captcha(html_text):
                    job_storage[job_id]['debug']['possivel_captcha'] = True
                    job_storage[job_id]['progress'] = 'Possível captcha/bloqueio detectado.'

                soup = BeautifulSoup(html_text, "html.parser")
                itens = soup.select(site_config['seletores']['item'])
                job_storage[job_id]['debug']['seletor_principal_hits'] = len(itens)

                # Fallback alternativo para Mercado Livre (variações de layout)
                if site_config['nome'] == 'Mercado Livre' and not itens:
                    alt_selectors = [
                        'div.ui-search-result__wrapper',
                        'div.ui-search-result',
                        'li.ui-search-layout__item shops__layout-item',
                        'div.poly-card'
                    ]
                    for sel in alt_selectors:
                        itens = soup.select(sel)
                        if itens:
                            job_storage[job_id]["progress"] = f"Fallback de seletor aplicado: {sel}"
                            job_storage[job_id]['debug']['fallback_usado'] = sel
                            break

                if not itens:
                    # Salvar HTML desta página para debug (primeiras 200KB)
                    try:
                        debug_path = f"/tmp/scraping/job_{job_id}_pagina_{pagina}_sem_itens.html"
                        with open(debug_path, 'w', encoding='utf-8') as f:
                            f.write(html_text[:200000])
                        job_storage[job_id]["progress"] = "Nenhum item encontrado - layout pode ter mudado (HTML salvo)."
                    except Exception:
                        pass
                    break

                for item in itens:
                    nome_elem = item.select_one(site_config['seletores']['nome'])
                    preco_elem = item.select_one(site_config['seletores']['preco'])
                    link_elem = item.select_one(site_config['seletores']['link'])

                    nome = nome_elem.get_text(strip=True) if nome_elem else None
                    preco = preco_elem.get_text(strip=True) if preco_elem else None
                    
                    link = None
                    if link_elem:
                        if link_elem.get('href'):
                            link = link_elem['href']
                            if link and link.startswith('/'):
                                if site_config['nome'] == "Mercado Livre":
                                    link = f"https://www.mercadolivre.com.br{link}"
                                elif site_config['nome'] == "Amazon":
                                    link = f"https://www.amazon.com.br{link}"

                    if nome:
                        produtos.append(Produto(
                            nome=nome,
                            preco=preco,
                            preco_num=_parse_preco(preco),
                            link=link,
                            site=site_config['nome']
                        ))

                pagina += 1
                time.sleep(delay)
                
            except Exception as e:
                job_storage[job_id]["progress"] = f"Erro na página {pagina}: {str(e)}"
                break
        
        # Completar job
        job_storage[job_id]["status"] = "completed"
        job_storage[job_id]["total_produtos"] = len(produtos)
        job_storage[job_id]["produtos"] = produtos
        job_storage[job_id]["completed_at"] = datetime.now().isoformat()
        job_storage[job_id]["progress"] = f"Concluído! {len(produtos)} produtos encontrados."
        _persist_jobs()
    except Exception as e:
        job_storage[job_id]["status"] = "failed"
        job_storage[job_id]["erro"] = str(e)
        job_storage[job_id]["completed_at"] = datetime.now().isoformat()
        _persist_jobs()

# ==========================
# ENDPOINTS DA API
# ==========================

@app.get("/", summary="Interface Web")
async def interface():
    """Serve a interface web principal"""
    interface_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(interface_file):
        return FileResponse(interface_file)
    else:
        return {
            "message": "🎯 Web Scraper Universal API",
            "version": "2.0.0",
            "documentation": "/docs",
            "interface": "Interface web não encontrada em /static/index.html",
            "endpoints": {
                "GET /sites": "Lista sites disponíveis",
                "POST /scraping": "Inicia um job de scraping",
                "GET /job/{job_id}": "Consulta status de um job"
            }
        }

@app.get("/api", summary="Informações da API")
async def api_info():
    """Endpoint com informações da API"""
    return {
        "message": "🎯 Web Scraper Universal API",
        "version": "2.0.0",
        "documentation": "/docs",
        "endpoints": {
            "GET /sites": "Lista sites disponíveis",
            "POST /scraping": "Inicia um job de scraping",
            "GET /job/{job_id}": "Consulta status de um job"
        }
    }

@app.get("/sites", response_model=SitesResponse, summary="Sites disponíveis")
async def listar_sites():
    """Lista todos os sites disponíveis para scraping"""
    sites = {key: config["nome"] for key, config in SITES_SUPORTADOS.items()}
    return SitesResponse(sites_disponiveis=sites)

@app.post("/scraping", response_model=ScrapingResponse, summary="Iniciar scraping")
async def iniciar_scraping(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """
    Inicia um job de scraping assíncrono
    
    - **site**: ID do site ("mercado_livre" ou "amazon")
    - **termo_busca**: Produto a ser buscado
    - **max_paginas**: Máximo de páginas a processar (padrão: 10)
    - **delay**: Delay entre requisições em segundos (padrão: 1.0)
    """
    
    # Validar site
    if request.site not in SITES_SUPORTADOS:
        raise HTTPException(
            status_code=400, 
            detail=f"Site não suportado. Sites disponíveis: {list(SITES_SUPORTADOS.keys())}"
        )
    
    # Validar termo de busca
    if not request.termo_busca.strip():
        raise HTTPException(status_code=400, detail="Termo de busca não pode estar vazio")
    
    # Gerar job ID
    job_id = str(uuid.uuid4())
    
    # Configurar job
    site_config = SITES_SUPORTADOS[request.site]
    url_busca = construir_url_busca(site_config, request.termo_busca)
    
    if not url_busca:
        raise HTTPException(status_code=500, detail="Erro ao construir URL de busca")
    
    # Inicializar job storage
    job_storage[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": "Job criado, aguardando processamento...",
        "total_produtos": 0,
        "produtos": [],
        "erro": None,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "config": {
            "site": request.site,
            "termo_busca": request.termo_busca,
            "max_paginas": request.max_paginas,
            "delay": request.delay
        }
    }
    _persist_jobs()
    
    # Iniciar processamento em background
    background_tasks.add_task(
        realizar_scraping,
        job_id,
        site_config,
        url_busca,
        request.termo_busca,
        request.max_paginas,
        request.delay
    )
    
    return ScrapingResponse(
        job_id=job_id,
        status="pending",
        message="Job de scraping iniciado. Use o job_id para consultar o status."
    )

@app.get("/job/{job_id}", response_model=JobStatus, summary="Status do job")
async def consultar_job(job_id: str):
    """
    Consulta o status e resultados de um job de scraping
    
    - **job_id**: ID do job retornado pelo endpoint /scraping
    """
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    job_data = job_storage[job_id]
    
    return JobStatus(
        job_id=job_id,
        status=job_data["status"],
        progress=job_data["progress"],
        total_produtos=job_data["total_produtos"],
        produtos=job_data["produtos"],
        erro=job_data["erro"],
        created_at=job_data["created_at"],
        completed_at=job_data["completed_at"]
    )

@app.get("/job/{job_id}/download", summary="Download dos resultados")
async def download_job_results(job_id: str):
    """Faz download dos resultados em formato Excel"""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    job_data = job_storage[job_id]
    
    if job_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job ainda não foi concluído")
    
    if not job_data["produtos"]:
        raise HTTPException(status_code=404, detail="Nenhum produto encontrado para download")
    
    try:
        # Criar DataFrame
        df = pd.DataFrame([p.dict() for p in job_data["produtos"]])
        
        # Salvar em buffer
        from io import BytesIO
        buffer = BytesIO()

        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Produtos')

        buffer.seek(0)

        # Retornar arquivo
        from fastapi.responses import StreamingResponse

        return StreamingResponse(
            BytesIO(buffer.read()),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                "Content-Disposition": f"attachment; filename=scraping_{job_id}.xlsx"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar arquivo: {str(e)}")

@app.get("/jobs", summary="Listar todos os jobs")
async def listar_jobs():
    """Lista todos os jobs e seus status"""
    jobs_summary = []
    for job_id, job_data in job_storage.items():
        jobs_summary.append({
            "job_id": job_id,
            "status": job_data["status"],
            "termo_busca": job_data["config"]["termo_busca"],
            "site": job_data["config"]["site"],
            "total_produtos": job_data["total_produtos"],
            "created_at": job_data["created_at"]
        })
    
    return {"jobs": jobs_summary, "total": len(jobs_summary)}

@app.get("/healthz", summary="Healthcheck", tags=["Infra"])
async def healthcheck():
    """Endpoint rápido para verificação de saúde (usado por plataformas de deploy)."""
    uptime = None
    try:
        # created_at do primeiro job como referência de uptime se existir
        if job_storage:
            first = min([j["created_at"] for j in job_storage.values()])
            uptime = first
    except Exception:
        uptime = None
    return {
        "status": "ok",
        "version": "2.0.0",
        "time": datetime.utcnow().isoformat() + "Z",
        "jobs": len(job_storage),
        "uptime_ref": uptime
    }

@app.get("/job/{job_id}/json", summary="Resultados em JSON bruto")
async def job_json(job_id: str):
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    job_data = job_storage[job_id]
    if job_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job ainda não concluído")
    return {
        "job_id": job_id,
        "total": job_data["total_produtos"],
        "produtos": [p.dict() for p in job_data["produtos"]]
    }

@app.get("/job/{job_id}/debug", summary="Debug do job", tags=["Debug"])
async def job_debug(job_id: str):
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    data = job_storage[job_id]
    return {
        'job_id': job_id,
        'status': data['status'],
        'progress': data['progress'],
        'debug': data.get('debug', {}),
        'config': data.get('config')
    }

@app.get("/debug/teste_pagina", summary="Teste bruto de captura", tags=["Debug"])
async def debug_teste_pagina(site: str = "mercado_livre", termo: str = "notebook"):
    if site not in SITES_SUPORTADOS:
        raise HTTPException(status_code=400, detail="Site inválido")
    site_config = SITES_SUPORTADOS[site]
    url = construir_url_busca(site_config, termo)
    headers = build_headers()
    r = requests.get(url, headers=headers, timeout=15)
    content = r.text
    h = hashlib.sha256(content.encode('utf-8')).hexdigest()
    return {
        "status_code": r.status_code,
        "url": url,
        "length": len(content),
        "sha256": h,
        "sample_start": content[:400]
    }

@app.delete("/job/{job_id}", summary="Deletar job")
async def deletar_job(job_id: str):
    """Deleta um job específico"""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    del job_storage[job_id]
    _persist_jobs()
    return {"message": f"Job {job_id} deletado com sucesso"}

@app.get("/metrics", summary="Métricas básicas", tags=["Infra"])
async def metrics():
    total_jobs = len(job_storage)
    concluidos = sum(1 for j in job_storage.values() if j['status'] == 'completed')
    falhados = sum(1 for j in job_storage.values() if j['status'] == 'failed')
    rodando = sum(1 for j in job_storage.values() if j['status'] == 'running')
    medias = None
    try:
        produtos = [j['total_produtos'] for j in job_storage.values() if j.get('total_produtos') is not None]
        if produtos:
            medias = {
                'media_produtos_por_job': sum(produtos)/len(produtos),
                'max_produtos': max(produtos),
                'min_produtos': min(produtos)
            }
    except Exception:
        pass
    return {
        'total_jobs': total_jobs,
        'concluidos': concluidos,
        'falhados': falhados,
        'rodando': rodando,
        'medias': medias
    }

@app.get("/job/{job_id}/html/{pagina}", summary="Download HTML debug", tags=["Debug"])
async def job_html(job_id: str, pagina: int):
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    base_dir = "/tmp/scraping"
    candidates = [
        f"{base_dir}/job_{job_id}_pagina{pagina}.html",
        f"{base_dir}/job_{job_id}_pagina_{pagina}_sem_itens.html",
        f"{base_dir}/job_{job_id}_pagina_{pagina}_erro.html"
    ]
    for c in candidates:
        if os.path.exists(c):
            return FileResponse(c, media_type='text/html')
    raise HTTPException(status_code=404, detail="Arquivo HTML não encontrado para esta página")

@app.get("/metrics", summary="Métricas básicas", tags=["Infra"])
async def metrics():
    total_jobs = len(job_storage)
    concluidos = sum(1 for j in job_storage.values() if j['status'] == 'completed')
    falhados = sum(1 for j in job_storage.values() if j['status'] == 'failed')
    rodando = sum(1 for j in job_storage.values() if j['status'] == 'running')
    medias = None
    try:
        produtos = [j['total_produtos'] for j in job_storage.values() if j.get('total_produtos') is not None]
        if produtos:
            medias = {
                'media_produtos_por_job': sum(produtos)/len(produtos),
                'max_produtos': max(produtos),
                'min_produtos': min(produtos)
            }
    except Exception:
        pass
    return {
        'total_jobs': total_jobs,
        'concluidos': concluidos,
        'falhados': falhados,
        'rodando': rodando,
        'medias': medias
    }

@app.get("/job/{job_id}/html/{pagina}", summary="Download HTML debug", tags=["Debug"])
async def job_html(job_id: str, pagina: int):
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    base_dir = "/tmp/scraping"
    candidates = [
        f"{base_dir}/job_{job_id}_pagina{pagina}.html",
        f"{base_dir}/job_{job_id}_pagina_{pagina}_sem_itens.html",
        f"{base_dir}/job_{job_id}_pagina_{pagina}_erro.html"
    ]
    for c in candidates:
        if os.path.exists(c):
            return FileResponse(c, media_type='text/html')
    raise HTTPException(status_code=404, detail="Arquivo HTML não encontrado para esta página")

if __name__ == "__main__":
    import uvicorn
    # Configuração para Railway/produção
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"🚀 Iniciando servidor em {host}:{port}")
    print(f"📡 Interface: http://{host}:{port}")
    print(f"📚 Docs: http://{host}:{port}/docs")
    
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_level="info"
    )
