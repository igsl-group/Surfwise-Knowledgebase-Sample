from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.markdown_utils import render_html, slugify
from app.models import ApiToken, Book, Page
from app.routers._serializers import iso, page_stub, parse_filter_dt
from app.schemas import PageCreate, PageRead, PageUpdate
from app.security import require_admin_token, require_token

router = APIRouter(prefix="/api/pages", tags=["pages"])


async def _get_page(session: AsyncSession, page_id: int) -> Page:
    page = (
        await session.execute(select(Page).where(Page.id == page_id))
    ).scalar_one_or_none()
    if page is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Page not found")
    return page


async def _unique_page_slug(
    session: AsyncSession, book_id: int, base: str, exclude_id: int | None = None
) -> str:
    slug, n = base, 1
    while True:
        stmt = select(Page.id).where(Page.book_id == book_id, Page.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(Page.id != exclude_id)
        if (await session.execute(stmt)).first() is None:
            return slug
        n += 1
        slug = f"{base}-{n}"


# ---- BookStack-compatible read endpoints (consumed by SurfWise connector) ----

@router.get("")
async def list_pages(
    request: Request,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> dict:
    """List pages. Supports ``count``, ``offset``, ``filter[updated_at:gt]``, ``sort``."""
    qp = request.query_params
    count = min(int(qp.get("count", 100) or 100), 500)
    offset = int(qp.get("offset", 0) or 0)
    updated_gt = parse_filter_dt(qp.get("filter[updated_at:gt]"))
    sort = qp.get("sort", "")

    base = select(Page)
    if updated_gt is not None:
        base = base.where(Page.updated_at > updated_gt)

    total = (
        await session.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()

    if sort == "-updated_at":
        base = base.order_by(Page.updated_at.desc(), Page.id.desc())
    elif sort == "updated_at":
        base = base.order_by(Page.updated_at.asc(), Page.id.asc())
    else:
        base = base.order_by(Page.id.asc())

    rows = (
        await session.execute(base.offset(offset).limit(count))
    ).scalars().unique().all()
    return {"data": [page_stub(p) for p in rows], "total": total}


@router.get("/{page_id}")
async def get_page(
    page_id: int,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> dict:
    page = await _get_page(session, page_id)
    data = page_stub(page)
    data.update(
        {
            "markdown": page.markdown,
            "html": render_html(page.markdown),
            "raw_html": render_html(page.markdown),
        }
    )
    return data


@router.get("/{page_id}/export/markdown")
async def export_page_markdown(
    page_id: int,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> Response:
    page = await _get_page(session, page_id)
    return Response(content=page.markdown, media_type="text/plain; charset=utf-8")


@router.get("/{page_id}/export/html")
async def export_page_html(
    page_id: int,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> Response:
    page = await _get_page(session, page_id)
    return Response(content=render_html(page.markdown), media_type="text/html; charset=utf-8")


# ---- Content management (CRUD) ----

@router.post("", response_model=PageRead, status_code=status.HTTP_201_CREATED)
async def create_page(
    payload: PageCreate,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_admin_token),
) -> Page:
    book = (
        await session.execute(select(Book).where(Book.id == payload.book_id))
    ).scalar_one_or_none()
    if book is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="book_id does not exist")
    base = payload.slug or slugify(payload.name)
    slug = await _unique_page_slug(session, payload.book_id, base)
    page = Page(
        book_id=payload.book_id,
        chapter_id=payload.chapter_id,
        name=payload.name,
        slug=slug,
        markdown=payload.markdown,
    )
    session.add(page)
    await session.commit()
    await session.refresh(page)
    return page


@router.put("/{page_id}", response_model=PageRead)
async def update_page(
    page_id: int,
    payload: PageUpdate,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_admin_token),
) -> Page:
    page = await _get_page(session, page_id)
    if payload.book_id is not None:
        page.book_id = payload.book_id
    if payload.chapter_id is not None:
        page.chapter_id = payload.chapter_id
    if payload.name is not None:
        page.name = payload.name
    if payload.markdown is not None:
        page.markdown = payload.markdown
    if payload.slug is not None:
        page.slug = await _unique_page_slug(
            session, page.book_id, payload.slug, exclude_id=page.id
        )
    await session.commit()
    await session.refresh(page)
    return page


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: int,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_admin_token),
) -> None:
    page = await _get_page(session, page_id)
    await session.delete(page)
    await session.commit()
