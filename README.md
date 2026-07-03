# SurfWise Knowledge Base — Sample & Integration Docs

Reference material for connecting an external DMS/CMS to SurfWise's knowledge base
so its content becomes searchable and usable by the SurfWise chat agent (via the
"Manage Connectors" GUI or a push integration).

## Contents
- [`docs/knowledge-base-connector-integration-guide.md`](docs/knowledge-base-connector-integration-guide.md)
  — integration guide for DMS/CMS vendors: architecture overview, the two integration
  paths (push via Documents API + PAT, or a native pull connector), the API contract to
  expose, item→document mapping, sync/dedup semantics, security, and a validation checklist.
