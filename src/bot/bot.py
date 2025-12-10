"""Discord bot initialization and setup."""
import os
import logging
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class GamePriceBot(commands.Bot):
    """Custom Discord bot for game price tracking."""

    def __init__(self):
        """Initialize the bot."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=commands.DefaultHelpCommand()
        )

    async def setup_hook(self):
        """Setup hook called when bot is starting."""
        # Load cogs
        await self.load_extension("src.bot.cogs.game_commands")
        await self.load_extension("src.bot.cogs.tracker_commands")
        logger.info("Cogs loaded successfully")

    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")

        # Set bot status
        await self.change_presence(
            activity=discord.Game(name="Tracking game prices | !help")
        )

    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found. Use `!help` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Bad argument: {error}")
        else:
            logger.error(f"Unhandled error in command {ctx.command}: {error}", exc_info=error)
            await ctx.send("An error occurred while processing your command.")


def create_bot() -> GamePriceBot:
    """Create and return bot instance."""
    return GamePriceBot()
