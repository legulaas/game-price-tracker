"""Game tracking/wishlist commands."""
import logging
import discord
from discord.ext import commands
from typing import Optional

from ...database.config import AsyncSessionLocal
from ...services.tracker_service import TrackerService
from ...services.game_service import GameService

logger = logging.getLogger(__name__)


class TrackerCommands(commands.Cog):
    """Commands for tracking games (wishlist)."""

    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot

    @commands.command(name="track", aliases=["add", "watch"])
    async def track_game(self, ctx, game_url: str, target_price: Optional[float] = None):
        """
        Add a game to your tracking list (wishlist).

        Usage: !track <game URL> [target price]
        Example: !track https://store.steampowered.com/app/1234567/GameName/ 29.99
        """
        async with ctx.typing():
            try:
                # Determine platform from URL
                platform = "steam"
                if "epicgames.com" in game_url:
                    platform = "epic"
                elif "gog.com" in game_url:
                    platform = "gog"
                elif "playstation.com" in game_url:
                    platform = "playstation"

                async with AsyncSessionLocal() as session:
                    game_service = GameService(session)
                    tracker_service = TrackerService(session)

                    # Get or create game
                    from ...scraper.factory import ScraperFactory
                    async with ScraperFactory.create(platform) as scraper:
                        game_data = await scraper.get_game_details(game_url)

                    if not game_data:
                        await ctx.send(f"{ctx.author.mention} Não foi possível buscar informações do jogo.")
                        return

                    game = await game_service.get_or_create_game(game_data)

                    if not game:
                        await ctx.send(f"{ctx.author.mention} Erro ao salvar informações do jogo.")
                        return

                    # Add to tracking
                    tracked = await tracker_service.add_tracked_game(
                        discord_id=str(ctx.author.id),
                        username=ctx.author.name,
                        game_id=game.id,
                        target_price=target_price,
                        notify_on_any_sale=True
                    )

                    if not tracked:
                        await ctx.send(f"{ctx.author.mention} Erro ao adicionar jogo à sua lista de rastreamento.")
                        return

                    # Create confirmation embed
                    embed = discord.Embed(
                        title="Jogo Adicionado à Lista de Rastreamento",
                        description=f"**{ctx.author.mention}** O jogo **{game.title}** está sendo rastreado!",
                        color=discord.Color.green()
                    )

                    embed.add_field(
                        name="Preço Atual",
                        value=f"R$ {game.current_price:.2f}" if game.current_price else "N/A",
                        inline=True
                    )

                    if target_price:
                        embed.add_field(
                            name="Preço Alvo",
                            value=f"R$ {target_price:.2f}",
                            inline=True
                        )

                    embed.add_field(
                        name="Platform",
                        value=game.platform,
                        inline=True
                    )

                    embed.set_footer(text="You'll receive notifications when this game goes on sale!")

                    await ctx.send(embed=embed)

            except Exception as e:
                logger.error(f"Error in track command: {e}")
                await ctx.send("An error occurred while adding the game to your tracking list.")

    @commands.command(name="untrack", aliases=["remove", "unwatch"])
    async def untrack_game(self, ctx, game_id: int):
        """
        Remove a game from your tracking list.

        Usage: !untrack <game ID>
        Example: !untrack 5
        """
        async with ctx.typing():
            try:
                async with AsyncSessionLocal() as session:
                    tracker_service = TrackerService(session)

                    success = await tracker_service.remove_tracked_game(
                        discord_id=str(ctx.author.id),
                        game_id=game_id
                    )

                    if success:
                        await ctx.send(f"{ctx.author.mention} Game (ID: {game_id}) removed from your tracking list.")
                    else:
                        await ctx.send(f"{ctx.author.mention} Could not remove game. Make sure you're tracking this game and the ID is correct.")

            except Exception as e:
                logger.error(f"Error in untrack command: {e}")
                await ctx.send(f"{ctx.author.mention} An error occurred while removing the game from your tracking list.")

    @commands.command(name="wishlist", aliases=["list", "tracked"])
    async def show_wishlist(self, ctx):
        """
        Show your tracked games (wishlist).

        Usage: !wishlist
        """
        async with ctx.typing():
            try:
                async with AsyncSessionLocal() as session:
                    tracker_service = TrackerService(session)

                    tracked_games = await tracker_service.get_user_tracked_games(
                        discord_id=str(ctx.author.id)
                    )

                    if not tracked_games:
                        await ctx.send(f"{ctx.author.mention} You're not tracking any games yet. Use `!track <game URL>` to start tracking!")
                        return

                    # Create embed
                    embed = discord.Embed(
                        title=f"{ctx.author.name}'s Wishlist",
                        description=f"**{ctx.author.mention}** Tracking {len(tracked_games)} game(s)",
                        color=discord.Color.blue()
                    )

                    for tracked in tracked_games:
                        game = tracked.game

                        price_info = "Grátis" if game.current_price == 0 else f"R$ {game.current_price:.2f}"

                        if game.is_on_sale and game.original_price:
                            price_info = f"~~R$ {game.original_price:.2f}~~ **R$ {game.current_price:.2f}** ({game.discount_percentage}% OFF) 🔥"

                        field_value = [
                            f"Preço: {price_info}",
                            f"Plataforma: {game.platform}",
                        ]

                        if tracked.target_price:
                            field_value.append(f"Preço Alvo: R$ {tracked.target_price:.2f}")

                        field_value.append(f"[View Game]({game.url})")
                        field_value.append(f"ID: {game.id}")

                        embed.add_field(
                            name=game.title,
                            value="\n".join(field_value),
                            inline=False
                        )

                    await ctx.send(embed=embed)

            except Exception as e:
                logger.error(f"Error in wishlist command: {e}")
                await ctx.send(f"{ctx.author.mention} An error occurred while fetching your wishlist.")


async def setup(bot):
    """Setup function to add cog to bot."""
    await bot.add_cog(TrackerCommands(bot))
