import logging
from playwright.sync_api import sync_playwright
from typing import Dict, Optional
import re
import random
import time

logger = logging.getLogger("price_scraper.steam")

class SteamScraper:
    """Scraper para a loja Steam"""
    
    def search_game(self, title: str) -> Optional[Dict]:
        logger.info(f"Buscando jogo '{title}' no SteamDB de forma mais natural")
        try:
            with sync_playwright() as p:
                # 1. EXECUTAR COM NAVEGADOR VISÍVEL (MUITO IMPORTANTE)
                browser = p.chromium.launch(headless=False, slow_mo=50) # slow_mo adiciona um pequeno delay a cada ação

                # 2. USAR UM USER-AGENT REAL E DEFINIR VIEWPORT
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()
                
                encoded_title = title.replace(' ', '+')
                import os
                # Diretório absoluto para screenshots
                screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                search_url = f"https://steamdb.info/search/?a=all&q={encoded_title}"
                
                logger.info("Navegando para a página de busca...")
                page.goto(search_url)

                # 3. ADICIONAR PAUSA PARA SIMULAR LEITURA
                time.sleep(random.uniform(2, 4))

                try:
                    # Usar um timeout maior, pois a navegação "humana" é mais lenta
                    page.wait_for_selector("#search-results .table", timeout=30000)
                    rows = page.locator("#search-results .table tbody tr")
                except Exception as e:
                     logger.error(f"Não foi possível encontrar a tabela de resultados, mesmo com a abordagem natural. Provavelmente um CAPTCHA. Erro: {e}")
                     page.screenshot(path="./screenshots/steamdb_captcha_error.png")
                     browser.close()
                     return None
                
                if rows.count() == 0:
                    logger.info(f"Nenhum resultado encontrado para '{title}' no SteamDB")
                    browser.close()
                    return None
                
                first_row = rows.nth(0)
                game_link_element = first_row.locator("td").nth(2).locator("a")
                
                # 4. SIMULAR MOVIMENTO DO MOUSE ANTES DA AÇÃO
                logger.info("Simulando mouse sobre o primeiro resultado...")
                game_link_element.hover()
                time.sleep(random.uniform(0.5, 1.5)) # Pausa antes de "decidir" pegar o link
                
                game_url = game_link_element.get_attribute("href")
                if not game_url.startswith("http"):
                    game_url = f"https://steamdb.info{game_url}"
                game_title = game_link_element.inner_text()
                
                logger.info(f"Navegando para a página do jogo: {game_title}")
                page.goto(game_url)

                # Pausa mais longa para a página do jogo carregar e parecer natural
                time.sleep(random.uniform(3, 5))

                # O restante da lógica permanece o mesmo, pois já é robusta
                price_row = page.locator("tr:has-text('Price')")
                if price_row.count() == 0:
                    # ... (resto do código igual ao anterior)
                    pass

                # ... (cole o restante do seu código de extração de preço aqui)

                logger.info("Extração concluída com sucesso!")
                browser.close()
                # ... (return { ... })
                # O restante do código de extração e retorno pode ser mantido como na versão anterior.
                # Apenas o trecho de navegação foi modificado.
                return {} # Placeholder para o dicionário de retorno

        except Exception as e:
            logger.error(f"Erro inesperado durante a busca natural no SteamDB: {str(e)}")
            return None