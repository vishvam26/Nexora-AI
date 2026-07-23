import sys
import os
import logging
from sqlalchemy import create_engine, text, inspect

# Set path so we can import settings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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

        # 2. Create CompanySettings table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS company_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL UNIQUE,
                default_llm VARCHAR(50) NOT NULL DEFAULT 'gemini-1.5-flash',
                theme VARCHAR(20) NOT NULL DEFAULT 'dark',
                logo VARCHAR(255) NULL,
                max_file_size INTEGER NOT NULL DEFAULT 10485760,
                allowed_extensions TEXT NULL,
                FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
            )
        """) if dialect == "sqlite" else text("""
            CREATE TABLE IF NOT EXISTS company_settings (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL UNIQUE REFERENCES companies(id) ON DELETE CASCADE,
                default_llm VARCHAR(50) NOT NULL DEFAULT 'gemini-1.5-flash',
                theme VARCHAR(20) NOT NULL DEFAULT 'dark',
                logo VARCHAR(255) NULL,
                max_file_size INTEGER NOT NULL DEFAULT 10485760,
                allowed_extensions JSON NULL
            )
        """))
        logger.info("Company settings table ensured.")

        # 3. Create CompanySecrets table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS company_secrets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                provider VARCHAR(50) NOT NULL,
                encrypted_api_key VARCHAR(512) NOT NULL,
                FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
            )
        """) if dialect == "sqlite" else text("""
            CREATE TABLE IF NOT EXISTS company_secrets (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                provider VARCHAR(50) NOT NULL,
                encrypted_api_key VARCHAR(512) NOT NULL
            )
        """))
        logger.info("Company secrets table ensured.")

        # 4. Create Invitations table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS invitations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                email VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'EMPLOYEE',
                token VARCHAR(36) NOT NULL UNIQUE,
                expires_at DATETIME NOT NULL,
                accepted BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
            )
        """) if dialect == "sqlite" else text("""
            CREATE TABLE IF NOT EXISTS invitations (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                email VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'EMPLOYEE',
                token VARCHAR(36) NOT NULL UNIQUE,
                expires_at TIMESTAMP NOT NULL,
                accepted BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        logger.info("Invitations table ensured.")

        # 5. Add columns to Users
        inspector = inspect(engine)
        user_columns = [col["name"] for col in inspector.get_columns("users")]
        
        if "company_id" not in user_columns:
            logger.info("Adding company_id column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL"))
        if "company_role" not in user_columns:
            logger.info("Adding company_role column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN company_role VARCHAR(20) DEFAULT 'EMPLOYEE'"))
        if "manager_id" not in user_columns:
            logger.info("Adding manager_id column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN manager_id INTEGER REFERENCES users(id) ON DELETE SET NULL"))

        # 6. Add columns to Workspaces
        workspace_columns = [col["name"] for col in inspector.get_columns("workspaces")]
        if "company_id" not in workspace_columns:
            logger.info("Adding company_id column to workspaces table...")
            conn.execute(text("ALTER TABLE workspaces ADD COLUMN company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE"))

        # 6b. Add columns to Knowledge Documents
        doc_columns = [col["name"] for col in inspector.get_columns("knowledge_documents")]
        if "visibility" not in doc_columns:
            logger.info("Adding visibility column to knowledge_documents table...")
            conn.execute(text("ALTER TABLE knowledge_documents ADD COLUMN visibility VARCHAR(20) DEFAULT 'WORKSPACE'"))

        # 7. Add columns to Workspace Members
        member_columns = [col["name"] for col in inspector.get_columns("workspace_members")]
        if "workspace_role" not in member_columns:
            logger.info("Adding workspace_role column to workspace_members table...")
            conn.execute(text("ALTER TABLE workspace_members ADD COLUMN workspace_role VARCHAR(20) DEFAULT 'EMPLOYEE'"))

        # 8. Add columns to Activity Logs
        log_columns = [col["name"] for col in inspector.get_columns("activity_logs")]
        if "ip_address" not in log_columns:
            logger.info("Adding ip_address column to activity_logs table...")
            conn.execute(text("ALTER TABLE activity_logs ADD COLUMN ip_address VARCHAR(45) NULL"))
        if "device" not in log_columns:
            logger.info("Adding device column to activity_logs table...")
            conn.execute(text("ALTER TABLE activity_logs ADD COLUMN device VARCHAR(100) NULL"))
        if "browser" not in log_columns:
            logger.info("Adding browser column to activity_logs table...")
            conn.execute(text("ALTER TABLE activity_logs ADD COLUMN browser VARCHAR(100) NULL"))
        if "status" not in log_columns:
            logger.info("Adding status column to activity_logs table...")
            conn.execute(text("ALTER TABLE activity_logs ADD COLUMN status VARCHAR(20) DEFAULT 'SUCCESS'"))

        # 9. Populate Data Tenancy Backwards Compatibility
        # Ensure a default company exists
        companies_count = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar()
        if companies_count == 0:
            logger.info("Creating default company for backwards compatibility...")
            conn.execute(text("INSERT INTO companies (id, name, plan) VALUES (1, 'Default Company', 'ENTERPRISE')"))
            conn.execute(text("INSERT INTO company_settings (company_id, default_llm, theme) VALUES (1, 'gemini-1.5-flash', 'dark')"))

        # Link existing users to Default Company
        conn.execute(text("UPDATE users SET company_id = 1 WHERE company_id IS NULL"))
        # Link existing workspaces to Default Company
        conn.execute(text("UPDATE workspaces SET company_id = 1 WHERE company_id IS NULL"))
        # Populate workspace_role values from existing role column, mapping OWNER/ADMIN to MANAGER and others to EMPLOYEE
        conn.execute(text("""
            UPDATE workspace_members 
            SET workspace_role = CASE 
                WHEN UPPER(role) IN ('OWNER', 'ADMIN') THEN 'MANAGER'
                ELSE 'EMPLOYEE'
            END
            WHERE workspace_role IS NULL OR workspace_role = 'EMPLOYEE'
        """))

        logger.info("Migration completed successfully!")


if __name__ == "__main__":
    migrate()
