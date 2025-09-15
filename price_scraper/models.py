from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class Game:
    """Modelo para representar um jogo"""
    id: Optional[int]
    title: str
    platform: str
    url: str
    added_by: str
    created_at: Optional[str]

@dataclass
class PriceRecord:
    """Modelo para representar um registro de preço"""
    game_id: int
    price: float
    currency: str
    discount_percent: float
    store: str
    timestamp: str

@dataclass
class Notification:
    """Modelo para representar uma notificação para o usuário"""
    id: Optional[int]
    user_id: str
    game_id: int
    price_threshold: Optional[float]
    created_at: Optional[str]