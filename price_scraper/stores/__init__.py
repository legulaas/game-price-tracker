from typing import Dict, Optional, Any
from price_scraper.stores.steam import SteamScraper
from price_scraper.stores.psn import PSNScraper

# Dicionário de scrapers disponíveis
SCRAPERS = {
    'steam': SteamScraper(),
    'psn': PSNScraper(),
    # Adicionar mais conforme necessário
}

def get_store_scraper(store_name: str):
    """Retorna o scraper adequado para a loja especificada"""
    store_name = store_name.lower()
    return SCRAPERS.get(store_name)