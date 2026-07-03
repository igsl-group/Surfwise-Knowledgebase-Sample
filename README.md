# SurfWise Knowledge Base — Sample & Integration Docs

Reference material for connecting an external DMS/CMS to SurfWise's knowledge base
so its content becomes searchable and usable by the SurfWise chat agent (via the
"Manage Connectors" GUI or a push integration).

## Contents
- [`docs/knowledge-base-connector-integration-guide.md`](docs/knowledge-base-connector-integration-guide.md)
  — integration guide for DMS/CMS vendors: architecture overview, the two integration
  paths (push via Documents API + PAT, or a native pull connector), the API contract to
  expose, item→document mapping, sync/dedup semantics, security, and a validation checklist.

## Reference implementation: `kb-service/`
A complete, runnable **SurfWise-compatible Knowledge Base** built with SurfWise's own
stack (FastAPI + async SQLAlchemy + asyncpg + PostgreSQL + Alembic + Docker). It exposes
a **BookStack-compatible API**, so SurfWise's native BookStack connector indexes it with
no SurfWise changes.

```bash
cd kb-service
docker compose up -d --build      # API on http://localhost:8090 (docs at /docs)
```
Connect from SurfWise → Manage Connectors → **BookStack**:
- Base URL: `http://host.docker.internal:8090` (same Docker host) or `http://<HOST_IP>:8090`
- Token ID / Secret: `kb_demo_token_id` / `kb_demo_token_secret`

Verified end-to-end: SurfWise's own `BookStackConnector` fetches pages, exports Markdown,
and supports incremental (`updated_at`) sync against this service. See
[`kb-service/README.md`](kb-service/README.md).
