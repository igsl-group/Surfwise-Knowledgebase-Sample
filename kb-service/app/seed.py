"""Idempotent seed: default API token + sample knowledge-base content."""
import asyncio

from sqlalchemy import func, select

from app.config import get_settings
from app.database import async_session_maker
from app.markdown_utils import slugify
from app.models import ApiToken, Book, Page
from app.security import hash_secret

SAMPLE_BOOKS = [
    {
        "name": "Company Handbook",
        "description": "Policies, onboarding and how we work.",
        "pages": [
            {
                "name": "Onboarding Guide",
                "markdown": (
                    "## Welcome\n\n"
                    "This guide walks new hires through their first week.\n\n"
                    "1. Set up your accounts\n2. Read the security policy\n3. Meet your team\n\n"
                    "> Tip: ask questions early and often.\n"
                ),
            },
            {
                "name": "Security Policy",
                "markdown": (
                    "## Security Policy\n\n"
                    "All credentials must be stored in the company password manager.\n\n"
                    "- Enable MFA on every account\n- Never share API tokens\n- Report incidents within 24h\n"
                ),
            },
            {
                "name": "Leave and Time Off",
                "markdown": (
                    "## Leave Policy\n\n"
                    "Employees accrue 1.75 days of paid leave per month.\n\n"
                    "Submit requests at least **two weeks** in advance.\n"
                ),
            },
        ],
    },
    {
        "name": "Product Documentation",
        "description": "How the product works and how to integrate.",
        "pages": [
            {
                "name": "Getting Started",
                "markdown": (
                    "## Getting Started\n\n"
                    "Install the CLI and authenticate:\n\n"
                    "```bash\npip install ourtool\nourtool login\n```\n\n"
                    "You are ready to go.\n"
                ),
            },
            {
                "name": "REST API Reference",
                "markdown": (
                    "## REST API\n\n"
                    "The API is versioned under `/api/v1`.\n\n"
                    "| Method | Path | Description |\n"
                    "|---|---|---|\n"
                    "| GET | /items | List items |\n"
                    "| POST | /items | Create an item |\n"
                ),
            },
        ],
    },
]


async def seed() -> None:
    settings = get_settings()
    async with async_session_maker() as session:
        token = (
            await session.execute(
                select(ApiToken).where(ApiToken.token_id == settings.default_token_id)
            )
        ).scalar_one_or_none()
        if token is None:
            session.add(
                ApiToken(
                    name=settings.default_token_name,
                    token_id=settings.default_token_id,
                    secret_hash=hash_secret(settings.default_token_secret),
                )
            )

        book_count = (await session.execute(select(func.count(Book.id)))).scalar_one()
        if book_count == 0:
            for b in SAMPLE_BOOKS:
                book = Book(
                    name=b["name"], slug=slugify(b["name"]), description=b["description"]
                )
                session.add(book)
                await session.flush()
                for p in b["pages"]:
                    session.add(
                        Page(
                            book_id=book.id,
                            name=p["name"],
                            slug=slugify(p["name"]),
                            markdown=p["markdown"],
                        )
                    )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
