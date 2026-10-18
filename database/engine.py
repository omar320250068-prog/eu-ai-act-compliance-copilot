"""
engine.py
Async SQLAlchemy engine and session factory.
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://omar:securepass@postgres:5432/eu_ai_act_db")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,         # Set True for SQL query logging in development
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # Validates connections before use — prevents stale connection errors
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """FastAPI dependency — yields a database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
