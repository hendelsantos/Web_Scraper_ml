#!/usr/bin/env python3
"""
🤖 Browser Engine - Navegador Real para Railway
Usa navegadores headless reais para evitar detecção
"""

import os
import time
import random
import tempfile
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import subprocess


class RealBrowserScraper:
    """Scraper usando navegador real headless"""
    
    def __init__(self):
        self.browser = None
        self.is_railway = os.environ.get('RAILWAY_ENVIRONMENT') is not None
        
    def setup_chrome_options(self):
        """Configura Chrome com máxima evasão"""
        options = [
            '--headless=new',  # Novo modo headless mais stealth
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-images',  # Mais rápido
            '--disable-javascript-harmony-shipping',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-field-trial-config',
            '--disable-back-forward-cache',
            '--disable-ipc-flooding-protection',
            '--window-size=1366,768',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        # Railway specific
        if self.is_railway:
            options.extend([
                '--single-process',  # Railway memory limits
                '--max_old_space_size=512',
                '--no-zygote',
                '--disable-dev-shm-usage',
            ])
            
        return options
    
    def get_page_content_with_chrome(self, url: str) -> Optional[str]:
        """Obtém conteúdo usando Chrome headless via subprocess"""
        try:
            # Criar script temporário para Chrome
            script = f'''
const puppeteer = require('puppeteer');

(async () => {{
  const browser = await puppeteer.launch({{
    headless: 'new',
    args: {self.setup_chrome_options()},
    executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || '/usr/bin/google-chrome',
  }});
  
  const page = await browser.newPage();
  
  // Simular comportamento humano
  await page.setViewport({{ width: 1366, height: 768 }});
  
  // Headers realistas
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  
  await page.setExtraHTTPHeaders({{
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.google.com.br/',
  }});
  
  // Navegar com timeout
  await page.goto('{url}', {{
    waitUntil: 'networkidle2',
    timeout: 30000
  }});
  
  // Aguardar elementos carregarem
  await page.waitForTimeout({random.randint(2000, 5000)});
  
  // Simular scroll humano
  await page.evaluate(() => {{
    window.scrollBy(0, Math.floor(Math.random() * 1000));
  }});
  
  await page.waitForTimeout({random.randint(1000, 3000)});
  
  const content = await page.content();
  console.log(content);
  
  await browser.close();
}})().catch(console.error);
            '''
            
            # Salvar script temporário
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(script)
                script_path = f.name
            
            try:
                # Executar com Node.js
                result = subprocess.run(
                    ['node', script_path], 
                    capture_output=True, 
                    text=True, 
                    timeout=60
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout
                else:
                    print(f"❌ Chrome subprocess falhou: {result.stderr}")
                    return None
                    
            finally:
                # Limpar arquivo temporário
                try:
                    os.unlink(script_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Erro no Chrome headless: {e}")
            return None
    
    def get_page_with_curl(self, url: str) -> Optional[str]:
        """Fallback usando curl com headers avançados"""
        try:
            headers = [
                '--header', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                '--header', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                '--header', 'Accept-Language: pt-BR,pt;q=0.9,en;q=0.8',
                '--header', 'Accept-Encoding: gzip, deflate, br',
                '--header', 'Cache-Control: no-cache',
                '--header', 'Connection: keep-alive',
                '--header', 'Referer: https://www.google.com.br/',
            ]
            
            cmd = ['curl', '-s', '--compressed', '--max-time', '30'] + headers + [url]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
            else:
                print(f"❌ Curl falhou: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Erro no curl: {e}")
            return None
    
    def scrape_url(self, url: str) -> Optional[str]:
        """Scraping principal com múltiplas estratégias"""
        print(f"🌐 Iniciando scraping: {url}")
        
        # Tentar Chrome headless primeiro
        content = self.get_page_content_with_chrome(url)
        
        if not content:
            print("🔄 Fallback para curl...")
            content = self.get_page_with_curl(url)
            
        if content:
            print(f"✅ Conteúdo obtido: {len(content)} caracteres")
            return content
        else:
            print("❌ Todas as estratégias falharam")
            return None


# Instância global
real_browser = RealBrowserScraper()


def scrape_with_real_browser(url: str) -> Optional[BeautifulSoup]:
    """Interface principal para scraping com navegador real"""
    content = real_browser.scrape_url(url)
    
    if content:
        return BeautifulSoup(content, 'html.parser')
    else:
        return None


if __name__ == "__main__":
    # Teste
    soup = scrape_with_real_browser("https://lista.mercadolivre.com.br/notebook")
    if soup:
        items = soup.select('li.ui-search-layout__item')
        print(f"✅ Encontrados {len(items)} itens")
        if items:
            first = items[0]
            nome = first.select_one('.poly-component__title')
            if nome:
                print(f"Primeiro item: {nome.get_text(strip=True)}")
    else:
        print("❌ Scraping falhou")
