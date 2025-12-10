"""Scheduler for daily price checks and notifications."""
import os
import logging
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .database.config import AsyncSessionLocal
from .services.game_service import GameService
from .services.tracker_service import TrackerService
from .services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class PriceCheckScheduler:
    """Scheduler for automated price checking and notifications."""

    def __init__(self, bot):
        """
        Initialize the scheduler.

        Args:
            bot: Discord bot instance
        """
        self.bot = bot
        self.scheduler = AsyncIOScheduler()

        # Get schedule from environment variables
        self.hour = int(os.getenv("NOTIFICATION_HOUR", "15"))
        self.minute = int(os.getenv("NOTIFICATION_MINUTE", "0"))

    def start(self):
        """Start the scheduler."""
        # Schedule daily price check
        self.scheduler.add_job(
            self.daily_price_check,
            trigger=CronTrigger(hour=self.hour, minute=self.minute),
            id="daily_price_check",
            name="Daily Price Check and Notifications",
            replace_existing=True
        )

        self.scheduler.start()
        logger.info(f"Scheduler started. Daily price check scheduled at {self.hour:02d}:{self.minute:02d}")

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    async def daily_price_check(self):
        """
        Daily job to check prices and send notifications.

        This runs at the configured time each day.
        """
        logger.info("Starting daily price check...")

        try:
            async with AsyncSessionLocal() as session:
                tracker_service = TrackerService(session)
                game_service = GameService(session)
                notification_service = NotificationService(session)

                # Get all tracked games
                tracked_games = await tracker_service.get_all_tracked_games()

                logger.info(f"Checking {len(tracked_games)} tracked games")

                notifications_sent = 0

                for tracked_game in tracked_games:
                    try:
                        # Update game price
                        await game_service.update_game_price(
                            tracked_game.game_id,
                            platform=tracked_game.game.platform
                        )

                        # Refresh the tracked_game to get updated game data
                        await session.refresh(tracked_game)

                        # Check if notification should be sent
                        should_notify = await notification_service.should_notify(tracked_game)

                        if should_notify:
                            # Format notification message
                            message = notification_service.format_price_notification(tracked_game)

                            # Send Discord DM to user
                            try:
                                user = await self.bot.fetch_user(int(tracked_game.user.discord_id))
                                await user.send(message)

                                # Log notification
                                await notification_service.log_notification(
                                    user_id=tracked_game.user.id,
                                    game_id=tracked_game.game.id,
                                    notification_type="price_drop",
                                    message=message
                                )

                                # Mark as notified
                                await notification_service.mark_notified(tracked_game)

                                notifications_sent += 1
                                logger.info(f"Sent notification to {tracked_game.user.username} for {tracked_game.game.title}")

                            except Exception as e:
                                logger.error(f"Error sending DM to user {tracked_game.user.discord_id}: {e}")

                        # Small delay to avoid rate limiting
                        await asyncio.sleep(1)

                    except Exception as e:
                        logger.error(f"Error processing tracked game {tracked_game.id}: {e}")
                        continue

                logger.info(f"Daily price check completed. Sent {notifications_sent} notifications.")

        except Exception as e:
            logger.error(f"Error in daily price check: {e}")

    async def manual_price_check(self):
        """
        Manually trigger a price check (for testing).

        Can be called from a Discord command.
        """
        logger.info("Manual price check triggered")
        await self.daily_price_check()
