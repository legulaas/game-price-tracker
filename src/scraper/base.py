"""Base scraper class with common functionality."""
import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page, Playwright

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for web scrapers."""

    def __init__(self, headless: bool = True):
        """
        Initialize the scraper.

        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self):
        """Start the browser with stealth settings."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security'
            ]
        )
        logger.info("Browser started successfully")

    async def close(self):
        """Close the browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")

    async def create_page(self) -> Page:
        """Create a new page with stealth settings."""
        if not self.browser:
            raise RuntimeError("Browser not started. Call start() first.")

        # Create context with viewport and timezone
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='pt-BR',
            timezone_id='America/Sao_Paulo',
            permissions=['geolocation'],
            geolocation={'latitude': -23.5505, 'longitude': -46.6333}  # São Paulo
        )

        page = await context.new_page()

        # Set realistic headers
        await page.set_extra_http_headers({
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })

        # Enhanced stealth script
        await page.add_init_script("""
            // Webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Chrome property
            window.chrome = {
                runtime: {}
            };

            // Permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Modernizr.notification ? 'granted' : 'prompt' }) :
                    originalQuery(parameters)
            );

            // Plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    }
                ]
            });

            // Languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-BR', 'pt', 'en-US', 'en']
            });

            // Platform
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });

            // Hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });

            // Device memory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
        """)

        return page

    @abstractmethod
    async def search_game(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for games by query.

        Args:
            query: Search query string

        Returns:
            List of game dictionaries with title, url, price, etc.
        """
        pass

    @abstractmethod
    async def get_game_details(self, url: str) -> Dict[str, Any]:
        """
        Get detailed information about a game.

        Args:
            url: Game page URL

        Returns:
            Dictionary with game details
        """
        pass

    async def safe_get_text(self, page: Page, selector: str, default: str = "") -> str:
        """Safely get text from an element."""
        try:
            element = await page.query_selector(selector)
            if element:
                text = await element.inner_text()
                return text.strip()
        except Exception as e:
            logger.debug(f"Could not get text from selector {selector}: {e}")
        return default

    async def safe_get_attribute(self, page: Page, selector: str, attribute: str, default: str = "") -> str:
        """Safely get attribute from an element."""
        try:
            element = await page.query_selector(selector)
            if element:
                value = await element.get_attribute(attribute)
                return value if value else default
        except Exception as e:
            logger.debug(f"Could not get attribute {attribute} from selector {selector}: {e}")
        return default
