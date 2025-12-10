"""Main entrypoint for the Game Price Tracker bot."""
import os
import sys
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bot.bot import create_bot
from src.database.config import init_db
from src.scheduler import PriceCheckScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main function to start the bot and scheduler."""
    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)

    logger.info("Starting Game Price Tracker Bot...")

    # Check for Discord token
    discord_token = os.getenv("DISCORD_TOKEN")
    if not discord_token:
        logger.error("DISCORD_TOKEN environment variable not set!")
        sys.exit(1)

    # Initialize database
    logger.info("Initializing database...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

    # Create bot
    bot = create_bot()

    # Create and start scheduler
    scheduler = PriceCheckScheduler(bot)

    async def start_scheduler():
        """Start scheduler after bot is ready."""
        await bot.wait_until_ready()
        scheduler.start()

    # Schedule the scheduler to start after bot is ready
    asyncio.create_task(start_scheduler())

    # Start bot
    try:
        logger.info("Starting Discord bot...")
        await bot.start(discord_token)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
    finally:
        # Cleanup
        scheduler.stop()
        await bot.close()
        logger.info("Bot shut down successfully")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
