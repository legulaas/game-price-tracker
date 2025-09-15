import discord
from discord.ext import commands
import asyncio
import logging
import sys
import os
from typing import Optional, List, Dict
import datetime

# Adiciona o diretório raiz ao PATH para importações relativas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from price_scraper.main import search_game_price, get_game_by_title, init_csv_files
from price_scraper.utils import get_best_price_in_period

logger = logging.getLogger("discord_bot.commands")

def setup_commands(bot):
    """Configura os comandos do bot"""
    
    @bot.command(name="ajuda")
    async def ajuda(ctx):
        """Exibe a lista de comandos disponíveis"""
        embed = discord.Embed(
            title="🎮 Game Price Tracker - Comandos",
            description="Lista de comandos disponíveis para o Bot de Preços de Jogos",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name=f"{bot.command_prefix}preco <jogo> [plataforma]",
            value="Busca o preço atual de um jogo nas lojas. Plataforma opcional: steam, psn, xbox, nintendo",
            inline=False
        )
        
        embed.add_field(
            name=f"{bot.command_prefix}historico <jogo> [dias]",
            value="Exibe o melhor preço de um jogo nos últimos X dias (padrão: 180 dias)",
            inline=False
        )
        
        embed.add_field(
            name=f"{bot.command_prefix}observar <jogo> [preço_alvo]",
            value="Adiciona um jogo à sua lista de observação, opcionalmente com um preço alvo",
            inline=False
        )
        
        embed.add_field(
            name=f"{bot.command_prefix}ajuda",
            value="Exibe esta mensagem de ajuda",
            inline=False
        )
        
        embed.set_footer(text="🤖 Powered by Discord.py & Playwright")
        
        await ctx.send(embed=embed)
    
    @bot.command(name="preco", aliases=["price", "p"])
    async def preco(ctx, *, args):
        """
        Busca o preço atual de um jogo
        
        Uso: !preco <jogo> [plataforma]
        Exemplo: !preco Elden Ring
                !preco God of War psn
        """
        # Inicializar arquivos CSV se não existirem
        init_csv_files()
        
        # Processar argumentos
        args_parts = args.strip().split()
        platform = None
        
        # Verificar se o último argumento é uma plataforma
        valid_platforms = ['steam', 'psn', 'xbox', 'nintendo']
        if args_parts[-1].lower() in valid_platforms:
            platform = args_parts[-1].lower()
            game_title = ' '.join(args_parts[:-1])
        else:
            game_title = args
        
        # Enviar mensagem de espera
        waiting_msg = await ctx.send(f"🔍 Buscando preços para **{game_title}**... Isso pode levar alguns segundos.")
        
        try:
            # Buscar preço de forma assíncrona para não bloquear o bot
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, search_game_price, game_title, platform)
            
            # Remover mensagem de espera
            await waiting_msg.delete()
            
            if not result['prices']:
                await ctx.send(f"❌ Não encontrei preços para **{game_title}** nas lojas consultadas.")
                return
            
            # Usar o título extraído do produto analisado (primeiro resultado)
            first_store = next(iter(result['prices'].values()), None)
            embed_title = first_store['title'] if first_store and 'title' in first_store else result['game'].get('title', game_title)
            embed = discord.Embed(
                title=f"🎮 {embed_title}",
                description=f"Preços encontrados em {len(result['prices'])} loja(s)",
                color=discord.Color.green()
            )
            
            for store, data in result['prices'].items():
                price_str = f"{data['currency']} {data['price']:.2f}"
                
                if data['discount_percent'] > 0:
                    price_str += f" 🔥 **{data['discount_percent']}% OFF**"
                
                embed.add_field(
                    name=f"📊 {store.upper()}",
                    value=f"{price_str}\n[Ver na loja]({data['url']})",
                    inline=False
                )
            
            embed.set_footer(text=f"⏱️ Atualizado em {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erro ao buscar preço: {e}")
            await waiting_msg.delete()
            await ctx.send(f"❌ Ocorreu um erro ao buscar o preço: {str(e)}")
    
    @bot.command(name="historico", aliases=["history", "h"])
    async def historico(ctx, *, args):
        """
        Exibe o histórico de preços de um jogo
        
        Uso: !historico <jogo> [dias]
        Exemplo: !historico Elden Ring
                !historico God of War 90
        """
        # Inicializar arquivos CSV se não existirem
        init_csv_files()
        
        # Processar argumentos
        args_parts = args.strip().split()
        days = 180  # Padrão: 6 meses
        
        # Verificar se o último argumento é um número (dias)
        if args_parts[-1].isdigit():
            days = int(args_parts[-1])
            game_title = ' '.join(args_parts[:-1])
        else:
            game_title = args
        
        # Verificar se o jogo existe no banco
        game = get_game_by_title(game_title)
        
        if not game:
            await ctx.send(f"❌ Jogo **{game_title}** não encontrado no banco de dados. Use `{bot.command_prefix}preco {game_title}` primeiro.")
            return
        
        # Obter melhor preço no período
        best_price = get_best_price_in_period(game.id, days)
        
        if not best_price:
            await ctx.send(f"❌ Não encontrei histórico de preços para **{game.title}** nos últimos {days} dias.")
            return
        
        # Criar embed com resultado
        embed = discord.Embed(
            title=f"📊 Histórico de {game.title}",
            description=f"Melhor preço nos últimos {days} dias",
            color=discord.Color.gold()
        )
        
        store = best_price['store'].upper()
        price_str = f"{best_price['currency']} {best_price['price']:.2f}"
        
        if best_price['discount_percent'] > 0:
            price_str += f" 🔥 **{best_price['discount_percent']}% OFF**"
        
        timestamp = datetime.datetime.fromisoformat(best_price['timestamp'])
        
        embed.add_field(
            name=f"💰 Melhor preço ({store})",
            value=f"{price_str}\nRegistrado em {timestamp.strftime('%d/%m/%Y %H:%M')}",
            inline=False
        )
        
        embed.set_footer(text=f"⏱️ Consultado em {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        await ctx.send(embed=embed)
    
    @bot.command(name="observar", aliases=["watch", "w"])
    async def observar(ctx, *, args):
        """
        Adiciona um jogo à lista de observação
        
        Uso: !observar <jogo> [preço_alvo]
        Exemplo: !observar Elden Ring
                !observar God of War 150.00
        """
        # Por enquanto, apenas simular a função, pois dependerá do banco SQLite
        await ctx.send("⚠️ Função de observação será implementada em breve, quando o banco SQLite estiver configurado.")
        
        # Processar argumentos
        args_parts = args.strip().split()
        price_target = None
        
        # Verificar se o último argumento é um número (preço)
        if args_parts[-1].replace('.', '').isdigit():
            try:
                price_target = float(args_parts[-1])
                game_title = ' '.join(args_parts[:-1])
            except ValueError:
                game_title = args
        else:
            game_title = args
        
        # Mensagem explicativa
        if price_target:
            await ctx.send(f"ℹ️ Quando implementado: Você será notificado quando **{game_title}** estiver abaixo de R$ {price_target:.2f}")
        else:
            await ctx.send(f"ℹ️ Quando implementado: Você será notificado sobre promoções para **{game_title}**")