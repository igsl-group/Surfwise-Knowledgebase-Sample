import markdown as _md
from slugify import slugify as _slugify


def slugify(text: str) -> str:
    return _slugify(text) or "untitled"


def render_html(markdown_text: str) -> str:
    """Render Markdown to HTML (BookStack page detail exposes rendered html)."""
    return _md.markdown(
        markdown_text or "",
        extensions=["extra", "sane_lists", "tables", "fenced_code", "toc"],
    )
