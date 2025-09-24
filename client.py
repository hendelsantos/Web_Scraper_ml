#!/usr/bin/env python3
"""
Cliente simples para testar a Web Scraper API
"""

import requests
import time
import json

API_BASE_URL = "http://localhost:8000"

def listar_sites():
    """Lista sites disponíveis"""
    try:
        response = requests.get(f"{API_BASE_URL}/sites")
        if response.status_code == 200:
            sites = response.json()["sites_disponiveis"]
            print("\n🌐 Sites disponíveis:")
            for key, nome in sites.items():
                print(f"  - {key}: {nome}")
            return sites
        else:
            print(f"Erro ao listar sites: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Erro de conexão: {e}")
        return None

def iniciar_scraping(site, termo_busca, max_paginas=3):
    """Inicia um job de scraping"""
    data = {
        "site": site,
        "termo_busca": termo_busca,
        "max_paginas": max_paginas,
        "delay": 1.0
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/scraping", json=data)
        if response.status_code == 200:
            job_data = response.json()
            print(f"\n✅ Job iniciado!")
            print(f"Job ID: {job_data['job_id']}")
            print(f"Status: {job_data['status']}")
            return job_data['job_id']
        else:
            print(f"Erro ao iniciar scraping: {response.status_code}")
            print(response.text)
            return None
    except requests.RequestException as e:
        print(f"Erro de conexão: {e}")
        return None

def consultar_job(job_id):
    """Consulta o status de um job"""
    try:
        response = requests.get(f"{API_BASE_URL}/job/{job_id}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro ao consultar job: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Erro de conexão: {e}")
        return None

def aguardar_conclusao(job_id, timeout=300):
    """Aguarda a conclusão de um job"""
    start_time = time.time()
    
    print(f"\n⏳ Aguardando conclusão do job {job_id}...")
    
    while time.time() - start_time < timeout:
        job_data = consultar_job(job_id)
        if not job_data:
            return None
        
        status = job_data['status']
        progress = job_data.get('progress', '')
        
        print(f"Status: {status} - {progress}")
        
        if status == 'completed':
            return job_data
        elif status == 'failed':
            print(f"❌ Job falhou: {job_data.get('erro', 'Erro desconhecido')}")
            return job_data
        
        time.sleep(5)
    
    print(f"⏰ Timeout atingido após {timeout} segundos")
    return None

def exibir_resultados(job_data):
    """Exibe os resultados do scraping"""
    if job_data['status'] != 'completed':
        print("Job não foi concluído com sucesso")
        return
    
    produtos = job_data.get('produtos', [])
    total = job_data.get('total_produtos', 0)
    
    print(f"\n🎉 Scraping concluído!")
    print(f"Total de produtos encontrados: {total}")
    
    if produtos:
        print(f"\n📋 Primeiros {min(10, len(produtos))} produtos:")
        print("-" * 80)
        
        for i, produto in enumerate(produtos[:10], 1):
            print(f"{i:2d}. {produto['nome']}")
            print(f"    💰 Preço: R$ {produto['preco']}")
            print(f"    🌐 Site: {produto['site']}")
            if produto['link']:
                print(f"    🔗 Link: {produto['link'][:60]}...")
            print()

def main():
    """Função principal"""
    print("🎯 Cliente Web Scraper API")
    print("=" * 50)
    
    # 1. Listar sites
    sites = listar_sites()
    if not sites:
        print("Não foi possível listar os sites. Verifique se a API está rodando.")
        return
    
    # 2. Obter entrada do usuário
    print("\n" + "=" * 50)
    site_escolhido = input("Digite o ID do site desejado: ").strip()
    
    if site_escolhido not in sites:
        print(f"Site '{site_escolhido}' não é válido.")
        return
    
    termo_busca = input("Digite o produto para buscar: ").strip()
    if not termo_busca:
        print("Termo de busca não pode estar vazio.")
        return
    
    try:
        max_paginas = int(input("Máximo de páginas (padrão 3): ") or "3")
    except ValueError:
        max_paginas = 3
    
    # 3. Iniciar scraping
    job_id = iniciar_scraping(site_escolhido, termo_busca, max_paginas)
    if not job_id:
        return
    
    # 4. Aguardar conclusão
    resultado = aguardar_conclusao(job_id)
    if not resultado:
        return
    
    # 5. Exibir resultados
    exibir_resultados(resultado)
    
    # 6. Salvar em arquivo (opcional)
    salvar = input("\nDeseja salvar os resultados em JSON? (s/n): ").lower().strip()
    if salvar in ['s', 'sim', 'y', 'yes']:
        filename = f"resultados_{termo_busca.replace(' ', '_')}_{int(time.time())}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        print(f"📁 Resultados salvos em: {filename}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Operação cancelada pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
