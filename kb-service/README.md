# SurfWise-Compatible Knowledge Base (reference service)

A small but production-grade Knowledge Base that **SurfWise can connect to and index
out of the box**. It exposes a **BookStack-compatible API**, so you point SurfWise's
native **BookStack connector** at this service — no SurfWise code changes required.

Built with the same stack as SurfWise: **FastAPI + async SQLAlchemy 2.0 + asyncpg +
PostgreSQL + Alembic + Docker**.

## Why BookStack-compatible?
SurfWise ships a native BookStack connector (Option B — native pull connector). By
implementing the exact endpoints/auth that connector calls, any DMS/CMS becomes
connectable immediately. This service is a working reference of that contract.

## Features
- BookStack-compatible read API consumed by the SurfWise connector:
  - `GET /api/pages?count=&offset=&filter[updated_at:gt]=&sort=-updated_at` → `{ data, total }`
  - `GET /api/pages/{id}` (detail incl. rendered `html` + `markdown`)
  - `GET /api/pages/{id}/export/markdown` (raw Markdown — used for indexing)
  - `GET /api/books` and `GET /api/books/{id}` (with `contents`)
- Full content management CRUD: `POST/PUT/DELETE /api/books` and `/api/pages`
- Token auth (`Authorization: Token <id>:<secret>`), tokens hashed at rest
- Incremental sync support via `filter[updated_at:gt]` (drives SurfWise re-indexing)
- Alembic migrations, seed data, health check, OpenAPI docs at `/docs`

## Quick start
```bash
cp .env.example .env          # optional: customize token / URLs
docker compose up -d --build
# API on http://localhost:8090  (docs at /docs)
```
On first boot it runs migrations and seeds a demo API token plus sample content.

## Connect from SurfWise (Manage Connectors)
Add a **BookStack** connector in a SurfWise search space with:
- **Base URL**: this service's URL reachable from the SurfWise backend
  (e.g. `http://host.docker.internal:8090` when both run on the same Docker host,
  or `http://<HOST_IP>:8090`)
- **Token ID**: `KB_DEFAULT_TOKEN_ID` (default `kb_demo_token_id`)
- **Token Secret**: `KB_DEFAULT_TOKEN_SECRET` (default `kb_demo_token_secret`)

Trigger indexing; SurfWise pulls pages, exports each as Markdown, chunks + embeds them,
and they become searchable/usable by the SurfWise agent. Editing a page bumps its
`updated_at`, so incremental re-index picks up only changes.

## Configuration (env, prefix `KB_`)
| Var | Default | Purpose |
|---|---|---|
| `KB_DATABASE_URL` | `postgresql+asyncpg://kb:kb@db:5432/kb` | Async DB URL |
| `KB_DEFAULT_TOKEN_ID` / `KB_DEFAULT_TOKEN_SECRET` | demo values | Seeded API token |
| `KB_PUBLIC_BASE_URL` | `http://localhost:8090` | Human-facing base URL |
| `KB_SEED_ON_STARTUP` | `true` | Seed token + sample content on boot |
| `KB_HOST_PORT` (compose) | `8090` | Host port mapping |

## Content management API (examples)
```bash
AUTH='Authorization: Token kb_demo_token_id:kb_demo_token_secret'
# create a book
curl -X POST localhost:8090/api/books -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"name":"Runbooks","description":"Ops docs"}'
# create a page (Markdown body)
curl -X POST localhost:8090/api/pages -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"book_id":1,"name":"Restart Service","markdown":"# Restart\n\n..."}'
```

## Tests
```bash
pip install -e ".[dev]"     # or: pip install pytest pytest-asyncio httpx aiosqlite + deps
pytest -q                    # runs against in-memory SQLite (no Postgres needed)
```

## Project layout
```
kb-service/
├── app/
│   ├── config.py          # settings (env KB_*)
│   ├── database.py        # async engine/session + Base
│   ├── models.py          # Book, Page, ApiToken
│   ├── schemas.py         # Pydantic CRUD models
│   ├── security.py        # Token auth (id:secret, hashed)
│   ├── markdown_utils.py  # slugify + Markdown->HTML
│   ├── seed.py            # default token + sample content
│   ├── main.py            # FastAPI app
│   └── routers/           # health, books, pages (BookStack-compat + CRUD)
├── migrations/            # Alembic (async env) + 0001_init
├── tests/                 # pytest (BookStack contract + CRUD)
├── Dockerfile, docker-compose.yml, entrypoint.sh
└── pyproject.toml, .env.example
```

## Notes for adapting your own DMS/CMS
This service is a reference. To make an existing DMS/CMS connectable, expose the same
read contract (token auth; paginated + `updated_at`-filterable list with stable IDs;
Markdown export per item). See the integration guide in `../docs/`.

## Document management + Web GUI
Beyond page CRUD, the service supports file **upload / download / delete** with a
built-in web GUI (no extra service):

- **GUI**: open `http://<host>:8090/ui` — enter the API token (demo token pre-filled),
  pick/create a book, upload files, then View / Download / Delete documents.
- **API**:
  - `POST /api/documents/upload` (multipart: `file`, `book_id`, optional `name`)
  - `GET /api/documents` (list with file metadata)
  - `GET /api/documents/{id}/download` (original bytes, or Markdown for page-only docs)
  - `DELETE /api/documents/{id}`

Uploaded text files (`.md/.txt/.csv/...`) have their content stored as the page
Markdown, so they are immediately indexable by SurfWise via the BookStack API; binary
files are stored for download with an indexable placeholder note.
