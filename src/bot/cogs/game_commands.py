"""Game search and price checking commands."""
import logging
import discord
from discord.ext import commands

from ...database.config import AsyncSessionLocal
from ...services.game_service import GameService

logger = logging.getLogger(__name__)


class GameCommands(commands.Cog):
    """Commands for searching and checking game prices."""

    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot

    @commands.command(name="search", aliases=["s"])
    async def search_game(self, ctx, platform: str = "steam", *, query: str):
        """
        Search for games by name on a specific platform.

        Usage:
        !search <game name>
        !search <platform> <game name>

        Examples:
        !search Cyberpunk 2077
        !search steam Cyberpunk 2077
        !search playstation God of War
        !search psn Horizon
        """
        async with ctx.typing():
            try:
                # Normalize platform name
                platform = platform.lower()

                # If platform is not valid, assume it's part of the query
                valid_platforms = ["steam", "playstation", "psn", "ps"]
                if platform not in valid_platforms:
                    query = f"{platform} {query}"
                    platform = "steam"

                async with AsyncSessionLocal() as session:
                    game_service = GameService(session)
                    results = await game_service.search_games(query, platform=platform)

                if not results:
                    await ctx.send(f"{ctx.author.mention} Nenhum jogo encontrado para: **{query}** em {platform.title()}")
                    return

                # Get display name for platform
                platform_display = "PlayStation" if platform in ["playstation", "psn", "ps"] else platform.title()

                # Create embed
                embed = discord.Embed(
                    title=f"Resultados da busca: {query}",
                    description=f"**{ctx.author.mention}** Encontrados {len(results)} jogos em {platform_display}",
                    color=discord.Color.blue()
                )

                for i, game in enumerate(results[:5], 1):
                    price_info = "Grátis" if game["current_price"] == 0 else f"R$ {game['current_price']:.2f}"

                    if game["is_on_sale"] and game["original_price"]:
                        price_info = f"~~R$ {game['original_price']:.2f}~~ **R$ {game['current_price']:.2f}** ({game['discount_percentage']}% OFF)"

                    # Get platform name from game data
                    game_platform = game.get('platform', platform_display)

                    embed.add_field(
                        name=f"{i}. {game['title']}",
                        value=f"Preço: {price_info}\n[Ver no {game_platform}]({game['url']})",
                        inline=False
                    )

                await ctx.send(embed=embed)

            except Exception as e:
                logger.error(f"Error in search command: {e}")
                await ctx.send("An error occurred while searching for games.")

    @commands.command(name="price", aliases=["p"])
    async def check_price(self, ctx, *, game_url: str):
        """
        Check current price of a game by URL.

        Usage: !price <game URL>
        Example: !price https://store.steampowered.com/app/1234567/GameName/
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

                    # Create scraper and get game details
                    from ...scraper.factory import ScraperFactory
                    async with ScraperFactory.create(platform) as scraper:
                        game_data = await scraper.get_game_details(game_url)

                    if not game_data:
                        await ctx.send(f"{ctx.author.mention} Não foi possível buscar informações do jogo.")
                        return

                    # Save/update in database
                    game = await game_service.get_or_create_game(game_data)

                    # Create embed with user mention
                    embed = discord.Embed(
                        title=game_data["title"],
                        url=game_url,
                        description=f"**{ctx.author.mention}**\n\n" + (game_data.get("description", "")[:180] + "..." if game_data.get("description") else ""),
                        color=discord.Color.green() if game_data["is_on_sale"] else discord.Color.blue()
                    )

                    if game_data.get("image_url"):
                        embed.set_thumbnail(url=game_data["image_url"])

                    # Price information
                    price_info = "Grátis" if game_data["current_price"] == 0 else f"R$ {game_data['current_price']:.2f}"

                    if game_data["is_on_sale"] and game_data["original_price"]:
                        embed.add_field(
                            name="Preço Original",
                            value=f"R$ {game_data['original_price']:.2f}",
                            inline=True
                        )
                        embed.add_field(
                            name="Preço Atual",
                            value=f"**R$ {game_data['current_price']:.2f}**",
                            inline=True
                        )
                        embed.add_field(
                            name="Desconto",
                            value=f"**{game_data['discount_percentage']}% OFF**",
                            inline=True
                        )
                    else:
                        embed.add_field(
                            name="Preço",
                            value=price_info,
                            inline=True
                        )

                    embed.add_field(
                        name="Platform",
                        value=game_data["platform"],
                        inline=True
                    )

                    # Show historical low if available
                    if game and game.lowest_price:
                        embed.add_field(
                            name="Menor Preço Histórico",
                            value=f"R$ {game.lowest_price:.2f}",
                            inline=True
                        )

                        # Calculate if current price is good
                        if game.current_price and game.lowest_price > 0:
                            diff_percent = ((game.current_price - game.lowest_price) / game.lowest_price) * 100
                            if diff_percent <= 10:
                                embed.add_field(
                                    name="💰 Oportunidade",
                                    value="Preço próximo do histórico mínimo!",
                                    inline=False
                                )

                    embed.set_footer(text=f"Game ID: {game.id}" if game else "")

                    await ctx.send(embed=embed)

            except Exception as e:
                logger.error(f"Error in price command: {e}")
                await ctx.send("An error occurred while checking the game price.")

    @commands.command(name="platforms")
    async def list_platforms(self, ctx):
        """
        List supported platforms.

        Usage: !platforms
        """
        from ...scraper.factory import ScraperFactory

        platforms = ScraperFactory.get_supported_platforms()

        embed = discord.Embed(
            title="Supported Platforms",
            description="\n".join([f"• {p.title()}" for p in platforms]),
            color=discord.Color.blue()
        )

        await ctx.send(embed=embed)


async def setup(bot):
    """Setup function to add cog to bot."""
    await bot.add_cog(GameCommands(bot))
