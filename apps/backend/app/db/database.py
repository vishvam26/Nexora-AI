import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

logger = logging.getLogger("app.db.database")

db_url = settings.DATABASE_URL or "sqlite:///./nexora_ai.db"

def _create_db_engine(url: str):
    is_sqlite = url.startswith("sqlite")
    kwargs = {}
    if is_sqlite:
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_pre_ping"] = True
        kwargs["pool_recycle"] = 300
    return create_engine(url, echo=False, **kwargs)

try:
    engine = _create_db_engine(db_url)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("[Database] Successfully verified database connection.")
except Exception as e:
    logger.warning(f"[Database] Primary connection failed: {e}. Falling back to local SQLite database.")
    engine = _create_db_engine("sqlite:///./nexora_ai.db")

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
