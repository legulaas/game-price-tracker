"""Database configuration and session management."""
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+aiomysql://gpt_user:gpt_password@localhost:3306/game_price_tracker")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
