import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.routers import books, health, pages

settings = get_settings()
logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger("kb")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.seed_on_startup:
        try:
            from app.seed import seed

            await seed()
            logger.info("Seed complete.")
        except Exception as exc:  # noqa: BLE001 - startup should not crash on seed
            logger.warning("Seed skipped/failed: %s", exc)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "A SurfWise-compatible Knowledge Base. Exposes a BookStack-compatible API "
        "so SurfWise's native BookStack connector can index it, plus CRUD for content."
    ),
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(books.router)
app.include_router(pages.router)


@app.get("/", tags=["system"])
async def root() -> dict:
    return {"service": settings.app_name, "docs": "/docs", "health": "/health"}
