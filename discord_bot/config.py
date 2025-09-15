import json
import os
import logging

logger = logging.getLogger("discord_bot.config")

CONFIG_FILE = "config.json"

def load_config():
    """Carrega as configurações do arquivo config.json"""
    if not os.path.exists(CONFIG_FILE):
        # Criar arquivo de configuração padrão
        default_config = {
            "token": "",
            "prefix": "!",
            "admin_ids": [],
            "log_level": "INFO"
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=4)
            
        logger.warning(f"Arquivo de configuração {CONFIG_FILE} criado. Edite-o e adicione seu token Discord.")
        return default_config
    
    # Carregar configuração existente
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # Verificar token
        if config.get("token") == "":
            logger.warning("Token do Discord não configurado. Edite o arquivo config.json.")
        
        return config
    except Exception as e:
        logger.error(f"Erro ao carregar configuração: {e}")
        return {"token": "", "prefix": "!"}