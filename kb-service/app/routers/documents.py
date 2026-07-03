"""Document management: upload / download / list / delete.

Uploaded files are stored (bytes) and, when text-decodable, their content becomes
the page Markdown so the document is indexable by SurfWise via the BookStack API.
"""
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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.markdown_utils import slugify
from app.models import ApiToken, Book, Page
from app.routers._serializers import iso
from app.routers.pages import _unique_page_slug
from app.security import require_token

router = APIRouter(prefix="/api/documents", tags=["documents"])

_TEXT_EXTENSIONS = (".md", ".markdown", ".txt", ".text", ".csv", ".log", ".rst", ".json", ".yaml", ".yml")


def _extract_markdown(filename: str | None, content_type: str | None, data: bytes) -> str:
    """Return Markdown/plain text for indexing; fall back to a note for binaries."""
    name = (filename or "").lower()
    looks_text = name.endswith(_TEXT_EXTENSIONS) or (content_type or "").startswith("text/") or "markdown" in (content_type or "")
    try:
        text = data.decode("utf-8")
        if looks_text or text.isprintable() or "\n" in text:
            return text
    except UnicodeDecodeError:
        pass
    size = len(data)
    return (
        f"> Uploaded document **{filename or 'file'}** "
        f"({size} bytes, type `{content_type or 'unknown'}`). "
        "Binary content is not text-extracted; use download to retrieve the original file."
    )


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
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> dict:
    rows = (
        await session.execute(select(Page).order_by(Page.updated_at.desc()))
    ).scalars().unique().all()
    return {"data": [_doc_info(p) for p in rows], "total": len(rows)}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    book_id: int = Form(...),
    file: UploadFile = File(...),
    name: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> dict:
    book = (
        await session.execute(select(Book).where(Book.id == book_id))
    ).scalar_one_or_none()
    if book is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="book_id does not exist")
    data = await file.read()
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
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )
    return Response(
        content=page.markdown.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{page.slug}.md"'},
    )


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    page_id: int,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> None:
    page = (
        await session.execute(select(Page).where(Page.id == page_id))
    ).scalar_one_or_none()
    if page is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found")
    await session.delete(page)
    await session.commit()
