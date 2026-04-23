# Aidbox Documentation Index

Quick reference for the most-used doc pages. Fetch any page with:
```bash
bash .claude/commands/aidbox/scripts/fetch-doc.sh <path>
```

## Database & Storage
- `database/overview` — Table schema (id, txid, ts, cts, status, resource JSONB), two-table pattern, direct SQL
- `database/database-schema` — Detailed column descriptions, history tables
- `database/postgresql-extensions` — Required (pg_trgm, unaccent) and optional (fuzzystrmatch, postgis) extensions

## API
- `api/api-overview` — API overview (REST, SQL, GraphQL, Bulk, Subscriptions)
- `api/rest-api/crud` — FHIR CRUD operations
- `api/rest-api/crud/patch` — PATCH operations (also works in Bundles)
- `api/rest-api/fhir-search` — FHIR search parameters
- `api/rest-api/fhir-search/searchparameter` — Custom SearchParameters, _count, _page
- `api/rest-api/fhir-search/include-and-revinclude` — _include, _revinclude
- `api/rest-api/history` — Resource version history
- `api/batch-transaction` — FHIR Bundle transactions
- `api/graphql-api` — GraphQL API
- `api/bulk-api` — Bulk operations overview
- `api/bulk-api/import-and-fhir-import` — Bulk import ($import)
- `api/bulk-api/export` — Bulk export ($export)

## Other APIs
- `api/other/changes-api` — Delta tracking via txid (polling, 304 if unchanged)
- `api/other/etag-support` — ETag caching based on txid, transaction_id_seq
- `api/other/batch-upsert` — Simple PUT / with resource array
- `api/other/sequence-api` — PostgreSQL sequences via REST
- `api/other/rpc-api` — JSON-RPC endpoint
- `api/other/cache` — Cache management

## SQL on FHIR
- `modules/sql-on-fhir` — Overview, ViewDefinition concept
- `modules/sql-on-fhir/defining-flat-views-with-view-definitions` — How to write ViewDefinitions
- `modules/sql-on-fhir/query-data-from-flat-views` — Querying materialized views
- `modules/sql-on-fhir/operation-materialize` — $materialize (table/view/materialized-view)
- `modules/sql-on-fhir/reference` — FHIRPath expressions, column definitions

## Subscriptions & Events
- `modules/topic-based-subscriptions` — Overview (FHIR, Aidbox, deprecated)
- `modules/topic-based-subscriptions/aidbox-topic-based-subscriptions` — Aidbox subscriptions (Kafka, Webhook, etc.)
- `modules/other-modules/aidbox-trigger` — AidboxTrigger: SQL on FHIR CRUD (v2505+, alpha)

## Integration
- `modules/integration-toolkit/mappings` — JUTE-based data mappings
- `modules/mdm` — Master Data Management (patient dedup, probabilistic matching)
- `modules/other-modules/mcp` — MCP server for LLM access (v2505+, alpha)

## Access Control
- `access-control/authorization/access-policies` — AccessPolicy engine
- `access-control/authorization/scoped-api/organization-based-hierarchical-access-control` — Org-based access
- `access-control/authentication/oauth-2-0` — OAuth 2.0

## Configuration
- `configuration/recommended-envs` — Recommended environment variables
- `configuration/settings` — Aidbox settings
- `reference/all-settings` — Complete settings reference

## Profiling & Validation
- `modules/profiling-and-validation/fhir-schema-validator` — FHIR Schema validation
- `modules/profiling-and-validation/fhir-ig` — Implementation Guides
