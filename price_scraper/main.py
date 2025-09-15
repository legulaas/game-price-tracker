import csv
import os
import argparse
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from price_scraper.models import Game, PriceRecord
from price_scraper.stores import get_store_scraper

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("price_scraper")

# Caminho do CSV (posteriormente será substituído pelo SQLite)
DB_PATH = Path(__file__).parent.parent / "database"
DB_PATH.mkdir(exist_ok=True)
GAMES_CSV = DB_PATH / "games.csv"
PRICES_CSV = DB_PATH / "prices.csv"

def init_csv_files():
    """Inicializa os arquivos CSV se não existirem"""
    if not GAMES_CSV.exists():
        with open(GAMES_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'title', 'platform', 'url', 'added_by', 'created_at'])
    
    if not PRICES_CSV.exists():
        with open(PRICES_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['game_id', 'price', 'currency', 'discount_percent', 'store', 'timestamp'])

def get_game_by_title(title: str, platform: Optional[str] = None) -> Optional[Game]:
    """Busca um jogo pelo título no CSV"""
    if not GAMES_CSV.exists():
        return None
    
    with open(GAMES_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['title'].lower() == title.lower():
                if platform and row['platform'].lower() != platform.lower():
                    continue
                return Game(
                    id=int(row['id']),
                    title=row['title'],
                    platform=row['platform'],
                    url=row['url'],
                    added_by=row['added_by'],
                    created_at=row['created_at']
                )
    return None

def add_game(game: Game) -> Game:
    """Adiciona um novo jogo ao CSV"""
    # Determinar o próximo ID
    next_id = 1
    if GAMES_CSV.exists():
        with open(GAMES_CSV, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            ids = [int(row['id']) for row in reader]
            if ids:
                next_id = max(ids) + 1
    
    # Definir o ID e timestamp
    game.id = next_id
    if not game.created_at:
        game.created_at = datetime.datetime.now().isoformat()
    
    # Adicionar ao CSV
    with open(GAMES_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            game.id,
            game.title,
            game.platform,
            game.url,
            game.added_by,
            game.created_at
        ])
    
    return game

def add_price_record(record: PriceRecord):
    """Adiciona um registro de preço ao CSV"""
    with open(PRICES_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            record.game_id,
            record.price,
            record.currency,
            record.discount_percent,
            record.store,
            record.timestamp
        ])

def search_game_price(title: str, platform: str = None) -> Dict:
    """
    Busca o preço de um jogo em todas as lojas ou em uma plataforma específica
    
    Args:
        title: Título do jogo
        platform: Plataforma específica (opcional)
        
    Returns:
        Dict com informações sobre o jogo e preços encontrados
    """
    logger.info(f"Buscando preço para o jogo: {title} na plataforma: {platform or 'todas'}")
    
    # Verificar se o jogo já existe no banco
    game = get_game_by_title(title, platform)
    
    # Se não existir e tiver plataforma definida, criar o jogo
    if not game and platform:
        game = Game(
            id=None,
            title=title,
            platform=platform,
            url="",  # Será atualizado após o scraping
            added_by="system",
            created_at=None
        )
    
    # Obter o scraper para a loja específica ou todos se não especificado
    stores = [platform] if platform else ['steam', 'psn', 'xbox', 'nintendo']
    results = {}
    
    for store_name in stores:
        try:
            scraper = get_store_scraper(store_name)
            if not scraper:
                logger.warning(f"Scraper não encontrado para a loja: {store_name}")
                continue
                
            logger.info(f"Iniciando busca na loja: {store_name}")
            price_data = scraper.search_game(title)
            
            if price_data:
                # Se o jogo não existia, criar agora com os dados da primeira loja onde foi encontrado
                if not game:
                    game = Game(
                        id=None,
                        title=price_data.get('title', title),
                        platform=store_name,
                        url=price_data.get('url', ''),
                        added_by="system",
                        created_at=None
                    )
                    game = add_game(game)
                # Se o jogo já existe mas não tem URL
                elif not game.url and 'url' in price_data:
                    game.url = price_data['url']
                    # TODO: Atualizar URL no banco quando for SQLite
                
                # Registrar o preço encontrado
                price_record = PriceRecord(
                    game_id=game.id,
                    price=price_data.get('price', 0.0),
                    currency=price_data.get('currency', 'BRL'),
                    discount_percent=price_data.get('discount_percent', 0),
                    store=store_name,
                    timestamp=datetime.datetime.now().isoformat()
                )
                add_price_record(price_record)
                
                results[store_name] = {
                    'title': price_data.get('title', title),
                    'price': price_data.get('price', 0.0),
                    'currency': price_data.get('currency', 'BRL'),
                    'discount_percent': price_data.get('discount_percent', 0),
                    'url': price_data.get('url', ''),
                    'timestamp': price_record.timestamp
                }
        except Exception as e:
            logger.error(f"Erro ao buscar preço na loja {store_name}: {str(e)}")
    
    return {
        'game': game.__dict__ if game else {'title': title},
        'prices': results
    }

def main():
    """Função principal que pode ser chamada via linha de comando"""
    parser = argparse.ArgumentParser(description="Game Price Scraper")
    parser.add_argument("--title", "-t", required=True, help="Título do jogo")
    parser.add_argument("--platform", "-p", help="Plataforma específica (steam, psn, xbox, nintendo)")
    
    args = parser.parse_args()
    
    # Inicializar arquivos CSV
    init_csv_files()
    
    # Buscar preço
    result = search_game_price(args.title, args.platform)
    
    # Exibir resultado
    if not result['prices']:
        print(f"Nenhum preço encontrado para o jogo: {args.title}")
    else:
        print(f"Preços encontrados para: {result['game'].get('title', args.title)}")
        for store, data in result['prices'].items():
            print(f"  {store.upper()}: {data['currency']} {data['price']}")
            if data['discount_percent'] > 0:
                print(f"    Desconto: {data['discount_percent']}%")
            print(f"    URL: {data['url']}")

if __name__ == "__main__":
    main()