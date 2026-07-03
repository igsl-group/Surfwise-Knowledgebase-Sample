"""Admin user manual (Markdown) served at /manual and shipped in the repo docs."""

MANUAL_MD = """# Connect this Knowledge Base to SurfWise - Admin Guide

This Knowledge Base exposes a **BookStack-compatible API**, so SurfWise's built-in
**BookStack connector** can index it with no changes to SurfWise. Follow the steps below.

## 1. What you need
- A SurfWise account that can add connectors in a **Search Space**.
- This KB's **Base URL** (reachable from the SurfWise backend), e.g. `http://<KB_HOST>:8090`.
- An **API token** for this KB: a Token ID and Token Secret.

## 2. Get the Base URL and token
**Base URL** - the address of this service as seen from the SurfWise server:
- Same Docker host as SurfWise: `http://host.docker.internal:8090`
- Different machine: `http://<KB_HOST_IP>:8090` (must be reachable from the SurfWise backend)

**Token** - use the demo token for testing, or create a dedicated one:
- Demo Token ID: `kb_demo_token_id`
- Demo Token Secret: `kb_demo_token_secret`

Quick reachability test (run from the SurfWise server):
```
curl -H "Authorization: Token <TOKEN_ID>:<TOKEN_SECRET>" http://<KB_HOST>:8090/api/pages
```
A JSON list of pages confirms connectivity and the token.

## 3. Add the connector in SurfWise
1. Log in to SurfWise and open your **Search Space**.
2. Open **Manage Connectors** (or **Connect your connectors** from the document list).
3. Choose **BookStack**.
4. Enter:
   - **Base URL**: `http://<KB_HOST>:8090`
   - **API Token ID**: your Token ID
   - **API Token Secret**: your Token Secret
5. **Save**.

## 4. Index the content
- Click **Index now** to start. SurfWise pulls all pages, exports each as Markdown,
  then chunks and embeds them for search.
- (Optional) Enable **periodic indexing** for automatic, ongoing sync.

## 5. How syncing works
- Each document has an `updated_at` timestamp. SurfWise re-indexes only what changed
  (incremental sync), so large libraries stay cheap to keep current.
- Editing a page or uploading a new file updates its timestamp and will be picked up
  on the next index.

## 6. Verify
- In SurfWise, search for something you know is in the KB. It should appear and be
  usable by the agent, with citations linking back to the source page.

## 7. Manage the KB content
- **Documents GUI**: open `http://<KB_HOST>:8090/ui` to upload / download / delete
  documents and browse books and pages.
- **API docs**: `http://<KB_HOST>:8090/docs` (interactive Swagger UI).

## Troubleshooting
| Symptom | Fix |
|---|---|
| Connector cannot reach the KB | Confirm the Base URL is reachable from the SurfWise **backend** (network/firewall/Tailscale). Use the curl test above. |
| 401 Unauthorized | Re-check the Token ID and Secret. |
| Nothing gets indexed | Confirm the KB has pages (open `/ui`) and the token is valid. |
| A document is missing | Re-run indexing; brand-new uploads are picked up on the next sync. |

## Notes for production
- Replace the demo token with a dedicated API token.
- Serve the KB over **HTTPS** (e.g., behind a reverse proxy) for secure access.
"""
