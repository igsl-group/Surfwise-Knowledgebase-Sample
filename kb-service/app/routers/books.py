from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.markdown_utils import slugify
from app.models import ApiToken, Book
from app.routers._serializers import book_stub, page_stub
from app.schemas import BookCreate, BookRead, BookUpdate
from app.security import require_token

router = APIRouter(prefix="/api/books", tags=["books"])


async def _get_book(session: AsyncSession, book_id: int) -> Book:
    book = (
        await session.execute(select(Book).where(Book.id == book_id))
    ).scalar_one_or_none()
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


@router.get("")
async def list_books(
    count: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> dict:
    total = (await session.execute(select(func.count(Book.id)))).scalar_one()
    rows = (
        await session.execute(
            select(Book).order_by(Book.id).offset(offset).limit(min(count, 500))
        )
    ).scalars().all()
    return {"data": [book_stub(b) for b in rows], "total": total}


@router.get("/{book_id}")
async def get_book(
    book_id: int,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> dict:
    book = await _get_book(session, book_id)
    pages = (
        await session.execute(select(Book).where(Book.id == book_id))
    ).scalar_one()
    data = book_stub(book)
    data["contents"] = [{**page_stub(p), "type": "page"} for p in pages.pages]
    return data


@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED)
async def create_book(
    payload: BookCreate,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> Book:
    book = Book(
        name=payload.name,
        description=payload.description,
        slug=payload.slug or slugify(payload.name),
    )
    session.add(book)
    await session.commit()
    await session.refresh(book)
    return book


@router.put("/{book_id}", response_model=BookRead)
async def update_book(
    book_id: int,
    payload: BookUpdate,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> Book:
    book = await _get_book(session, book_id)
    if payload.name is not None:
        book.name = payload.name
    if payload.description is not None:
        book.description = payload.description
    if payload.slug is not None:
        book.slug = payload.slug
    await session.commit()
    await session.refresh(book)
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    session: AsyncSession = Depends(get_session),
    _: ApiToken = Depends(require_token),
) -> None:
    book = await _get_book(session, book_id)
    await session.delete(book)
    await session.commit()
