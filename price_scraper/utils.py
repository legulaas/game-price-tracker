import datetime
from typing import Dict, List, Optional
import csv
from pathlib import Path

def get_best_price_in_period(game_id: int, days: int = 180, db_path: Optional[Path] = None) -> Optional[Dict]:
    """
    Obtém o melhor preço para um jogo em um período específico
    
    Args:
        game_id: ID do jogo
        days: Período em dias (padrão: 180 = 6 meses)
        db_path: Caminho para o diretório do banco de dados
        
    Returns:
        Dicionário com informações do melhor preço ou None se não houver dados
    """
    if db_path is None:
        db_path = Path(__file__).parent.parent / "database"
    
    prices_csv = db_path / "prices.csv"
    
    if not prices_csv.exists():
        return None
    
    # Calcular a data limite para o período
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
    cutoff_str = cutoff_date.isoformat()
    
    best_price = None
    
    with open(prices_csv, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row['game_id']) != game_id:
                continue
                
            if row['timestamp'] < cutoff_str:
                continue
                
            price = float(row['price'])
            
            if best_price is None or price < best_price['price']:
                best_price = {
                    'price': price,
                    'currency': row['currency'],
                    'discount_percent': float(row['discount_percent']),
                    'store': row['store'],
                    'timestamp': row['timestamp']
                }
    
    return best_price