"""Database configuration and connection management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import structlog

from app.config import settings

logger = structlog.get_logger()

# Create database engines (with error handling)
try:
    if "mysql" in settings.database_url:
        # MySQL configuration
        engine = create_engine(settings.database_url)
        async_engine = create_async_engine(
            settings.database_url.replace("mysql+pymysql://", "mysql+aiomysql://"))
    elif "postgresql" in settings.database_url:
        # PostgreSQL configuration
        engine = create_engine(settings.database_url)
        async_engine = create_async_engine(settings.database_url.replace(
            "postgresql://", "postgresql+asyncpg://"))
    else:
        # SQLite fallback
        engine = create_engine(settings.database_url)
        async_engine = create_async_engine("sqlite+aiosqlite:///./app.db")
except Exception as e:
    logger.warning(f"Database connection failed: {e}. Using SQLite fallback.")
    # Fallback to SQLite for development
    engine = create_engine("sqlite:///./app.db")
    async_engine = create_async_engine("sqlite+aiosqlite:///./app.db")

# Create session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# Create declarative base
Base = declarative_base()


async def init_db():
    """Initialize database tables."""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def get_db():
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_db():
    """Get synchronous database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
