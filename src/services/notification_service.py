"""Service for sending notifications to users."""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import TrackedGame, Notification, Game

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing and sending notifications."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the service.

        Args:
            session: Database session
        """
        self.session = session

    async def should_notify(
        self,
        tracked_game: TrackedGame,
        notification_type: str = "price_drop"
    ) -> bool:
        """
        Check if user should be notified about a game.

        Args:
            tracked_game: TrackedGame instance
            notification_type: Type of notification

        Returns:
            True if should notify, False otherwise
        """
        try:
            game = tracked_game.game

            # Don't notify if no price available
            if game.current_price is None:
                return False

            # Check notification cooldown (don't spam - max once per day)
            if tracked_game.last_notified:
                time_since_last = datetime.utcnow() - tracked_game.last_notified
                if time_since_last < timedelta(hours=24):
                    return False

            # Check if game meets notification criteria
            if tracked_game.target_price is not None:
                # Notify if price is at or below target
                if game.current_price <= tracked_game.target_price:
                    return True

            if tracked_game.notify_on_any_sale and game.is_on_sale:
                # Notify on any sale
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking notification criteria: {e}")
            return False

    async def log_notification(
        self,
        user_id: int,
        game_id: int,
        notification_type: str,
        message: str
    ) -> Optional[Notification]:
        """
        Log a sent notification.

        Args:
            user_id: User ID
            game_id: Game ID
            notification_type: Type of notification
            message: Notification message

        Returns:
            Notification instance or None
        """
        try:
            notification = Notification(
                user_id=user_id,
                game_id=game_id,
                notification_type=notification_type,
                message=message,
                sent_at=datetime.utcnow()
            )

            self.session.add(notification)
            await self.session.commit()
            await self.session.refresh(notification)

            logger.info(f"Logged notification for user {user_id}, game {game_id}")
            return notification

        except Exception as e:
            logger.error(f"Error logging notification: {e}")
            await self.session.rollback()
            return None

    async def mark_notified(self, tracked_game: TrackedGame):
        """
        Mark a tracked game as notified.

        Args:
            tracked_game: TrackedGame instance
        """
        try:
            tracked_game.last_notified = datetime.utcnow()
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error marking as notified: {e}")
            await self.session.rollback()

    def format_price_notification(self, tracked_game: TrackedGame) -> str:
        """
        Format a price notification message.

        Args:
            tracked_game: TrackedGame instance

        Returns:
            Formatted notification message
        """
        game = tracked_game.game

        message_parts = [
            f"**{game.title}** está em promoção!",
            f"Plataforma: {game.platform}",
            f"Preço Atual: R$ {game.current_price:.2f}"
        ]

        if game.original_price and game.original_price != game.current_price:
            message_parts.append(f"Preço Original: R$ {game.original_price:.2f}")
            message_parts.append(f"Desconto: {game.discount_percentage}% OFF")

        if tracked_game.target_price:
            message_parts.append(f"Seu Preço Alvo: R$ {tracked_game.target_price:.2f}")

        message_parts.append(f"\nLink: {game.url}")

        return "\n".join(message_parts)

    async def get_notification_history(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[Notification]:
        """
        Get notification history for a user.

        Args:
            user_id: User ID
            limit: Maximum number of notifications to return

        Returns:
            List of notifications
        """
        try:
            result = await self.session.execute(
                select(Notification)
                .where(Notification.user_id == user_id)
                .order_by(Notification.sent_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error getting notification history: {e}")
            return []
