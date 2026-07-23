"""v2 enterprise saas

Revision ID: f9e8d7c6b5a4
Revises: bd7f8e91d0e2
Create Date: 2026-07-23 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9e8d7c6b5a4'
down_revision: Union[str, None] = 'bd7f8e91d0e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create companies table
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('plan', sa.String(length=20), nullable=False, server_default='FREE'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )

    # 2. Create company_settings table
    op.create_table(
        'company_settings',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('default_llm', sa.String(length=50), nullable=False, server_default='gemini-1.5-flash'),
        sa.Column('theme', sa.String(length=20), nullable=False, server_default='dark'),
        sa.Column('logo', sa.String(length=255), nullable=True),
        sa.Column('max_file_size', sa.Integer(), nullable=False, server_default='10485760'),
        sa.Column('allowed_extensions', sa.JSON(), nullable=True)
    )

    # 3. Create company_secrets table
    op.create_table(
        'company_secrets',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('encrypted_api_key', sa.String(length=512), nullable=False)
    )

    # 4. Create invitations table
    op.create_table(
        'invitations',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='EMPLOYEE'),
        sa.Column('token', sa.String(length=36), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('accepted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )

    # 5. Add columns to users
    op.add_column('users', sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='SET NULL'), nullable=True))
    op.add_column('users', sa.Column('company_role', sa.String(length=20), nullable=False, server_default='EMPLOYEE'))
    op.add_column('users', sa.Column('manager_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))

    # 6. Add columns to workspaces
    op.add_column('workspaces', sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=True))

    # 6b. Add columns to knowledge_documents
    op.add_column('knowledge_documents', sa.Column('visibility', sa.String(length=20), nullable=False, server_default='WORKSPACE'))

    # 7. Add columns to workspace_members
    op.add_column('workspace_members', sa.Column('workspace_role', sa.String(length=20), nullable=False, server_default='EMPLOYEE'))

    # 8. Add columns to activity_logs
    op.add_column('activity_logs', sa.Column('ip_address', sa.String(length=45), nullable=True))
    op.add_column('activity_logs', sa.Column('device', sa.String(length=100), nullable=True))
    op.add_column('activity_logs', sa.Column('browser', sa.String(length=100), nullable=True))
    op.add_column('activity_logs', sa.Column('status', sa.String(length=20), nullable=False, server_default='SUCCESS'))

    # 9. Data Tenancy Backwards Compatibility
    bind = op.get_bind()
    dialect_name = bind.dialect.name

    if dialect_name == "sqlite":
        op.execute("INSERT OR IGNORE INTO companies (id, name, plan, created_at, updated_at) VALUES (1, 'Default Company', 'ENTERPRISE', datetime('now'), datetime('now'))")
        op.execute("INSERT OR IGNORE INTO company_settings (company_id, default_llm, theme, max_file_size) VALUES (1, 'gemini-1.5-flash', 'dark', 10485760)")
    else:
        op.execute("INSERT INTO companies (id, name, plan, created_at, updated_at) VALUES (1, 'Default Company', 'ENTERPRISE', NOW(), NOW()) ON CONFLICT (id) DO NOTHING")
        op.execute("INSERT INTO company_settings (company_id, default_llm, theme, max_file_size) VALUES (1, 'gemini-1.5-flash', 'dark', 10485760) ON CONFLICT (company_id) DO NOTHING")

    op.execute("UPDATE users SET company_id = 1 WHERE company_id IS NULL")
    op.execute("UPDATE workspaces SET company_id = 1 WHERE company_id IS NULL")
    op.execute("""
        UPDATE workspace_members 
        SET workspace_role = CASE 
            WHEN UPPER(role) IN ('OWNER', 'ADMIN') THEN 'MANAGER'
            ELSE 'EMPLOYEE'
        END
    """)


def downgrade() -> None:
    pass
