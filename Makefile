# Makefile para facilitar operações do Web Scraper Universal
# Uso rápido: make help

PYTHON?=.venv/bin/python
PIP?=.venv/bin/pip
UVICORN?=.venv/bin/uvicorn
PORT?=8000
HOST?=0.0.0.0
SITE?=mercado_livre
BUSCA?=notebook
PAGINAS?=1
DELAY?=1.0
JOB_FILE?=.jobid

.DEFAULT_GOAL := help

help:
	@echo "Alvos disponíveis:"
	@echo "  make venv          -> cria ambiente virtual (.venv)"
	@echo "  make install       -> instala dependências"
	@echo "  make run           -> roda servidor em modo dev (reload)"
	@echo "  make run-prod      -> roda servidor sem reload"
	@echo "  make kill          -> encerra processo na porta $(PORT)"
	@echo "  make job-start     -> inicia job (variáveis: SITE BUSCA PAGINAS DELAY)"
	@echo "  make job-status    -> mostra status do job salvo em $(JOB_FILE)"
	@echo "  make debug-page    -> testa captura bruta da página (SITE, BUSCA)"
	@echo "  make freeze        -> gera requirements.txt atualizado"
	@echo "  make clean-cache   -> remove caches py"

venv:
	@test -d .venv || python3 -m venv .venv
	@echo "[OK] venv pronta"

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "[OK] dependências instaladas"

run: install
	$(UVICORN) api:app --host $(HOST) --port $(PORT) --reload

run-prod: install
	$(UVICORN) api:app --host $(HOST) --port $(PORT) --log-level info

kill:
	- fuser -k $(PORT)/tcp 2>/dev/null || true
	@echo "[OK] Porta $(PORT) liberada"

job-start:
	@test -f requirements.txt || { echo "requirements.txt não encontrado"; exit 1; }
	@echo "Iniciando job: site=$(SITE) busca='$(BUSCA)' páginas=$(PAGINAS) delay=$(DELAY)"
	@JOB_ID=$$(curl -s -X POST "http://localhost:$(PORT)/scraping" \
	 -H "Content-Type: application/json" \
	 -d '{"site":"$(SITE)","termo_busca":"$(BUSCA)","max_paginas":$(PAGINAS),"delay":$(DELAY)}' | python -c 'import sys,json;print(json.load(sys.stdin).get("job_id",""))'); \
	 echo $$JOB_ID > $(JOB_FILE); \
	 echo "Job ID: $$JOB_ID"; \
	 test -n "$$JOB_ID" || { echo "Falha ao obter job id"; exit 1; }

job-status:
	@test -f $(JOB_FILE) || { echo "Arquivo $(JOB_FILE) não existe. Rode make job-start"; exit 1; }
	@JOB_ID=$$(cat $(JOB_FILE)); \
	 echo "Consultando job $$JOB_ID"; \
	 curl -s "http://localhost:$(PORT)/job/$$JOB_ID" | python -m json.tool

job-debug:
	@test -f $(JOB_FILE) || { echo "Arquivo $(JOB_FILE) não existe. Rode make job-start"; exit 1; }
	@JOB_ID=$$(cat $(JOB_FILE)); \
	 echo "Debug job $$JOB_ID"; \
	 curl -s "http://localhost:$(PORT)/job/$$JOB_ID/debug" | python -m json.tool

debug-page:
	@echo "Testando captura bruta: site=$(SITE) busca=$(BUSCA)"
	@curl -s "http://localhost:$(PORT)/debug/teste_pagina?site=$(SITE)&termo=$(BUSCA)" | python -m json.tool

freeze:
	$(PIP) freeze > requirements.txt
	@echo "[OK] requirements.txt atualizado"

clean-cache:
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type f -name '*.pyc' -delete
	@echo "[OK] caches removidos"
