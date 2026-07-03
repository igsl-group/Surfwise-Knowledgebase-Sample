"""add uploaded-file columns to pages

Revision ID: 0002_document_files
Revises: 0001_init
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_document_files"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pages", sa.Column("original_filename", sa.String(length=512), nullable=True))
    op.add_column("pages", sa.Column("content_type", sa.String(length=255), nullable=True))
    op.add_column("pages", sa.Column("file_size", sa.Integer(), nullable=True))
    op.add_column("pages", sa.Column("file_data", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    op.drop_column("pages", "file_data")
    op.drop_column("pages", "file_size")
    op.drop_column("pages", "content_type")
    op.drop_column("pages", "original_filename")
