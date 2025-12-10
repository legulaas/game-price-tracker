"""Service for managing user game tracking (wishlist)."""
import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.models import User, Game, TrackedGame

logger = logging.getLogger(__name__)


class TrackerService:
    """Service for tracking games on user wishlists."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the service.

        Args:
            session: Database session
        """
        self.session = session

    async def get_or_create_user(self, discord_id: str, username: str) -> Optional[User]:
        """
        Get existing user or create a new one.

        Args:
            discord_id: Discord user ID
            username: Discord username

        Returns:
            User instance or None
        """
        try:
            # Check if user exists
            result = await self.session.execute(
                select(User).where(User.discord_id == discord_id)
            )
            user = result.scalar_one_or_none()

            if user:
                # Update username if changed
                if user.username != username:
                    user.username = username
                    await self.session.commit()
                    await self.session.refresh(user)
                return user

            # Create new user
            new_user = User(discord_id=discord_id, username=username)
            self.session.add(new_user)
            await self.session.commit()
            await self.session.refresh(new_user)

            logger.info(f"Created new user: {username} ({discord_id})")
            return new_user

        except Exception as e:
            logger.error(f"Error getting/creating user: {e}")
            await self.session.rollback()
            return None

    async def add_tracked_game(
        self,
        discord_id: str,
        username: str,
        game_id: int,
        target_price: Optional[float] = None,
        notify_on_any_sale: bool = True
    ) -> Optional[TrackedGame]:
        """
        Add a game to user's tracking list.

        Args:
            discord_id: Discord user ID
            username: Discord username
            game_id: Game ID to track
            target_price: Optional target price for notifications
            notify_on_any_sale: Whether to notify on any sale

        Returns:
            TrackedGame instance or None
        """
        try:
            # Get or create user
            user = await self.get_or_create_user(discord_id, username)
            if not user:
                return None

            # Check if already tracking
            result = await self.session.execute(
                select(TrackedGame).where(
                    TrackedGame.user_id == user.id,
                    TrackedGame.game_id == game_id
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update settings
                existing.target_price = target_price
                existing.notify_on_any_sale = notify_on_any_sale
                await self.session.commit()
                await self.session.refresh(existing)
                logger.info(f"Updated tracked game for user {username}")
                return existing

            # Create new tracking entry
            tracked_game = TrackedGame(
                user_id=user.id,
                game_id=game_id,
                target_price=target_price,
                notify_on_any_sale=notify_on_any_sale
            )
            self.session.add(tracked_game)
            await self.session.commit()
            await self.session.refresh(tracked_game)

            logger.info(f"User {username} started tracking game ID {game_id}")
            return tracked_game

        except Exception as e:
            logger.error(f"Error adding tracked game: {e}")
            await self.session.rollback()
            return None

    async def remove_tracked_game(self, discord_id: str, game_id: int) -> bool:
        """
        Remove a game from user's tracking list.

        Args:
            discord_id: Discord user ID
            game_id: Game ID to stop tracking

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user
            result = await self.session.execute(
                select(User).where(User.discord_id == discord_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"User {discord_id} not found")
                return False

            # Find and delete tracked game
            result = await self.session.execute(
                select(TrackedGame).where(
                    TrackedGame.user_id == user.id,
                    TrackedGame.game_id == game_id
                )
            )
            tracked_game = result.scalar_one_or_none()

            if not tracked_game:
                logger.warning(f"User {discord_id} is not tracking game {game_id}")
                return False

            await self.session.delete(tracked_game)
            await self.session.commit()

            logger.info(f"User {discord_id} stopped tracking game {game_id}")
            return True

        except Exception as e:
            logger.error(f"Error removing tracked game: {e}")
            await self.session.rollback()
            return False

    async def get_user_tracked_games(self, discord_id: str) -> List[TrackedGame]:
        """
        Get all games tracked by a user.

        Args:
            discord_id: Discord user ID

        Returns:
            List of tracked games with game details
        """
        try:
            # Get user
            result = await self.session.execute(
                select(User).where(User.discord_id == discord_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                return []

            # Get tracked games with game details
            result = await self.session.execute(
                select(TrackedGame)
                .options(selectinload(TrackedGame.game))
                .where(TrackedGame.user_id == user.id)
            )
            tracked_games = list(result.scalars().all())

            return tracked_games

        except Exception as e:
            logger.error(f"Error getting user tracked games: {e}")
            return []

    async def get_all_tracked_games(self) -> List[TrackedGame]:
        """
        Get all tracked games across all users.

        Returns:
            List of all tracked games with user and game details
        """
        try:
            result = await self.session.execute(
                select(TrackedGame)
                .options(
                    selectinload(TrackedGame.user),
                    selectinload(TrackedGame.game)
                )
            )
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error getting all tracked games: {e}")
            return []
