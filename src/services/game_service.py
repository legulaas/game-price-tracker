"""Service for managing games and price tracking."""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Game, PriceHistory
from ..scraper.factory import ScraperFactory

logger = logging.getLogger(__name__)


class GameService:
    """Service for game-related operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the service.

        Args:
            session: Database session
        """
        self.session = session

    async def search_games(self, query: str, platform: str = "steam") -> List[Dict[str, Any]]:
        """
        Search for games on a platform.

        Args:
            query: Search query
            platform: Platform to search on

        Returns:
            List of game dictionaries
        """
        try:
            async with ScraperFactory.create(platform) as scraper:
                results = await scraper.search_game(query)
                logger.info(f"Found {len(results)} games for query '{query}' on {platform}")
                return results
        except Exception as e:
            logger.error(f"Error searching games: {e}")
            return []

    async def get_or_create_game(self, game_data: Dict[str, Any]) -> Optional[Game]:
        """
        Get existing game from database or create a new one.

        Args:
            game_data: Dictionary with game information

        Returns:
            Game instance or None if error
        """
        try:
            # Check if game already exists by URL
            result = await self.session.execute(
                select(Game).where(Game.url == game_data["url"])
            )
            existing_game = result.scalar_one_or_none()

            if existing_game:
                # Update price if changed
                if existing_game.current_price != game_data.get("current_price"):
                    await self._add_price_history(existing_game.id, existing_game.current_price)
                    existing_game.current_price = game_data.get("current_price")
                    existing_game.original_price = game_data.get("original_price")
                    existing_game.discount_percentage = game_data.get("discount_percentage", 0)
                    existing_game.is_on_sale = game_data.get("is_on_sale", False)
                    existing_game.last_checked = datetime.utcnow()
                    await self.session.commit()
                    await self.session.refresh(existing_game)
                    logger.info(f"Updated game: {existing_game.title}")

                return existing_game

            # Create new game
            new_game = Game(
                title=game_data["title"],
                url=game_data["url"],
                platform=game_data["platform"],
                current_price=game_data.get("current_price"),
                original_price=game_data.get("original_price"),
                discount_percentage=game_data.get("discount_percentage", 0),
                is_on_sale=game_data.get("is_on_sale", False),
                image_url=game_data.get("image_url"),
                description=game_data.get("description"),
                last_checked=datetime.utcnow()
            )

            self.session.add(new_game)
            await self.session.commit()
            await self.session.refresh(new_game)

            # Add initial price history
            if new_game.current_price is not None:
                await self._add_price_history(new_game.id, new_game.current_price)

            logger.info(f"Created new game: {new_game.title}")
            return new_game

        except Exception as e:
            logger.error(f"Error getting/creating game: {e}")
            await self.session.rollback()
            return None

    async def update_game_price(self, game_id: int, platform: str = None) -> Optional[Game]:
        """
        Update game price by scraping its page.

        Args:
            game_id: Game ID
            platform: Platform name (optional, will use game's platform if not provided)

        Returns:
            Updated game or None
        """
        try:
            # Get game from database
            result = await self.session.execute(
                select(Game).where(Game.id == game_id)
            )
            game = result.scalar_one_or_none()

            if not game:
                logger.warning(f"Game with ID {game_id} not found")
                return None

            platform = platform or game.platform

            # Scrape updated data
            async with ScraperFactory.create(platform) as scraper:
                game_data = await scraper.get_game_details(game.url)

            if not game_data:
                logger.warning(f"Could not fetch updated data for game {game_id}")
                return game

            # Check if price changed
            if game.current_price != game_data.get("current_price"):
                await self._add_price_history(game.id, game.current_price)

            # Update game data
            game.current_price = game_data.get("current_price")
            game.original_price = game_data.get("original_price")
            game.discount_percentage = game_data.get("discount_percentage", 0)
            game.is_on_sale = game_data.get("is_on_sale", False)
            game.last_checked = datetime.utcnow()

            if game_data.get("image_url"):
                game.image_url = game_data["image_url"]
            if game_data.get("description"):
                game.description = game_data["description"]

            await self.session.commit()
            await self.session.refresh(game)

            logger.info(f"Updated game price: {game.title} - {game.current_price}")
            return game

        except Exception as e:
            logger.error(f"Error updating game price: {e}")
            await self.session.rollback()
            return None

    async def _add_price_history(self, game_id: int, price: float):
        """Add price to history."""
        try:
            price_history = PriceHistory(
                game_id=game_id,
                price=price,
                recorded_at=datetime.utcnow()
            )
            self.session.add(price_history)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error adding price history: {e}")
            await self.session.rollback()

    async def get_game_price_history(self, game_id: int, limit: int = 30) -> List[PriceHistory]:
        """
        Get price history for a game.

        Args:
            game_id: Game ID
            limit: Maximum number of records to return

        Returns:
            List of price history records
        """
        try:
            result = await self.session.execute(
                select(PriceHistory)
                .where(PriceHistory.game_id == game_id)
                .order_by(PriceHistory.recorded_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting price history: {e}")
            return []
