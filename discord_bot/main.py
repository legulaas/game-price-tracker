import os
import discord
from discord.ext import commands
import logging
import asyncio
import sys

# Adiciona o diretório raiz ao PATH para importações relativas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from discord_bot.commands import setup_commands
from discord_bot.config import load_config

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("discord_bot.log"),
    ]
)
logger = logging.getLogger("discord_bot")

def run_discord_bot():
    """Inicializa e executa o bot Discord"""
    # Carregar configurações
    config = load_config()
    
    # Configurar intent do Discord (permissões)
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    
    # Inicializar o bot
    bot = commands.Bot(command_prefix=config.get('prefix', '!'), intents=intents)
    
    # Configurar comandos
    setup_commands(bot)
    
    @bot.event
    async def on_ready():
        """Evento disparado quando o bot está pronto e conectado"""
        logger.info(f'Bot conectado como {bot.user.name} ({bot.user.id})')
        await bot.change_presence(activity=discord.Game(name="Buscando preços de jogos | !ajuda"))
        
    @bot.event
    async def on_command_error(ctx, error):
        """Tratamento global de erros de comando"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Comando não encontrado. Use `{bot.command_prefix}ajuda` para ver os comandos disponíveis.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Parâmetro obrigatório faltando. Use `{bot.command_prefix}ajuda {ctx.command}` para mais informações.")
        else:
            logger.error(f"Erro no comando {ctx.command}: {error}")
            await ctx.send(f"Ocorreu um erro ao executar o comando: {error}")
    
    # Iniciar o bot
    try:
        bot.run(config.get('token'))
    except discord.LoginFailure:
        logger.error("Token inválido. Verifique seu token no arquivo config.json.")
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {e}")

if __name__ == "__main__":
    run_discord_bot()