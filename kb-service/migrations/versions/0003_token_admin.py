"""add is_admin to api_tokens

Revision ID: 0003_token_admin
Revises: 0002_document_files
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_token_admin"
down_revision = "0002_document_files"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "api_tokens",
        sa.Column("is_admin", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    # existing tokens (e.g. the seeded default) become admins for backward-compat
    op.execute("UPDATE api_tokens SET is_admin = true")


def downgrade() -> None:
    op.drop_column("api_tokens", "is_admin")
