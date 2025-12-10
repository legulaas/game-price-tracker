"""PlayStation Store scraper implementation."""
import re
import logging
import asyncio
from typing import List, Dict, Any
from urllib.parse import quote
from .base import BaseScraper

logger = logging.getLogger(__name__)


class PlayStationScraper(BaseScraper):
    """Scraper for PlayStation Store (Brazil)."""

    BASE_URL = "https://store.playstation.com"
    SEARCH_URL = f"{BASE_URL}/pt-br/search/"

    async def search_game(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for games on PlayStation Store using human-like interaction.

        Args:
            query: Game title to search for

        Returns:
            List of game dictionaries
        """
        page = await self.create_page()
        results = []

        try:
            # Navigate to PlayStation Store homepage (Brazil)
            logger.info("Navigating to PlayStation Store homepage...")
            await page.goto(f"{self.BASE_URL}/pt-br/", wait_until="domcontentloaded", timeout=45000)

            # Random delay to simulate human behavior
            await asyncio.sleep(1 + (asyncio.get_event_loop().time() % 2))

            # Wait for and click on search button
            try:
                search_button = await page.wait_for_selector('button[aria-label*="Pesquisar"], button[data-qa*="search"]', timeout=10000)
                if search_button:
                    logger.info("Clicking search button...")
                    await search_button.click()
                    await asyncio.sleep(0.5)
            except:
                logger.warning("Could not find search button, trying alternative method...")

            # Wait for search input field
            try:
                search_input = await page.wait_for_selector('input[type="text"], input[placeholder*="esquisar"]', timeout=10000)
                if search_input:
                    logger.info(f"Typing search query: {query}")

                    # Type slowly like a human
                    await search_input.click()
                    await asyncio.sleep(0.3)

                    for char in query:
                        await search_input.type(char)
                        await asyncio.sleep(0.05 + (asyncio.get_event_loop().time() % 0.1))

                    # Press Enter or click search
                    await search_input.press('Enter')
                    await asyncio.sleep(2)
                else:
                    raise Exception("Search input not found")
            except Exception as e:
                logger.warning(f"Could not interact with search: {e}. Falling back to direct URL...")
                # Fallback: navigate directly to search URL
                search_url = f"{self.SEARCH_URL}{quote(query)}"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)

            # Wait for search results to load
            try:
                await page.wait_for_selector('[data-qa="search-result"], .psw-product-tile', timeout=15000)
            except:
                logger.warning(f"No PlayStation Store results found for '{query}'")
                return results

            # Additional wait for dynamic content
            await asyncio.sleep(2)

            # Get all game entries - try multiple selectors
            games = await page.query_selector_all('[data-qa="search-result"]')
            if not games:
                games = await page.query_selector_all('.psw-product-tile')
            if not games:
                games = await page.query_selector_all('a[href*="/product/"]')

            for game in games[:5]:  # Limit to top 5 results
                try:
                    # Get game title
                    title_element = await game.query_selector('span[data-qa*="product"]')
                    title = await title_element.inner_text() if title_element else "Unknown"

                    # Get game URL
                    link_element = await game.query_selector('a')
                    url = None
                    if link_element:
                        url = await link_element.get_attribute("href")
                        if url and not url.startswith("http"):
                            url = f"{self.BASE_URL}{url}"

                    if not url:
                        continue

                    # Get price
                    current_price = None
                    original_price = None
                    is_on_sale = False
                    discount_percentage = 0

                    # Try to find price display
                    price_element = await game.query_selector('[data-qa*="price"]')
                    if price_element:
                        price_text = await price_element.inner_text()
                        current_price = self._parse_price(price_text)

                    # Check for discount/original price
                    strikethrough = await game.query_selector('s')
                    if strikethrough:
                        original_price_text = await strikethrough.inner_text()
                        original_price = self._parse_price(original_price_text)
                        is_on_sale = True

                        if original_price and current_price and original_price > 0:
                            discount_percentage = int(((original_price - current_price) / original_price) * 100)

                    if not is_on_sale and current_price:
                        original_price = current_price

                    # Get image
                    image_element = await game.query_selector('img')
                    image_url = await image_element.get_attribute("src") if image_element else None

                    results.append({
                        "title": title.strip(),
                        "url": url,
                        "platform": "PlayStation",
                        "current_price": current_price,
                        "original_price": original_price,
                        "discount_percentage": discount_percentage,
                        "is_on_sale": is_on_sale,
                        "image_url": image_url
                    })

                except Exception as e:
                    logger.warning(f"Error parsing PlayStation game entry: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error searching PlayStation Store for '{query}': {e}")
        finally:
            await page.close()

        return results

    async def get_game_details(self, url: str) -> Dict[str, Any]:
        """
        Get detailed information about a game from PlayStation Store.

        Args:
            url: PlayStation Store game page URL

        Returns:
            Dictionary with game details
        """
        page = await self.create_page()
        details = {}

        try:
            logger.info(f"Fetching PlayStation Store details from: {url}")

            # First visit homepage to appear more human-like
            logger.info("First visiting PlayStation Store homepage...")
            await page.goto(f"{self.BASE_URL}/pt-br/", wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(1.5 + (asyncio.get_event_loop().time() % 1))  # Random delay

            # Now navigate to the actual game page
            logger.info(f"Now navigating to game page: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)

            # Wait for page to load - try multiple selectors
            try:
                await page.wait_for_selector('h1, [data-qa*="product"]', timeout=15000)
                await asyncio.sleep(2)  # Wait for dynamic content

                # Simulate human scroll behavior
                await page.evaluate("window.scrollTo(0, 300)")
                await asyncio.sleep(0.5)
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(0.5)
            except:
                logger.warning("Page elements took too long to load, continuing anyway...")

            # Get title - try multiple selectors
            title = await self.safe_get_text(page, 'h1[data-qa*="product"], h1', "Unknown")
            logger.info(f"Found title: {title}")

            # Debug: Save screenshot if we got Access Denied
            if "Access Denied" in title or "access denied" in title.lower():
                screenshot_path = "logs/playstation_access_denied.png"
                await page.screenshot(path=screenshot_path)
                logger.error(f"Access Denied detected! Screenshot saved to {screenshot_path}")

                # Also log the page content
                content = await page.content()
                with open("logs/playstation_page_content.html", "w", encoding="utf-8") as f:
                    f.write(content)
                logger.error("Page HTML content saved to logs/playstation_page_content.html")

            # Get price - try multiple selectors
            current_price = None
            original_price = None
            is_on_sale = False
            discount_percentage = 0

            # Try different price selectors
            price_selectors = [
                '[data-qa*="price-display"]',
                '[data-qa*="mfeCtaMain"] span',
                'span[data-qa*="price"]',
                '.psw-t-title-m'
            ]

            price_text = None
            for selector in price_selectors:
                price_element = await page.query_selector(selector)
                if price_element:
                    price_text = await price_element.inner_text()
                    logger.info(f"Found price text with selector {selector}: {price_text}")
                    if 'R$' in price_text:
                        break

            if price_text:
                current_price = self._parse_price(price_text)
                logger.info(f"Parsed current price: R$ {current_price}")

            # Check for original price (strikethrough)
            strikethrough_selectors = ['s', '.psw-t-strikethrough', '[data-qa*="original"]']
            for selector in strikethrough_selectors:
                strikethrough = await page.query_selector(selector)
                if strikethrough:
                    original_price_text = await strikethrough.inner_text()
                    logger.info(f"Found original price: {original_price_text}")
                    original_price = self._parse_price(original_price_text)
                    if original_price > 0:
                        is_on_sale = True
                        break

            if is_on_sale and original_price and current_price and original_price > 0:
                discount_percentage = int(((original_price - current_price) / original_price) * 100)

            if not is_on_sale and current_price:
                original_price = current_price

            # Get image
            image_url = await self.safe_get_attribute(page, 'img[src*="image.api.playstation"], img[data-qa*="product"]', "src")

            # Get description
            description = await self.safe_get_text(page, '[data-qa*="description"], p')

            details = {
                "title": title.strip(),
                "url": url,
                "platform": "PlayStation",
                "current_price": current_price,
                "original_price": original_price,
                "discount_percentage": discount_percentage,
                "is_on_sale": is_on_sale,
                "image_url": image_url,
                "description": description.strip() if description else ""
            }

        except Exception as e:
            logger.error(f"Error getting PlayStation Store details for {url}: {e}")
        finally:
            await page.close()

        return details

    @staticmethod
    def _parse_price(price_text: str) -> float:
        """Parse price string to float (Brazilian format)."""
        if "Gratuito" in price_text or "Free" in price_text or "Grátis" in price_text or "Incluído" in price_text:
            return 0.0

        # Try to extract first price pattern (R$ XX,XX or R$XX,XX)
        price_pattern = r'R\$\s*(\d+(?:\.\d{3})*,\d{2})'
        matches = re.findall(price_pattern, price_text)

        if matches:
            # Use the first price found (usually the current/sale price)
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

        logger.warning(f"Could not parse price: {price_text}")
        return 0.0
