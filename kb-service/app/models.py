from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_utcnow, onupdate=_utcnow, nullable=False, index=True
    )


class Book(TimestampMixin, Base):
    """A collection of pages (maps to a BookStack 'book')."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    pages: Mapped[list["Page"]] = relationship(
        back_populates="book", cascade="all, delete-orphan", lazy="selectin"
    )


class Page(TimestampMixin, Base):
    """A single knowledge-base article, authored in Markdown."""

    __tablename__ = "pages"
    __table_args__ = (UniqueConstraint("book_id", "slug", name="uq_pages_book_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chapter_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    markdown: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # Optional original uploaded file (document management).
    original_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    book: Mapped["Book"] = relationship(back_populates="pages", lazy="joined")


class ApiToken(TimestampMixin, Base):
    """API token for BookStack-style ``Authorization: Token id:secret`` auth."""

    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    token_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    secret_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
