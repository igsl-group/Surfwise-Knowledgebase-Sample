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
- API token management (`/api/tokens`): create / list / rotate / delete, with **admin vs
  read-only** scopes (give SurfWise a read-only token)
- Document **upload / download / delete** + web GUI (`/ui`, HTTP Basic protected) with
  menu views, a modal document viewer, and paginated lists
- Hardening: sanitized Markdown (XSS-safe), constant-time token compare, upload size
  cap, and a DB-backed `/health` probe

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

> Recommended: create a dedicated **read-only** token (GUI **API Tokens** tab, leave *admin* unchecked) for the connector.

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
| `KB_UI_USERNAME` / `KB_UI_PASSWORD` | `admin` / `surfwise-kb-admin` | HTTP Basic login for the `/ui` admin console |
| `KB_MAX_UPLOAD_MB` | `50` | Max size (MB) per uploaded document |
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

Create a read-only API token for the SurfWise connector:
```bash
curl -X POST localhost:8090/api/tokens -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"name":"surfwise-connector","is_admin":false}'   # returns token_id + secret (once)
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
│   ├── routers/           # health, books, pages, documents, tokens, ui, manual
│   └── manual.py          # admin connection guide (served at /manual)
├── migrations/            # Alembic: 0001_init, 0002_document_files, 0003_token_admin
├── tests/                 # pytest: BookStack contract, CRUD, documents, tokens, authz
├── Dockerfile, docker-compose.yml, entrypoint.sh
└── pyproject.toml, .env.example
```

## Security model
- **API auth**: `Authorization: Token <id>:<secret>`; secrets stored SHA-256-hashed,
  compared in constant time.
- **Scopes**: admin tokens may read + write + manage tokens; **read-only** tokens can
  only read (recommended for the SurfWise connector). Writes return 403 for read-only.
- **Admin UI**: `/ui` is gated by HTTP Basic (`KB_UI_USERNAME`/`KB_UI_PASSWORD`).
- **XSS**: Markdown is rendered then sanitized (allowlist) before display.
- **Limits**: per-file upload cap (`KB_MAX_UPLOAD_MB`); safe `Content-Disposition` for
  non-ASCII filenames.
- For production: serve over **HTTPS**, replace the demo token/UI password, and consider
  object storage for large files.

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
