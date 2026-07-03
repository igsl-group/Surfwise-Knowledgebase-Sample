import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.routers import books, documents, health, pages, tokens, ui

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
        except Exception as exc:  # noqa: BLE001
            logger.warning("Seed skipped/failed: %s", exc)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description=(
        "A SurfWise-compatible Knowledge Base. BookStack-compatible API so SurfWise's "
        "native connector can index it, plus content CRUD and a document-management GUI."
    ),
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(books.router)
app.include_router(pages.router)
app.include_router(documents.router)
app.include_router(tokens.router)
app.include_router(ui.router)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/ui")
