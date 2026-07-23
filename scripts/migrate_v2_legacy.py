"""
migrate_v2.py — Legacy Manual Migration Script

NOTE: This is a legacy script kept for reference.
All database migrations are now managed via Alembic:
    alembic upgrade head

This script was used to manually add V2 enterprise SaaS columns
(company_id, company_role, workspace_role, etc.) to existing databases
before Alembic was set up. It is NO LONGER NEEDED for new installations.

Run 'alembic upgrade head' instead.
"""
import sys
import os
import logging
from sqlalchemy import create_engine, text, inspect

# Set path so we can import settings
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps", "backend"))
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_v2")


def migrate():
    db_url = settings.DATABASE_URL
    logger.info(f"Connecting to database: {db_url}")
    engine = create_engine(db_url)
    
    dialect = engine.dialect.name
    logger.info(f"Detected database dialect: {dialect}")
    
    with engine.begin() as conn:
        # 1. Create Companies table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                plan VARCHAR(20) NOT NULL DEFAULT 'FREE',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """) if dialect == "sqlite" else text("""
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                plan VARCHAR(20) NOT NULL DEFAULT 'FREE',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        logger.info("Companies table ensured.")

        # 5. Add columns to Users
        inspector = inspect(engine)
        user_columns = [col["name"] for col in inspector.get_columns("users")]
        
        if "company_id" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL"))
        if "company_role" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN company_role VARCHAR(20) DEFAULT 'EMPLOYEE'"))
        if "manager_id" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN manager_id INTEGER REFERENCES users(id) ON DELETE SET NULL"))

        logger.info("Migration completed successfully!")


if __name__ == "__main__":
    migrate()
