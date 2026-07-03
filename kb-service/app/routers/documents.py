"""Document management: upload / download / list / delete (admin scope for writes)."""
from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session
from app.markdown_utils import slugify
from app.models import ApiToken, Book, Page
from app.routers._serializers import iso
from app.routers.pages import _unique_page_slug
from app.security import require_admin_token, require_token

router = APIRouter(prefix="/api/documents", tags=["documents"])

_TEXT_EXTENSIONS = (".md", ".markdown", ".txt", ".text", ".csv", ".log", ".rst", ".json", ".yaml", ".yml")


def _extract_markdown(filename: str | None, content_type: str | None, data: bytes) -> str:
    name = (filename or "").lower()
    looks_text = name.endswith(_TEXT_EXTENSIONS) or (content_type or "").startswith("text/") or "markdown" in (content_type or "")
    try:
        text = data.decode("utf-8")
        if looks_text or "\n" in text or text.isprintable():
            return text
    except UnicodeDecodeError:
        pass
    return (
        f"> Uploaded document **{filename or 'file'}** "
        f"({len(data)} bytes, type `{content_type or 'unknown'}`). "
        "Binary content is not text-extracted; use download to retrieve the original file."
    )


def _content_disposition(filename: str) -> str:
    """latin-1-safe, injection-safe Content-Disposition (RFC 5987)."""
    safe = "".join(c for c in filename if c.isprintable() and c not in '"\\')
    ascii_name = safe.encode("ascii", "ignore").decode().strip() or "download"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"


def _doc_info(p: Page) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "book_id": p.book_id,
        "book_name": p.book.name if p.book else "",
        "filename": p.original_filename,
        "size": p.file_size,
        "content_type": p.content_type,
        "is_file": p.file_data is not None,
        "updated_at": iso(p.updated_at),
    }


@router.get("")
async def list_documents(
    count: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> dict:
    total = (await session.execute(select(func.count(Page.id)))).scalar_one()
    rows = (
        await session.execute(
            select(Page).order_by(Page.updated_at.desc()).offset(offset).limit(min(count, 500))
        )
    ).scalars().unique().all()
    return {"data": [_doc_info(p) for p in rows], "total": total}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    book_id: int = Form(...),
    file: UploadFile = File(...),
    name: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_admin_token),
) -> dict:
    book = (
        await session.execute(select(Book).where(Book.id == book_id))
    ).scalar_one_or_none()
    if book is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="book_id does not exist")

    max_mb = get_settings().max_upload_mb
    max_bytes = max_mb * 1024 * 1024
    data = b""
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        data += chunk
        if len(data) > max_bytes:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds the {max_mb} MB upload limit",
            )
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Empty file")

    markdown = _extract_markdown(file.filename, file.content_type, data)
    title = name or file.filename or "Untitled document"
    slug = await _unique_page_slug(session, book_id, slugify(title))
    page = Page(
        book_id=book_id,
        name=title,
        slug=slug,
        markdown=markdown,
        original_filename=file.filename,
        content_type=file.content_type,
        file_size=len(data),
        file_data=data,
    )
    session.add(page)
    await session.commit()
    await session.refresh(page)
    return _doc_info(page)


@router.get("/{page_id}/download")
async def download_document(
    page_id: int,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> Response:
    page = (
        await session.execute(select(Page).where(Page.id == page_id))
    ).scalar_one_or_none()
    if page is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found")
    if page.file_data is not None:
        fname = page.original_filename or f"{page.slug}.bin"
        return Response(
            content=page.file_data,
            media_type=page.content_type or "application/octet-stream",
            headers={"Content-Disposition": _content_disposition(fname)},
        )
    return Response(
        content=page.markdown.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": _content_disposition(page.slug + ".md")},
    )


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    page_id: int,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_admin_token),
) -> None:
    page = (
        await session.execute(select(Page).where(Page.id == page_id))
    ).scalar_one_or_none()
    if page is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found")
    await session.delete(page)
    await session.commit()
