"""
SQLAlchemy engine and session management.

Written to work against MySQL now and PostgreSQL later with only a
DATABASE_URL change - no MySQL-specific SQL is used anywhere in the models.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# pool_pre_ping avoids "MySQL server has gone away" errors on idle connections.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
