#!/usr/bin/env python3
"""
🥷 Técnicas Avançadas de Anti-Detecção para Web Scraping

Este módulo implementa técnicas sofisticadas para evitar detecção 
por sistemas anti-bot de sites de e-commerce.
"""

import random
import time
import hashlib
import base64
import json
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class StealthScraper:
    """Scraper com técnicas avançadas anti-detecção"""
    
    def __init__(self):
        self.session_fingerprints = {}
        self.request_history = []
        self.last_request_time = {}
        
    def generate_browser_fingerprint(self) -> Dict:
        """Gera fingerprint de navegador realista"""
        # Combinações realistas de OS + Browser
        configs = [
            {
                "os": "Windows NT 10.0; Win64; x64",
                "browser": "Chrome/120.0.0.0",
                "engine": "537.36",
                "vendor": "Google Inc.",
                "languages": ["pt-BR", "pt", "en-US", "en"],
                "timezone": "America/Sao_Paulo",
                "screen": {"width": 1366, "height": 768, "colorDepth": 24},
                "webgl_vendor": "Google Inc. (Intel)",
                "webgl_renderer": "ANGLE (Intel, Intel(R) HD Graphics 620 Direct3D11 vs_5_0 ps_5_0)"
            },
            {
                "os": "Macintosh; Intel Mac OS X 10_15_7",
                "browser": "Chrome/119.0.0.0",
                "engine": "537.36",
                "vendor": "Google Inc.",
                "languages": ["pt-BR", "en-US", "pt", "en"],
                "timezone": "America/Sao_Paulo",
                "screen": {"width": 1440, "height": 900, "colorDepth": 24},
                "webgl_vendor": "Apple Inc.",
                "webgl_renderer": "Apple GPU"
            },
            {
                "os": "X11; Linux x86_64",
                "browser": "Chrome/118.0.0.0",
                "engine": "537.36",
                "vendor": "Google Inc.",
                "languages": ["pt-BR", "pt", "en-US", "en"],
                "timezone": "America/Sao_Paulo", 
                "screen": {"width": 1920, "height": 1080, "colorDepth": 24},
                "webgl_vendor": "Mesa",
                "webgl_renderer": "Mesa DRI Intel(R) Graphics"
            }
        ]
        
        return random.choice(configs)
    
    def calculate_tls_fingerprint(self) -> str:
        """Simula TLS fingerprint de navegador real"""
        # Baseado em configurações TLS reais de navegadores
        tls_configs = [
            "769,47-53,0-23,65281,10,11,35,16,5,13,18,51,45,43,10,21",  # Chrome
            "769,47-53,0-23,65281,10,11,35,16,5,51,43,13,45,28,21",     # Firefox
            "769,47-53,0-23,65281,10,11,35,5,16,13,18,51,45,43,21"      # Safari
        ]
        return random.choice(tls_configs)
    
    def add_canvas_noise(self, base_string: str) -> str:
        """Simula variação de canvas fingerprint"""
        # Canvas fingerprinting varia ligeiramente entre execuções
        noise = random.randint(1, 10)
        return hashlib.sha256((base_string + str(noise)).encode()).hexdigest()[:16]
    
    def generate_webrtc_leak(self) -> Dict:
        """Gera dados WebRTC realistas (mas fake)"""
        # IPs privados comuns em redes residenciais
        private_ips = [
            "192.168.0." + str(random.randint(100, 254)),
            "192.168.1." + str(random.randint(100, 254)),
            "10.0.0." + str(random.randint(100, 254)),
            "172.16.0." + str(random.randint(100, 254))
        ]
        
        return {
            "local_ip": random.choice(private_ips),
            "public_ip": None,  # Bloqueado por VPN/Firewall
            "stun_servers": ["stun.l.google.com:19302", "stun1.l.google.com:19302"]
        }
    
    def simulate_mouse_movement(self) -> List[Dict]:
        """Gera dados de movimento de mouse realistas"""
        movements = []
        x, y = random.randint(100, 800), random.randint(100, 600)
        
        for _ in range(random.randint(5, 15)):
            # Movimento humano com aceleração/desaceleração
            dx = random.gauss(0, 50)  # Distribuição normal
            dy = random.gauss(0, 50)
            x = max(0, min(1366, x + dx))
            y = max(0, min(768, y + dy))
            
            movements.append({
                "x": int(x),
                "y": int(y),
                "timestamp": time.time() * 1000 + random.uniform(-10, 10)
            })
            
        return movements
    
    def generate_keyboard_timing(self, text: str) -> List[Dict]:
        """Simula timing de digitação humana"""
        if not text:
            return []
            
        events = []
        base_time = time.time() * 1000
        
        for i, char in enumerate(text):
            # Variação humana na velocidade de digitação
            if char == ' ':
                delay = random.uniform(100, 300)  # Espaços mais lentos
            elif char.isupper():
                delay = random.uniform(120, 250)  # Maiúsculas mais lentas (Shift)
            else:
                delay = random.uniform(80, 200)   # Caracteres normais
            
            base_time += delay
            events.append({
                "key": char,
                "timestamp": base_time,
                "duration": random.uniform(50, 150)
            })
            
        return events
    
    def add_human_delays(self, min_delay: float = 1.0, max_delay: float = 5.0):
        """Adiciona delays humanos realistas"""
        delay = random.uniform(min_delay, max_delay)
        
        # Variações baseadas em comportamento real:
        if random.random() < 0.1:  # 10% das vezes delay mais longo (distração)
            delay += random.uniform(5, 15)
        elif random.random() < 0.3:  # 30% delay mais rápido (usuário experiente)  
            delay *= 0.5
            
        time.sleep(delay)
    
    def rotate_session_identity(self, session: requests.Session, domain: str):
        """Rotaciona identidade completa da sessão"""
        fingerprint = self.generate_browser_fingerprint()
        
        # Atualizar headers baseado no fingerprint
        session.headers.update({
            'User-Agent': f"Mozilla/5.0 ({fingerprint['os']}) AppleWebKit/{fingerprint['engine']} (KHTML, like Gecko) Chrome/{fingerprint['browser']} Safari/{fingerprint['engine']}",
            'Accept-Language': ','.join(fingerprint['languages'][:2]) + ';q=0.9,' + ','.join(fingerprint['languages'][2:]) + ';q=0.8',
            'Sec-Ch-Ua-Platform': f'"{fingerprint["os"].split(";")[0]}"',
            'Sec-Ch-Viewport-Width': str(fingerprint['screen']['width']),
            'Sec-Ch-Viewport-Height': str(fingerprint['screen']['height']),
        })
        
        # Armazenar fingerprint para consistência
        self.session_fingerprints[domain] = fingerprint
        
    def mimic_real_browsing(self, session: requests.Session, domain: str, search_term: str):
        """Simula navegação real antes do scraping"""
        try:
            base_url = f"https://{domain}"
            
            # 1. Página inicial
            response = session.get(base_url, timeout=15)
            self.add_human_delays(2, 4)
            
            # 2. Seções populares (simulando exploração)
            if 'mercadolivre' in domain:
                popular_sections = ['/ofertas', '/mais-vendidos', '/lancamentos']
            elif 'amazon' in domain:
                popular_sections = ['/gp/bestsellers', '/gp/new-releases', '/deals']
            else:
                return
                
            if random.random() > 0.5:  # 50% das vezes
                section = random.choice(popular_sections)
                session.get(f"{base_url}{section}", timeout=15)
                self.add_human_delays(3, 6)
            
            # 3. Busca genérica relacionada
            if random.random() > 0.6:  # 40% das vezes
                generic_terms = [
                    search_term.split()[0] if search_term else 'produto',
                    'oferta', 'promoção', 'desconto'
                ]
                generic_term = random.choice(generic_terms)
                
                if 'mercadolivre' in domain:
                    search_url = f"{base_url}/{generic_term}"
                elif 'amazon' in domain:
                    search_url = f"{base_url}/s?k={generic_term}"
                    
                session.get(search_url, timeout=15) 
                self.add_human_delays(4, 8)
                
        except Exception:
            pass  # Se falhar, continua normalmente
            
    def is_rate_limited(self, domain: str) -> bool:
        """Verifica se devemos aplicar rate limiting"""
        now = time.time()
        last_request = self.last_request_time.get(domain, 0)
        
        # Mínimo 3 segundos entre requests para mesmo domínio
        if now - last_request < 3:
            return True
            
        self.last_request_time[domain] = now
        return False


# Instância global para reutilização
stealth_scraper = StealthScraper()


def create_stealth_headers(domain: str = None) -> Dict[str, str]:
    """
    Cria headers com técnicas avançadas anti-detecção
    """
    fingerprint = stealth_scraper.generate_browser_fingerprint()
    
    # Headers base realistas
    headers = {
        'User-Agent': f"Mozilla/5.0 ({fingerprint['os']}) AppleWebKit/{fingerprint['engine']} (KHTML, like Gecko) Chrome/{fingerprint['browser']} Safari/{fingerprint['engine']}",
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': ','.join(fingerprint['languages'][:2]) + ';q=0.9,' + ','.join(fingerprint['languages'][2:]) + ';q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': random.choice(['none', 'same-origin', 'cross-site']),
        'Sec-Fetch-User': '?1',
        'Cache-Control': random.choice(['no-cache', 'max-age=0']),
    }
    
    # Headers específicos do Chrome
    if 'Chrome' in fingerprint['browser']:
        headers.update({
            'Sec-Ch-Ua': f'"Not_A Brand";v="8", "Chromium";v="{fingerprint["browser"].split("/")[1].split(".")[0]}", "Google Chrome";v="{fingerprint["browser"].split("/")[1].split(".")[0]}"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': f'"{fingerprint["os"].split(";")[0]}"',
            'Sec-Ch-Viewport-Width': str(fingerprint['screen']['width']),
        })
    
    # Referrer realista baseado no domínio
    if domain and random.random() > 0.3:  # 70% das vezes
        if 'mercadolivre' in domain:
            referrers = ['https://www.google.com.br/search?q=mercado+livre', 'https://www.google.com/']
        elif 'amazon' in domain:
            referrers = ['https://www.google.com.br/search?q=amazon+brasil', 'https://www.google.com/']
        else:
            referrers = ['https://www.google.com/', 'https://www.bing.com/']
        headers['Referer'] = random.choice(referrers)
    
    return headers


def setup_stealth_session() -> requests.Session:
    """
    Configura sessão com máxima evasão de detecção
    """
    session = requests.Session()
    
    # Configurar retry strategy mais conservadora
    retry_strategy = Retry(
        total=2,  # Menos tentativas para evitar suspeita
        backoff_factor=2,  # Backoff mais longo
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=1,  # Pool menor
        pool_maxsize=3
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Timeouts realistas
    session.timeout = (10, 30)
    
    return session
