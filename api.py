from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
import uuid
import json
from datetime import datetime
import os
import pandas as pd

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
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
}

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
        },
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
    return None

def realizar_scraping(job_id: str, site_config: dict, url_base: str, termo_busca: str, max_paginas: int, delay: float):
    """Função para realizar o scraping em background"""
    try:
        # Atualizar status para running
        job_storage[job_id]["status"] = "running"
        job_storage[job_id]["progress"] = "Iniciando scraping..."
        
        produtos = []
        pagina = 1
        
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
            
            job_storage[job_id]["progress"] = f"Processando página {pagina}..."
            
            try:
                resp = requests.get(url, headers=HEADERS, timeout=10)
                if resp.status_code != 200:
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                itens = soup.select(site_config['seletores']['item'])
                
                if not itens:
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

                    if nome:  # Só adiciona se tiver nome
                        produtos.append(Produto(
                            nome=nome,
                            preco=preco,
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
        
    except Exception as e:
        job_storage[job_id]["status"] = "failed"
        job_storage[job_id]["erro"] = str(e)
        job_storage[job_id]["completed_at"] = datetime.now().isoformat()

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
        df = pd.DataFrame(job_data["produtos"])
        
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

@app.delete("/job/{job_id}", summary="Deletar job")
async def deletar_job(job_id: str):
    """Deleta um job específico"""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    del job_storage[job_id]
    return {"message": f"Job {job_id} deletado com sucesso"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
