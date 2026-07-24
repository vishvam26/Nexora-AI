import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.db.database import Base

logger = logging.getLogger("app.db.tenant_session")

TENANTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage", "tenants"))

# Cache of tenant engines to avoid re-creating SQLite engine connections per query
_tenant_engines = {}
_tenant_sessionmakers = {}


def get_tenant_db_path(user_id: int) -> str:
    """
    Returns absolute file path for a user's isolated SQLite database.
    """
    user_dir = os.path.join(TENANTS_DIR, f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, "tenant.db").replace("\\", "/")


def get_tenant_engine(user_id: int):
    """
    Retrieves or creates a thread-safe SQLAlchemy engine bound to user_{id}/tenant.db.
    """
    if user_id in _tenant_engines:
        return _tenant_engines[user_id]

    db_path = get_tenant_db_path(user_id)
    sqlite_url = f"sqlite:///{db_path}"
    
    engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )
    
    # Initialize all tenant-specific database schema tables
    Base.metadata.create_all(bind=engine)
    
    _tenant_engines[user_id] = engine
    _tenant_sessionmakers[user_id] = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info(f"Initialized isolated tenant DB for user_id={user_id} at: {db_path}")
    return engine


def get_tenant_session(user_id: int) -> Session:
    """
    Creates and returns a new DB session for the specific user's isolated database.
    """
    if user_id not in _tenant_sessionmakers:
        get_tenant_engine(user_id)
    return _tenant_sessionmakers[user_id]()
