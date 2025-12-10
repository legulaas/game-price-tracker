"""PSPrices scraper for price history."""
import re
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from .base import BaseScraper

logger = logging.getLogger(__name__)


class PSPricesScraper(BaseScraper):
    """Scraper for PSPrices.com to get price history."""

    BASE_URL = "https://psprices.com"

    async def search_game(self, query: str) -> list:
        """Not implemented - PSPrices is only for price history."""
        return []

    async def get_game_details(self, url: str) -> Dict[str, Any]:
        """Not implemented - PSPrices is only for price history."""
        return {}

    async def get_price_history(self, game_title: str, platform: str = "playstation") -> Dict[str, Any]:
        """
        Get price history for a game from PSPrices.

        Args:
            game_title: Game title to search for
            platform: Platform (playstation, steam, etc)

        Returns:
            Dictionary with lowest_price, lowest_price_date, and price history
        """
        page = await self.create_page()
        result = {
            "lowest_price": None,
            "lowest_price_date": None,
            "price_history": []
        }

        try:
            # Navigate to PSPrices homepage
            logger.info("Navigating to PSPrices homepage...")
            await page.goto(f"{self.BASE_URL}/region-br/index", wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(1 + (asyncio.get_event_loop().time() % 1))

            # Search for the game
            logger.info(f"Searching for game: {game_title}")

            # Try to find search input
            try:
                search_input = await page.wait_for_selector('input[type="search"], input[name="q"], input[placeholder*="Search"]', timeout=10000)
                if search_input:
                    await search_input.click()
                    await asyncio.sleep(0.3)

                    # Type game title slowly
                    for char in game_title:
                        await search_input.type(char)
                        await asyncio.sleep(0.05 + (asyncio.get_event_loop().time() % 0.1))

                    await search_input.press('Enter')
                    await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Could not use search input: {e}. Trying direct URL...")
                # Fallback: try direct search URL
                search_url = f"{self.BASE_URL}/region-br/search/?q={game_title.replace(' ', '+')}"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
                await asyncio.sleep(2)

            # Wait for search results
            try:
                await page.wait_for_selector('.game-collection-item, .game-item, a[href*="/game/"]', timeout=10000)
            except:
                logger.warning(f"No results found for '{game_title}' on PSPrices")
                return result

            # Click on first result
            try:
                first_result = await page.query_selector('.game-collection-item a, .game-item a, a[href*="/game/"]')
                if first_result:
                    await first_result.click()
                    await asyncio.sleep(2)

                    # Simulate human scroll
                    await page.evaluate("window.scrollTo(0, 500)")
                    await asyncio.sleep(0.5)
                else:
                    logger.warning("Could not find first result link")
                    return result
            except Exception as e:
                logger.warning(f"Could not click on first result: {e}")
                return result

            # Wait for price history chart/data
            try:
                await page.wait_for_selector('.chart, .price-history, canvas, [data-chart]', timeout=10000)
                await asyncio.sleep(2)
            except:
                logger.warning("Price history section not found")

            # Try to find lowest price information
            # PSPrices usually shows historical low in the page
            price_texts = await page.query_selector_all('.price, .historical-low, .lowest, [class*="price"], [class*="low"]')

            prices_found = []
            for price_elem in price_texts:
                try:
                    text = await price_elem.inner_text()
                    if 'R$' in text or 'lowest' in text.lower() or 'histórico' in text.lower():
                        logger.info(f"Found price text: {text}")
                        price = self._parse_price(text)
                        if price and price > 0:
                            prices_found.append(price)
                except:
                    continue

            # Get the minimum price found
            if prices_found:
                result["lowest_price"] = min(prices_found)
                result["lowest_price_date"] = datetime.now()  # PSPrices doesn't always show exact date
                logger.info(f"Found lowest price: R$ {result['lowest_price']:.2f}")

            # Try to get specific "historical low" if available
            historical_low_selectors = [
                '[class*="historical-low"]',
                '[class*="lowest"]',
                'text=/histórico/i',
                'text=/all time low/i'
            ]

            for selector in historical_low_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        price = self._parse_price(text)
                        if price and price > 0:
                            result["lowest_price"] = price
                            logger.info(f"Found historical low: R$ {price:.2f}")
                            break
                except:
                    continue

        except Exception as e:
            logger.error(f"Error fetching price history from PSPrices for '{game_title}': {e}")
        finally:
            await page.close()

        return result

    @staticmethod
    def _parse_price(price_text: str) -> Optional[float]:
        """Parse price string to float (Brazilian format)."""
        if not price_text:
            return None

        if "Gratuito" in price_text or "Free" in price_text or "Grátis" in price_text:
            return 0.0

        # Try to extract price pattern (R$ XX,XX or R$XX,XX)
        price_pattern = r'R\$\s*(\d+(?:\.\d{3})*,\d{2})'
        matches = re.findall(price_pattern, price_text)

        if matches:
            price_clean = matches[0]
        else:
            # Fallback: remove all non-numeric except comma and period
            price_clean = re.sub(r'[^\d.,]', '', price_text)

        # Handle Brazilian format: 199,90 or 1.199,90
        if price_clean:
            # Remove thousand separators (.) and replace comma with period
            price_clean = price_clean.replace('.', '').replace(',', '.')

            try:
                return float(price_clean)
            except ValueError:
                pass

        return None
