# SurfWise Knowledge Base — Sample, Reference Service & Docs

This repository shows how to make an external **DMS/CMS** connectable to **SurfWise**
so its content becomes searchable and usable by the SurfWise chat agent. It contains:

1. **`kb-service/`** — a complete, runnable, production-grade **SurfWise-compatible
   Knowledge Base** (FastAPI + async SQLAlchemy + PostgreSQL + Alembic + Docker) with a
   document-management **web GUI**. It exposes a **BookStack-compatible API**, so
   SurfWise's built-in BookStack connector indexes it **with no changes to SurfWise**.
2. **`docs/`** — an integration guide for DMS/CMS vendors and an admin guide for
   connecting the KB to SurfWise.

---

## Live demo instance (for testing/study)
A running instance is available on the internal demo host:

| Resource | URL |
|---|---|
| Document GUI (upload / download / delete) | http://100.106.109.59:8090/ui |
| API docs (interactive Swagger) | http://100.106.109.59:8090/docs |
| Admin guide: connect to SurfWise | http://100.106.109.59:8090/manual |
| Health check | http://100.106.109.59:8090/health |

**Demo API token** (BookStack-style `Authorization: Token <id>:<secret>`):
`kb_demo_token_id` / `kb_demo_token_secret`

> The demo host is on an internal/Tailscale network. Served over plain HTTP (demo only);
> use HTTPS + a dedicated token for real deployments.

---

## Run it yourself (Docker)
```bash
git clone https://github.com/igsl-group/Surfwise-Knowledgebase-Sample.git
cd Surfwise-Knowledgebase-Sample/kb-service
docker compose up -d --build
# GUI:   http://localhost:8090/ui
# Docs:  http://localhost:8090/docs
# Guide: http://localhost:8090/manual
```
First boot runs DB migrations and seeds a demo API token + sample content.
Set a different host port with `KB_HOST_PORT=9000 docker compose up -d`.

## What the KB service provides
- **Document management GUI** (`/ui`): create books, upload files, view rendered
  Markdown, download (with progress + original filenames incl. non-ASCII/CJK), delete.
- **BookStack-compatible connector API** (what SurfWise indexes):
  `GET /api/pages` (paginated, `filter[updated_at:gt]`, `sort`), `GET /api/pages/{id}`,
  `GET /api/pages/{id}/export/markdown`, `GET /api/books/{id}`.
- **Content CRUD & documents API**: `POST/PUT/DELETE /api/books` and `/api/pages`;
  `POST /api/documents/upload`, `GET /api/documents`, `GET /api/documents/{id}/download`.
- Token auth (hashed at rest), Alembic migrations, seed data, pytest suite, OpenAPI.

## Connect it to SurfWise (summary)
In a SurfWise Search Space → **Manage Connectors → BookStack**:
- **Base URL**: `http://host.docker.internal:8090` (same Docker host as SurfWise) or
  `http://<KB_HOST>:8090` (must be reachable from the SurfWise backend)
- **Token ID / Secret**: as above

Then **Index now** (optionally enable periodic indexing). Full walkthrough:
[`docs/connect-surfwise-admin-guide.md`](docs/connect-surfwise-admin-guide.md)
(also served live at `/manual`).

Verified end-to-end: SurfWise's own `BookStackConnector` fetches pages, exports
Markdown, and performs incremental (`updated_at`) sync against this service.

## Repository layout
```
.
├── docs/
│   ├── knowledge-base-connector-integration-guide.md   # for DMS/CMS vendors
│   └── connect-surfwise-admin-guide.md                 # for SurfWise admins
└── kb-service/                                          # runnable reference KB
    ├── app/                 # FastAPI app (routers, models, auth, GUI, manual)
    ├── migrations/          # Alembic migrations
    ├── tests/               # pytest (BookStack contract + CRUD + documents)
    ├── Dockerfile, docker-compose.yml, entrypoint.sh
    └── README.md            # service-level details
```

## Tests
```bash
cd kb-service
python -m venv .venv && . .venv/bin/activate
pip install fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg alembic \
            pydantic pydantic-settings markdown python-slugify python-multipart \
            pytest pytest-asyncio httpx aiosqlite
pytest -q     # runs against in-memory SQLite; no Postgres needed
```

## Docs
- **DMS/CMS integration guide** — [`docs/knowledge-base-connector-integration-guide.md`](docs/knowledge-base-connector-integration-guide.md)
- **Admin connection guide** — [`docs/connect-surfwise-admin-guide.md`](docs/connect-surfwise-admin-guide.md)
- **Service details** — [`kb-service/README.md`](kb-service/README.md)
