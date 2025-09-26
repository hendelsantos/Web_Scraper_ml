#!/usr/bin/env python3
"""
🌐 Proxy Rotator Avançado para Railway
Implementa rotação de proxies públicos para evitar bloqueios
"""

import requests
import random
import time
from typing import List, Dict, Optional
import json


class ProxyRotator:
    """Gerenciador avançado de proxies para Railway"""
    
    def __init__(self):
        self.working_proxies = []
        self.failed_proxies = []
        self.current_index = 0
        self.last_refresh = 0
        self.refresh_interval = 3600  # 1 hora
        
    def get_free_proxies(self) -> List[Dict]:
        """Obtém lista de proxies gratuitos de várias fontes"""
        proxies = []
        
        # Fonte 1: ProxyScrape
        try:
            response = requests.get(
                "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
                timeout=10
            )
            if response.status_code == 200:
                proxy_list = response.text.strip().split('\n')
                for proxy in proxy_list[:50]:  # Limitar a 50
                    if ':' in proxy:
                        ip, port = proxy.strip().split(':')
                        proxies.append({
                            'ip': ip,
                            'port': int(port),
                            'protocol': 'http',
                            'source': 'proxyscrape'
                        })
        except Exception:
            pass
            
        # Fonte 2: Free-Proxy-List
        try:
            response = requests.get(
                "https://www.proxy-list.download/api/v1/get?type=http&anon=elite&country=BR,US,CA",
                timeout=10
            )
            if response.status_code == 200:
                proxy_list = response.text.strip().split('\n')
                for proxy in proxy_list[:30]:
                    if ':' in proxy:
                        ip, port = proxy.strip().split(':')
                        proxies.append({
                            'ip': ip,
                            'port': int(port),
                            'protocol': 'http',
                            'source': 'proxy-list'
                        })
        except Exception:
            pass
            
        # Proxies fixos conhecidos (backup)
        backup_proxies = [
            {'ip': '8.210.83.33', 'port': 80, 'protocol': 'http', 'source': 'backup'},
            {'ip': '91.107.208.99', 'port': 8080, 'protocol': 'http', 'source': 'backup'},
            {'ip': '103.149.162.194', 'port': 80, 'protocol': 'http', 'source': 'backup'},
        ]
        proxies.extend(backup_proxies)
        
        return proxies
    
    def test_proxy(self, proxy: Dict) -> bool:
        """Testa se um proxy está funcionando"""
        try:
            proxy_url = f"http://{proxy['ip']}:{proxy['port']}"
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            # Teste simples
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                timeout=5
            )
            
            if response.status_code == 200:
                # Teste com site real
                response = requests.get(
                    'https://www.mercadolivre.com.br',
                    proxies=proxies,
                    timeout=10,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                return response.status_code == 200
                
        except Exception:
            pass
        return False
    
    def refresh_proxy_list(self):
        """Atualiza lista de proxies funcionais"""
        print("🔄 Atualizando lista de proxies...")
        
        # Obter novos proxies
        all_proxies = self.get_free_proxies()
        random.shuffle(all_proxies)
        
        # Testar proxies (apenas primeiros 20 para não demorar)
        working = []
        for proxy in all_proxies[:20]:
            print(f"🧪 Testando {proxy['ip']}:{proxy['port']}...")
            if self.test_proxy(proxy):
                working.append(proxy)
                print(f"✅ Proxy funcionando: {proxy['ip']}:{proxy['port']}")
            else:
                print(f"❌ Proxy falhou: {proxy['ip']}:{proxy['port']}")
                
            # Não testar mais que 10 ao mesmo tempo
            if len(working) >= 10:
                break
        
        self.working_proxies = working
        self.current_index = 0
        self.last_refresh = time.time()
        
        print(f"✅ {len(working)} proxies funcionais encontrados")
        
    def get_next_proxy(self) -> Optional[Dict]:
        """Obtém próximo proxy da rotação"""
        # Atualizar lista se necessário
        if (time.time() - self.last_refresh) > self.refresh_interval or not self.working_proxies:
            self.refresh_proxy_list()
            
        if not self.working_proxies:
            return None
            
        proxy = self.working_proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.working_proxies)
        
        return proxy
    
    def mark_proxy_failed(self, proxy: Dict):
        """Marca proxy como falho e remove da lista"""
        if proxy in self.working_proxies:
            self.working_proxies.remove(proxy)
            self.failed_proxies.append(proxy)
            print(f"❌ Proxy removido: {proxy['ip']}:{proxy['port']}")


# Instância global
proxy_rotator = ProxyRotator()


def get_proxy_session() -> requests.Session:
    """Cria sessão com proxy rotativo"""
    session = requests.Session()
    
    proxy = proxy_rotator.get_next_proxy()
    if proxy:
        proxy_url = f"http://{proxy['ip']}:{proxy['port']}"
        session.proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        print(f"🌐 Usando proxy: {proxy['ip']}:{proxy['port']}")
    else:
        print("⚠️ Nenhum proxy disponível, usando conexão direta")
    
    # Configurações de timeout
    session.timeout = (10, 30)
    
    return session


if __name__ == "__main__":
    # Teste
    rotator = ProxyRotator()
    rotator.refresh_proxy_list()
    
    for i in range(3):
        proxy = rotator.get_next_proxy()
        if proxy:
            print(f"Proxy {i+1}: {proxy['ip']}:{proxy['port']}")
        else:
            print(f"Proxy {i+1}: Nenhum disponível")
