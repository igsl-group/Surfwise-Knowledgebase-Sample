from datetime import date, datetime

from app.models import Book, Page


def iso(dt: datetime | None) -> str | None:
    """Serialize a naive-UTC datetime to a Zulu ISO-8601 string (BookStack style)."""
    return dt.isoformat() + "Z" if dt is not None else None


def parse_filter_dt(value: str | None) -> datetime | None:
    """Parse BookStack ``filter[updated_at:gt]`` value (ISO datetime or YYYY-MM-DD)."""
    if not value:
        return None
    v = value.strip().replace("Z", "")
    try:
        dt = datetime.fromisoformat(v)
        return dt.replace(tzinfo=None)
    except ValueError:
        pass
    try:
        return datetime.combine(date.fromisoformat(v), datetime.min.time())
    except ValueError:
        return None


def page_stub(p: Page) -> dict:
    """BookStack list/`contents` representation of a page (no body)."""
    return {
        "id": p.id,
        "book_id": p.book_id,
        "chapter_id": p.chapter_id or 0,
        "name": p.name,
        "slug": p.slug,
        "book_slug": p.book.slug if p.book else "",
        "created_at": iso(p.created_at),
        "updated_at": iso(p.updated_at),
    }


def book_stub(b: Book) -> dict:
    return {
        "id": b.id,
        "name": b.name,
        "slug": b.slug,
        "description": b.description,
        "created_at": iso(b.created_at),
        "updated_at": iso(b.updated_at),
    }
