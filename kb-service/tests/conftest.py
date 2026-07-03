import os

os.environ["KB_SEED_ON_STARTUP"] = "false"
os.environ["KB_DATABASE_URL"] = "sqlite+aiosqlite://"

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_session
from app.main import app
from app.security import hash_secret

TOKEN_ID = "testid"
TOKEN_SECRET = "testsecret"
AUTH = {"Authorization": f"Token {TOKEN_ID}:{TOKEN_SECRET}"}


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with maker() as s:
        s.add(
            models.ApiToken(
                name="test", token_id=TOKEN_ID, secret_hash=hash_secret(TOKEN_SECRET)
            )
        )
        book = models.Book(name="Handbook", slug="handbook", description="d")
        s.add(book)
        await s.flush()
        s.add(
            models.Page(
                book_id=book.id,
                name="Onboarding",
                slug="onboarding",
                markdown="# Onboarding\n\nHello world",
            )
        )
        await s.commit()

    async def _override():
        async with maker() as s:
            yield s

    app.dependency_overrides[get_session] = _override
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()
