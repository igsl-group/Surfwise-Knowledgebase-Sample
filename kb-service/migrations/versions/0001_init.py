"""initial schema: books, pages, api_tokens

Revision ID: 0001_init
Revises:
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_books_slug", "books", ["slug"], unique=True)
    op.create_index("ix_books_updated_at", "books", ["updated_at"])

    op.create_table(
        "pages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "book_id",
            sa.Integer(),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chapter_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("markdown", sa.Text(), server_default="", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("book_id", "slug", name="uq_pages_book_slug"),
    )
    op.create_index("ix_pages_book_id", "pages", ["book_id"])
    op.create_index("ix_pages_name", "pages", ["name"])
    op.create_index("ix_pages_slug", "pages", ["slug"])
    op.create_index("ix_pages_updated_at", "pages", ["updated_at"])

    op.create_table(
        "api_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("token_id", sa.String(length=64), nullable=False),
        sa.Column("secret_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_api_tokens_token_id", "api_tokens", ["token_id"], unique=True)
    op.create_index("ix_api_tokens_updated_at", "api_tokens", ["updated_at"])


def downgrade() -> None:
    op.drop_table("api_tokens")
    op.drop_table("pages")
    op.drop_table("books")
