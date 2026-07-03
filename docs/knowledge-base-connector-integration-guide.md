# SurfWise Knowledge Base Connector — Integration Guide for DMS/CMS Vendors

**Audience:** engineers of an existing Document/Content Management System (DMS/CMS)
who want their repository to appear as a connectable knowledge source inside
SurfWise ("Manage Connectors" / the "connect your connectors" surface in the
document list), so its content is searchable and usable by the SurfWise chat agent.

**Status:** implementation guide derived from the SurfWise codebase
(`github.com/igsl-group/SurfWise`, `develop`). Confirm exact request schemas
against your target instance's OpenAPI at `‹BASE_URL›/api/v1/openapi.json`.

---

## 1. How SurfWise ingests knowledge (architecture)

```
Source system ──► Connector (API client) ──► Indexer (Celery task) ──►
      KB-sync (map to Document) ──► chunk + embed ──► Documents + Chunks (pgvector)
                                                          └► hybrid search + chat agent
```

Key concepts:
- **Search space** — the tenant/workspace that owns documents and connectors. Every
  ingested document belongs to exactly one `search_space_id`.
- **Connector** (`search_source_connectors` row): `name`, `connector_type` (enum),
  `config` (JSON: endpoint URL + credentials), `is_indexable`, `periodic_indexing_enabled`,
  `indexing_frequency_minutes`, `last_indexed_at`, `search_space_id`, `user_id`.
- **Document** (`documents` row): `title`, `document_type` (enum), `content` (Markdown/plain
  text — the indexable body), `document_metadata` (JSON), `content_hash`,
  `unique_identifier_hash` (UNIQUE — stable per source item), `embedding`, `updated_at`,
  `search_space_id`, `connector_id`.
- **Chunks + embeddings** — SurfWise chunks `content` and stores vector embeddings
  (`create_document_chunks`) for hybrid semantic + keyword search.
- **Dedup / incremental** — two SHA-256 hashes:
  - `unique_identifier_hash = sha256("{DOCUMENT_TYPE}:{your_stable_item_id}:{search_space_id}")`
    → identifies "the same source item" across syncs (insert vs update).
  - `content_hash = sha256("{search_space_id}:{content}")`
    → if unchanged, the item is skipped (no re-embedding).

There are **two integration paths**. Pick based on how much you want to build.

| | Option A — **Push (Documents API)** | Option B — **Native pull connector** |
|---|---|---|
| Who calls whom | Your DMS → SurfWise (HTTP push) | SurfWise → Your DMS (polls your API) |
| SurfWise code change | None | Yes (add a connector type) |
| Appears in "Manage Connectors" GUI | No (documents just appear in the space) | **Yes** (native connect UI) |
| Best for | Quick availability, event-driven push on change | First-class product integration, scheduled sync |
| Effort on your side | Low | Medium (expose a clean read API) |

---

## 2. Option A — Push integration via the Documents API (fastest)

Your DMS pushes content into a SurfWise search space over authenticated HTTP.
No SurfWise code changes required.

### 2.1 Authentication — Personal Access Token (PAT)
1. A SurfWise user creates a PAT: `POST /api/v1/pats` (returns the token once).
2. Enable API access on the target search space (`api_access_enabled`).
3. Send the token on every request: `Authorization: Bearer <PAT>`.

### 2.2 Push documents
- `POST /api/v1/documents` — submit content items (JSON). The body carries a
  `document_type`, the `content` payload, and the target `search_space_id`.
- `POST /api/v1/documents/fileupload` — multipart upload of a file (Markdown, PDF,
  DOCX, …); SurfWise runs its ETL (text extraction / OCR / optional vision LLM) and
  indexes it. Good when you already have exportable files.

> Confirm the exact JSON fields for `DocumentsCreate` against
> `‹BASE_URL›/api/v1/openapi.json` (schema: `DocumentsCreate`). At minimum you supply
> the document type, the Markdown/text content, and the search space.

### 2.3 Updates & deletes (push)
- SurfWise dedups by `unique_identifier_hash`. To make updates land on the **same**
  document, always send a **stable, unique per-item identifier** (your DMS's item ID).
- Re-push an item when it changes; unchanged content is skipped via `content_hash`.
- For deletions, call the document delete API for the corresponding document, or
  reconcile periodically.

### 2.4 When to use
Event-driven DMS (you already emit "document created/updated/deleted" events) →
push on each event. Simplest path to "our content is searchable in SurfWise."

---

## 3. Option B — Native pull connector (first-class "Manage Connectors" experience)

This makes your DMS a selectable connector in the SurfWise GUI, with scheduled
incremental sync. It requires (a) a small **read API on your side** and (b) a
connector implementation **inside SurfWise** (contributed by you or SurfWise maintainers).

### 3.1 The contract your DMS must expose (normative)

Model it on SurfWise's proven **BookStack** connector. Provide a token-authenticated
REST API with three capabilities:

1. **Auth** — a header your API accepts, e.g. `Authorization: Token <id>:<secret>`
   or `Authorization: Bearer <token>`. Read-only scope is sufficient.

2. **List items (paginated, incremental)** — return item stubs with a stable ID and a
   last-modified timestamp; support filtering by an updated-since window so SurfWise
   can pull only what changed since `last_indexed_at`.
   ```
   GET /api/items?updated_after=<ISO8601>&offset=<n>&count=<n>
   → { "data": [ { "id": "1234", "title": "…", "updated_at": "2026-07-01T10:00:00Z",
                   "url": "https://dms/items/1234" }, … ],
       "total": 4200 }
   ```

3. **Fetch item content as Markdown (or clean text) + metadata**
   ```
   GET /api/items/{id}                → metadata (title, author, timestamps, url, tags…)
   GET /api/items/{id}/export/markdown → the item body as Markdown/plain text
   ```

Guidelines:
- **Stable IDs**: the item `id` must never change for the life of the item — it maps to
  `unique_identifier_hash`. If it changes, SurfWise will treat it as a new document.
- **Markdown preferred**: return clean Markdown (headings, lists, tables). Strip UI chrome.
  Plain text is acceptable. For binary docs, either pre-render to Markdown or expose a
  file download so SurfWise's ETL can extract it.
- **Incremental**: support `updated_after`/`updated_since`; include a reliable
  `updated_at` per item. This is what keeps large repositories cheap to sync.
- **Pagination**: stable ordering + offset/cursor + total count.
- **Permissions (optional but recommended)**: if your DMS is multi-tenant/ACL'd, scope
  results to what the connector's credential is allowed to read.

### 3.2 What gets implemented inside SurfWise (per connector)

For maintainers wiring your DMS in (mirrors every existing connector):
- **Enum values**: add `‹YOURDMS›_CONNECTOR` to `SearchSourceConnectorType` and a
  matching `DocumentType` (`app/db.py`).
- **Connector client**: `app/connectors/‹yourdms›_connector.py` — a class that calls
  your API (`set_credentials`, list, get-detail, export-markdown, get-by-date-range),
  with rate limiting and error handling. (See `bookstack_connector.py` as the template.)
- **Indexer task**: `app/tasks/connector_indexers/‹yourdms›_indexer.py` — iterate items
  (incrementally from `last_indexed_at`), fetch Markdown, compute
  `content_hash`/`unique_identifier_hash`, upsert `Document` via `create_document_chunks`,
  update `last_indexed_at`, emit progress logs. (See `bookstack_indexer.py`.)
- **Config validation + trigger**: extend `search_source_connectors_routes.py` to
  validate the `config` (e.g. `base_url`, `token_id`, `token_secret`) and dispatch the
  indexer task.
- **Frontend**: add the connector card/form to the "Manage Connectors" UI in
  `surfsense_web` (icon, display name, config fields, connect action).

### 3.3 Item → Document mapping
| SurfWise `Document` field | Source of value |
|---|---|
| `title` | item title |
| `content` | item body as Markdown/clean text |
| `document_type` | `DocumentType.‹YOURDMS›_CONNECTOR` |
| `document_metadata` | JSON: author, url, tags, source timestamps, item id |
| `unique_identifier_hash` | `generate_unique_identifier_hash(type, item_id, search_space_id)` |
| `content_hash` | `generate_content_hash(content, search_space_id)` |
| `updated_at` | item last-modified |
| `search_space_id` / `connector_id` | from the connector row |

---

## 4. Sync & data semantics (applies to both options)
- **Insert vs update** is decided by `unique_identifier_hash` (stable item id). Keep IDs stable.
- **No-op detection** via `content_hash` — unchanged bodies are skipped (no re-embed).
- **Incremental** — pull connectors use `last_indexed_at` + your `updated_after` filter;
  push integrations should send only changed items.
- **Deletions** — pull connectors should reconcile (items no longer returned can be
  retired); push integrations call the delete API.
- **Scheduling** — pull connectors support periodic indexing
  (`periodic_indexing_enabled` + `indexing_frequency_minutes`).

## 5. Content format guidance
- Prefer **Markdown**; keep one logical document per source item.
- Include a canonical **URL** back to the item in metadata (used for citations).
- Very large items: split at the source or rely on SurfWise chunking; avoid multi-MB
  single documents where possible.
- Binary/office files: expose a download so SurfWise ETL (text extraction, OCR, optional
  vision LLM) can process them, or pre-convert to Markdown.

## 6. Security
- Use a **dedicated, least-privilege, read-only** credential for the connector.
- Prefer per-tenant tokens; support rotation/revocation.
- SurfWise stores connector `config` (which may include tokens) server-side; OAuth-based
  connectors additionally encrypt tokens. Use HTTPS for your API.
- For push: treat the PAT as a secret; scope it to the intended search space.

## 7. Validation checklist
- [ ] Auth: a read-only token authenticates list + detail + export endpoints.
- [ ] List returns stable IDs, `updated_at`, and supports an `updated_after` filter + paging.
- [ ] Export returns clean Markdown/text; metadata includes a canonical URL.
- [ ] Re-running a sync with no source changes creates **zero** new documents (hash dedup).
- [ ] Editing one source item and re-syncing updates exactly **one** SurfWise document.
- [ ] Large repository: an incremental sync only transfers changed items.

## 8. Appendix — key references in the SurfWise codebase
- Connector template: `surfsense_backend/app/connectors/bookstack_connector.py`
- Indexer template: `surfsense_backend/app/tasks/connector_indexers/bookstack_indexer.py`
- Document mapping: `surfsense_backend/app/services/*/kb_sync_service.py`
- Hash helpers: `surfsense_backend/app/utils/document_converters.py`
  - `generate_content_hash(content, search_space_id)`
  - `generate_unique_identifier_hash(document_type, unique_identifier, search_space_id)`
- Connector CRUD + trigger: `surfsense_backend/app/routes/search_source_connectors_routes.py`
- Push API: `surfsense_backend/app/routes/documents_routes.py`
  (`POST /documents`, `POST /documents/fileupload`)
- PAT auth: `surfsense_backend/app/routes/personal_access_tokens_routes.py` (`POST /pats`),
  `app/users.py` (Bearer PAT).
- Enums: `SearchSourceConnectorType`, `DocumentType` in `surfsense_backend/app/db.py`.
