import bleach
import markdown as _md
from slugify import slugify as _slugify

_ALLOWED_TAGS = {
    "a", "abbr", "acronym", "b", "blockquote", "br", "code", "div", "em", "h1", "h2",
    "h3", "h4", "h5", "h6", "hr", "i", "img", "li", "ol", "p", "pre", "span", "strong",
    "table", "tbody", "td", "th", "thead", "tr", "ul",
}
_ALLOWED_ATTRS = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title"],
    "*": ["class"],
}


def slugify(text: str) -> str:
    return _slugify(text) or "untitled"


def render_html(markdown_text: str) -> str:
    """Render Markdown to HTML and sanitize it (prevents stored XSS in the viewer)."""
    html = _md.markdown(
        markdown_text or "",
        extensions=["extra", "sane_lists", "tables", "fenced_code", "toc"],
    )
    return bleach.clean(
        html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, protocols=["http", "https", "mailto"], strip=True
    )
