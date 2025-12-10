"""Scraper factory for creating platform-specific scrapers."""
import os
from typing import Optional
from .base import BaseScraper
from .steam import SteamScraper
from .playstation import PlayStationScraper


class ScraperFactory:
    """Factory for creating platform-specific scrapers."""

    _scrapers = {
        "steam": SteamScraper,
        "playstation": PlayStationScraper,
        "psn": PlayStationScraper,  # Alias
        "ps": PlayStationScraper,   # Alias
        # Add more platforms here in the future
        # "epic": EpicScraper,
        # "gog": GOGScraper,
    }

    # Main platforms (without aliases) for display
    _main_platforms = ["steam", "playstation"]

    @classmethod
    def create(cls, platform: str, headless: Optional[bool] = None) -> BaseScraper:
        """
        Create a scraper instance for the specified platform.

        Args:
            platform: Platform name (e.g., "steam", "epic")
            headless: Whether to run browser in headless mode (defaults to env var)

        Returns:
            Platform-specific scraper instance

        Raises:
            ValueError: If platform is not supported
        """
        platform = platform.lower()

        if platform not in cls._scrapers:
            raise ValueError(
                f"Platform '{platform}' not supported. "
                f"Available platforms: {', '.join(cls._scrapers.keys())}"
            )

        # Get headless setting from environment if not specified
        if headless is None:
            headless = os.getenv("HEADLESS", "true").lower() == "true"

        scraper_class = cls._scrapers[platform]
        return scraper_class(headless=headless)

    @classmethod
    def get_supported_platforms(cls) -> list:
        """Get list of supported platforms (without aliases)."""
        return cls._main_platforms
