from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BookCreate(BaseModel):
    name: str
    description: str = ""
    slug: str | None = None


class BookUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    slug: str | None = None


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    description: str
    created_at: datetime
    updated_at: datetime


class PageCreate(BaseModel):
    book_id: int
    name: str
    markdown: str = ""
    slug: str | None = None
    chapter_id: int | None = None


class PageUpdate(BaseModel):
    name: str | None = None
    markdown: str | None = None
    slug: str | None = None
    book_id: int | None = None
    chapter_id: int | None = None


class PageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    book_id: int
    chapter_id: int | None
    name: str
    slug: str
    markdown: str
    created_at: datetime
    updated_at: datetime
