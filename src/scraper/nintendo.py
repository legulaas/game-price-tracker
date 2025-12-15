"""Nintendo eShop scraper for Brazilian region."""
import re
import logging
import asyncio
from typing import Dict, Any, List, Optional
from urllib.parse import quote
from .base import BaseScraper

logger = logging.getLogger(__name__)


class NintendoScraper(BaseScraper):
    """Scraper for Nintendo eShop (Brazil)."""

    BASE_URL = "https://www.nintendo.com/pt-br"
    SEARCH_URL = "https://www.nintendo.com/pt-br/search/#q="
    API_URL = "https://searching.nintendo.com/api/search"

    async def search_game(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for games on Nintendo eShop using API.

        Args:
            query: Game title to search

        Returns:
            List of game dictionaries
        """
        page = await self.create_page()
        results = []

        try:
            # Use Nintendo's search API
            api_url = f"{self.API_URL}/product?q={quote(query)}&locale=pt_BR&fq=type:game&start=0&rows=10"
            logger.info(f"Searching Nintendo eShop API: {api_url}")

            await page.goto(api_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(1)

            # Get JSON response
            content = await page.content()

            # Parse JSON from body
            import json
            try:
                # Extract JSON from <pre> tag (API returns JSON in pre tag)
                json_match = re.search(r'<pre[^>]*>(.*?)</pre>', content, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
                    data = json.loads(json_text)
                else:
                    # Try parsing directly
                    data = json.loads(content)

                logger.info(f"API returned {len(data.get('response', {}).get('docs', []))} results")

                # Parse products from API response
                for product in data.get('response', {}).get('docs', [])[:10]:
                    try:
                        title = product.get('title', '')
                        nsuid = product.get('nsuid_txt', [''])[0] if isinstance(product.get('nsuid_txt'), list) else product.get('nsuid_txt', '')
                        url_path = product.get('url', '')

                        if not title or not url_path:
                            continue

                        url = f"{self.BASE_URL}{url_path}"

                        # Get price from price_raw field
                        current_price = None
                        if 'price_regular_f' in product:
                            current_price = float(product['price_regular_f'])
                        elif 'price_lowest_f' in product:
                            current_price = float(product['price_lowest_f'])

                        # Get image
                        image_url = product.get('image_url', product.get('image_url_sq_s', ''))
                        if image_url and not image_url.startswith('http'):
                            image_url = f"https:{image_url}" if image_url.startswith('//') else f"https://assets.nintendo.com{image_url}"

                        logger.info(f"Found game: {title} - R$ {current_price if current_price else 'N/A'}")

                        results.append({
                            "title": title,
                            "url": url,
                            "platform": "Nintendo",
                            "current_price": current_price,
                            "image_url": image_url
                        })

                    except Exception as e:
                        logger.warning(f"Error parsing product: {e}")
                        continue

                logger.info(f"Found {len(results)} games on Nintendo eShop")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Response content: {content[:500]}")

        except Exception as e:
            logger.error(f"Error searching Nintendo eShop: {e}")
        finally:
            await page.close()

        return results

    async def get_game_details(self, url: str) -> Dict[str, Any]:
        """
        Get detailed information about a game from Nintendo eShop.

        Args:
            url: Nintendo eShop game page URL

        Returns:
            Dictionary with game details
        """
        page = await self.create_page()
        details = {}

        try:
            logger.info(f"Fetching Nintendo eShop details from: {url}")

            # Visit homepage first for human-like behavior
            await page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(1 + (asyncio.get_event_loop().time() % 1))

            # Now go to game page
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)

            # Wait for page content
            try:
                await page.wait_for_selector('h1, [data-testid*="title"], [class*="ProductHero"]', timeout=15000)
                await asyncio.sleep(2)

                # Scroll to load all content
                await page.evaluate("window.scrollTo(0, 500)")
                await asyncio.sleep(0.5)
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(0.5)
            except:
                logger.warning("Page elements took too long to load")

            # Get title
            title_selectors = ['h1', '[data-testid*="title"]', '[class*="ProductHero"] h1']
            title = "Unknown"
            for selector in title_selectors:
                title_elem = await page.query_selector(selector)
                if title_elem:
                    title = await title_elem.inner_text()
                    title = title.strip()
                    if title:
                        break

            logger.info(f"Found title: {title}")

            # Get price
            current_price = None
            original_price = None
            is_on_sale = False
            discount_percentage = 0

            # Try different price selectors
            price_selectors = [
                '[data-testid*="price"]',
                '[class*="price"]',
                'span:has-text("R$")',
                '[class*="ProductPrice"]'
            ]

            for selector in price_selectors:
                price_elements = await page.query_selector_all(selector)
                if price_elements:
                    for elem in price_elements:
                        price_text = await elem.inner_text()
                        if 'R$' in price_text:
                            logger.info(f"Found price text: {price_text}")
                            price = self._parse_price(price_text)
                            if price and price > 0:
                                if current_price is None:
                                    current_price = price
                                else:
                                    # Second price might be original price
                                    original_price = max(current_price, price)
                                    current_price = min(current_price, price)
                                    if original_price > current_price:
                                        is_on_sale = True

            # Check for strikethrough price (original price)
            strikethrough = await page.query_selector('s, del, [class*="strike"], [class*="original"]')
            if strikethrough:
                original_price_text = await strikethrough.inner_text()
                if 'R$' in original_price_text:
                    original_price = self._parse_price(original_price_text)
                    if original_price and original_price > (current_price or 0):
                        is_on_sale = True

            # Calculate discount
            if is_on_sale and original_price and current_price and original_price > 0:
                discount_percentage = int(((original_price - current_price) / original_price) * 100)

            if not is_on_sale and current_price:
                original_price = current_price

            # Get image
            image_url = None
            img_selectors = ['[class*="ProductHero"] img', 'img[alt*="cover"]', 'main img']
            for selector in img_selectors:
                img = await page.query_selector(selector)
                if img:
                    image_url = await img.get_attribute('src')
                    if image_url and 'nintendo' in image_url:
                        break

            # Get description
            description_selectors = [
                '[data-testid*="description"]',
                '[class*="description"]',
                'p[class*="ProductDescription"]',
                'section p'
            ]

            description = ""
            for selector in description_selectors:
                desc_elem = await page.query_selector(selector)
                if desc_elem:
                    desc = await desc_elem.inner_text()
                    if desc and len(desc) > 50:
                        description = desc.strip()
                        break

            details = {
                "title": title,
                "url": url,
                "platform": "Nintendo",
                "current_price": current_price,
                "original_price": original_price,
                "discount_percentage": discount_percentage,
                "is_on_sale": is_on_sale,
                "image_url": image_url,
                "description": description
            }

        except Exception as e:
            logger.error(f"Error getting Nintendo eShop details for {url}: {e}")
        finally:
            await page.close()

        return details

    @staticmethod
    def _parse_price(price_text: str) -> Optional[float]:
        """Parse price string to float (Brazilian format)."""
        if not price_text:
            return None

        # Check for free games
        if "Gratuito" in price_text or "Free" in price_text or "Grátis" in price_text:
            if "R$" not in price_text:
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

        logger.warning(f"Could not parse price: {price_text}")
        return None
