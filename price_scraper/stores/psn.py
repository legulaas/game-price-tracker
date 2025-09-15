import logging
import re
from playwright.sync_api import sync_playwright
from typing import Dict, Optional

logger = logging.getLogger("price_scraper.psn")

class PSNScraper:
    """Scraper para a PlayStation Store"""
    
    def search_game(self, title: str) -> Optional[Dict]:
        """
        Busca um jogo na PlayStation Store pelo título
        
        Args:
            title: Título do jogo
            
        Returns:
            Dicionário com informações do jogo ou None se não encontrado
        """
        logger.info(f"Buscando jogo '{title}' na PlayStation Store")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Buscar o jogo na PSN
                encoded_title = title.replace(' ', '%20')
                search_url = f"https://store.playstation.com/pt-br/search/{encoded_title}"
                page.goto(search_url)
                
                # Esperar carregamento dos resultados
                page.wait_for_selector("li div div.psw-product-tile", timeout=10000)
                
                # Verificar se há resultados
                results = page.locator("li div div.psw-product-tile")
                if results.count() == 0:
                    logger.info(f"Nenhum resultado encontrado para '{title}' na PSN")
                    browser.close()
                    return None
                
                # Pegar o primeiro resultado
                first_result = results.first
                
                # Extrair título
                game_title_element = first_result.locator("li div div#psw-product-tile")
                game_title = game_title_element.inner_text() if game_title_element.count() > 0 else title
                
                # Extrair URL
                link_element = first_result.locator("a.psw-link")
                game_url = "https://store.playstation.com" + link_element.get_attribute("href")
                
                # Extrair preço
                price_element = first_result.locator("span.psw-m-r-3")
                
                if price_element.count() == 0:
                    logger.info(f"Preço não encontrado para '{game_title}' na PSN")
                    browser.close()
                    return None
                
                price_text = price_element.inner_text().strip()
                
                # Verificar se tem desconto
                discount_element = first_result.locator(".psw-c-t-discount")
                discount_percent = 0
                
                if discount_element.count() > 0:
                    discount_text = discount_element.inner_text().strip()
                    discount_match = re.search(r'(\d+)%', discount_text)
                    if discount_match:
                        discount_percent = int(discount_match.group(1))
                
                # Tratar o preço
                if "Grátis" in price_text or "Free" in price_text:
                    price = 0.0
                    currency = "BRL"
                else:
                    currency = "BRL"
                    # Remover R$ e converter para float
                    price_clean = price_text.replace("R$", "").strip().replace(",", ".")
                    try:
                        price = float(price_clean)
                    except ValueError:
                        logger.warning(f"Não foi possível converter o preço '{price_text}' para float")
                        price = 0.0
                
                browser.close()
                
                return {
                    "title": game_title,
                    "price": price,
                    "currency": currency,
                    "discount_percent": discount_percent,
                    "url": game_url
                }
                
        except Exception as e:
            logger.error(f"Erro ao buscar jogo na PSN: {str(e)}")
            return None