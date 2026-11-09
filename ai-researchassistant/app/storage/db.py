import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.models.database import Base

logger = logging.getLogger(__name__)

# Determine connection URL
def get_engine():
    db_url = settings.DATABASE_URL
    if settings.USE_SQLITE_FALLBACK:
        db_url = settings.SQLITE_FALLBACK_URL
        connect_args = {"check_same_thread": False}
        return create_engine(db_url, connect_args=connect_args)
    
    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        # Test connection
        with engine.connect() as conn:
            pass
        return engine
    except Exception as e:
        logger.warning(
            f"Could not connect to PostgreSQL at {db_url}: {e}. Falling back to SQLite at {settings.SQLITE_FALLBACK_URL}"
        )
        connect_args = {"check_same_thread": False}
        return create_engine(settings.SQLITE_FALLBACK_URL, connect_args=connect_args)


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables in the active database engine."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")


def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
