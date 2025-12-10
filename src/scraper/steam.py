"""Steam store scraper implementation."""
import re
import logging
from typing import List, Dict, Any
from urllib.parse import quote
from .base import BaseScraper

logger = logging.getLogger(__name__)


class SteamScraper(BaseScraper):
    """Scraper for Steam store."""

    BASE_URL = "https://store.steampowered.com"
    SEARCH_URL = f"{BASE_URL}/search/?term="

    # Default region (Brazil)
    REGION = "br"
    CURRENCY = "BRL"

    async def search_game(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for games on Steam.

        Args:
            query: Game title to search for

        Returns:
            List of game dictionaries
        """
        page = await self.create_page()
        results = []

        try:
            # Navigate to search page with Brazilian region
            search_url = f"{self.SEARCH_URL}{quote(query)}&cc={self.REGION}"
            await page.goto(search_url, wait_until="networkidle", timeout=30000)

            # Wait for search results
            await page.wait_for_selector("#search_resultsRows", timeout=10000)

            # Get all game entries
            games = await page.query_selector_all("#search_resultsRows > a")

            for game in games[:5]:  # Limit to top 5 results
                try:
                    # Get game title
                    title_element = await game.query_selector(".title")
                    title = await title_element.inner_text() if title_element else "Unknown"

                    # Get game URL
                    url = await game.get_attribute("href")
                    if url:
                        # Clean up URL (remove tracking parameters)
                        url = url.split("?")[0]

                    # Get price information
                    price_element = await game.query_selector(".discount_final_price")
                    original_price_element = await game.query_selector(".discount_original_price")

                    current_price = None
                    original_price = None
                    discount_percentage = 0
                    is_on_sale = False

                    if price_element:
                        price_text = await price_element.inner_text()
                        current_price = self._parse_price(price_text)

                    if original_price_element:
                        original_price_text = await original_price_element.inner_text()
                        original_price = self._parse_price(original_price_text)
                        is_on_sale = True

                        # Get discount percentage
                        discount_element = await game.query_selector(".discount_pct")
                        if discount_element:
                            discount_text = await discount_element.inner_text()
                            discount_percentage = self._parse_discount(discount_text)

                    if not is_on_sale and current_price:
                        original_price = current_price

                    # Get image URL
                    image_element = await game.query_selector("img")
                    image_url = await image_element.get_attribute("src") if image_element else None

                    results.append({
                        "title": title.strip(),
                        "url": url,
                        "platform": "Steam",
                        "current_price": current_price,
                        "original_price": original_price,
                        "discount_percentage": discount_percentage,
                        "is_on_sale": is_on_sale,
                        "image_url": image_url
                    })

                except Exception as e:
                    logger.warning(f"Error parsing game entry: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error searching Steam for '{query}': {e}")
        finally:
            await page.close()

        return results

    async def get_game_details(self, url: str) -> Dict[str, Any]:
        """
        Get detailed information about a game from its Steam page.

        Args:
            url: Steam game page URL

        Returns:
            Dictionary with game details
        """
        page = await self.create_page()
        details = {}

        try:
            # Add Brazilian region to URL if not present
            if "?" in url:
                url_with_region = f"{url}&cc={self.REGION}"
            else:
                url_with_region = f"{url}?cc={self.REGION}"

            await page.goto(url_with_region, wait_until="networkidle", timeout=30000)

            # Handle age gate if present
            age_check = await page.query_selector("#age_gate")
            if age_check:
                await page.click("#ageYear")
                await page.select_option("#ageYear", "1990")
                await page.click("#view_product_page_btn")
                await page.wait_for_load_state("networkidle")

            # Get game title
            title = await self.safe_get_text(page, "#appHubAppName", "Unknown")

            # Get price information
            price_element = await page.query_selector(".game_purchase_price, .discount_final_price")
            current_price = None
            if price_element:
                price_text = await price_element.inner_text()
                current_price = self._parse_price(price_text)

            original_price_element = await page.query_selector(".discount_original_price")
            original_price = None
            is_on_sale = False
            discount_percentage = 0

            if original_price_element:
                original_price_text = await original_price_element.inner_text()
                original_price = self._parse_price(original_price_text)
                is_on_sale = True

                discount_element = await page.query_selector(".discount_pct")
                if discount_element:
                    discount_text = await discount_element.inner_text()
                    discount_percentage = self._parse_discount(discount_text)

            if not is_on_sale and current_price:
                original_price = current_price

            # Get image
            image_url = await self.safe_get_attribute(page, ".game_header_image_full", "src")

            # Get description
            description = await self.safe_get_text(page, ".game_description_snippet")

            details = {
                "title": title.strip(),
                "url": url,
                "platform": "Steam",
                "current_price": current_price,
                "original_price": original_price,
                "discount_percentage": discount_percentage,
                "is_on_sale": is_on_sale,
                "image_url": image_url,
                "description": description.strip()
            }

        except Exception as e:
            logger.error(f"Error getting details for {url}: {e}")
        finally:
            await page.close()

        return details

    @staticmethod
    def _parse_price(price_text: str) -> float:
        """Parse price string to float."""
        # Remove currency symbols and extract number
        # Handles formats like: R$ 49,99 or $49.99 or Free
        if "Free" in price_text or "Gratuito" in price_text:
            return 0.0

        # Remove all non-numeric characters except comma and period
        price_clean = re.sub(r'[^\d.,]', '', price_text)

        # Handle different decimal separators
        if ',' in price_clean and '.' in price_clean:
            # Determine which is decimal separator (usually the last one)
            if price_clean.rindex(',') > price_clean.rindex('.'):
                price_clean = price_clean.replace('.', '').replace(',', '.')
            else:
                price_clean = price_clean.replace(',', '')
        elif ',' in price_clean:
            price_clean = price_clean.replace(',', '.')

        try:
            return float(price_clean)
        except ValueError:
            logger.warning(f"Could not parse price: {price_text}")
            return 0.0

    @staticmethod
    def _parse_discount(discount_text: str) -> int:
        """Parse discount percentage string to int."""
        # Extract number from strings like "-75%"
        match = re.search(r'(\d+)', discount_text)
        if match:
            return int(match.group(1))
        return 0
