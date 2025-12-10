"""Database models for game price tracking."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from .config import Base


class User(Base):
    """Discord user model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tracked_games = relationship("TrackedGame", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, discord_id={self.discord_id}, username={self.username})>"


class Game(Base):
    """Game model with price information."""
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    url = Column(Text, nullable=False)
    platform = Column(String(100), nullable=False)  # e.g., "Steam", "Epic", "GOG"
    current_price = Column(Float, nullable=True)
    original_price = Column(Float, nullable=True)
    discount_percentage = Column(Integer, nullable=True)  # 0-100
    is_on_sale = Column(Boolean, default=False)
    last_checked = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Additional metadata
    image_url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    # Price history tracking
    lowest_price = Column(Float, nullable=True)
    lowest_price_date = Column(DateTime, nullable=True)

    # Relationships
    tracked_by = relationship("TrackedGame", back_populates="game", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="game", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Game(id={self.id}, title={self.title}, platform={self.platform}, current_price={self.current_price})>"


class TrackedGame(Base):
    """User's wishlist/tracked games."""
    __tablename__ = "tracked_games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    target_price = Column(Float, nullable=True)  # Optional: notify when price drops below this
    notify_on_any_sale = Column(Boolean, default=True)
    last_notified = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="tracked_games")
    game = relationship("Game", back_populates="tracked_by")

    def __repr__(self):
        return f"<TrackedGame(user_id={self.user_id}, game_id={self.game_id}, target_price={self.target_price})>"


class PriceHistory(Base):
    """Historical price data for games."""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    price = Column(Float, nullable=False)
    discount_percentage = Column(Integer, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    game = relationship("Game", back_populates="price_history")

    def __repr__(self):
        return f"<PriceHistory(game_id={self.game_id}, price={self.price}, recorded_at={self.recorded_at})>"


class Notification(Base):
    """Notification log to avoid duplicate notifications."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    notification_type = Column(String(50), nullable=False)  # e.g., "price_drop", "sale_alert"
    sent_at = Column(DateTime, default=datetime.utcnow)
    message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Notification(user_id={self.user_id}, game_id={self.game_id}, type={self.notification_type})>"
