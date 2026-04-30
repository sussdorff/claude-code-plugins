---
name: mira-aidbox
description: "Mira-specific Aidbox configuration, infrastructure, billing catalogs, flat tables, IG testing, and accumulated learnings. Supplements the samurai-skills plugin with mira-project-specific content. MUST USE whenever: (1) connecting to mira's Aidbox instance (URLs, auth, infrastructure), (2) working with mira's billing catalogs (EBM/GOA/HZV), (3) working with mira's flat tables or AidboxTriggers, (4) testing mira's FHIR IGs (fhir-praxis-de, fhir-dental-de), (5) working with mira's ETL pipelines or seed data, (6) querying mira's ViewDefinitions or $materialize setup. Also triggers on generic aidbox usage to supplement the upstream samurai-skills plugin with mira-specific context."
requires_standards: [healthcare-control-areas, english-only]
---

# Mira Aidbox

> This skill contains mira-project-specific Aidbox configuration. For general Aidbox/FHIR reference, see the samurai-skills plugin.

Single reference for mira-specific Aidbox configuration, infrastructure, and operational knowledge.

## Routing

| You need... | Read |
|---|---|
| Connection URLs, infrastructure, quick commands | `references/connection.md` |
| Billing catalogs (EBM/GOA/HZV), ETL, seed scripts | `references/billing-catalogs.md` |
| Flat tables, ViewDefinitions, $materialize, sync | `references/flat-tables.md` |
| FHIR resources — mira-specific patterns, ETL load order | `references/fhir-resources.md` |
| Install IG into Aidbox (`install-ig`) | `references/ig-install.md` |
| Test CodeSystems/ValueSets (`test-cs`, `test-vs`) | `references/ig-terminology.md` |
| Validate profiles (`test-profile`, `$validate`) | `references/ig-profiles.md` |
| QA review, report interpretation, fix patterns | `references/ig-qa.md` |
| Find an Aidbox doc page | `references/doc-index.md` + scripts below |

## Searching Aidbox Documentation

Aidbox docs are JS-rendered — `WebFetch` and `crwl` return only navigation HTML, not content. Use these methods:

### Fetch a specific page

Append `.md` to any doc URL for plain markdown:
```bash
curl -sL "https://www.health-samurai.io/docs/aidbox/<path>.md"
```

### Search by keyword

```bash
# Build index + search URLs (cached 1 day)
bash <skill-dir>/scripts/search-docs.sh <keyword>

# Also grep page content
bash <skill-dir>/scripts/search-docs.sh <keyword> --fetch
```

### Page index

See `references/doc-index.md` for curated paths to key documentation pages.

## Mira-Specific Learnings

These prevent repeated mistakes specific to the mira deployment.

### ALWAYS use /fhir base — aidbox-format endpoint is obsolete

**Rule**: ALL Aidbox API calls from adapter code MUST use the `/fhir` base path.
The aidbox-format endpoint (`/`) is becoming obsolete per Health Samurai and has
resource-specific bugs that will NOT be fixed there.

**Verified broken on Aidbox 2602.3 (2026-04-14)**:
- `POST /AidboxTopicDestination` with a `header` parameter → **422 NPE**
  `Cannot invoke "java.lang.CharSequence.length()" because "this.text" is null`
- `POST /fhir/AidboxTopicDestination` with `header` parameter → **201 Created** (works)

**Env var semantics** (mira-adapters):
- `AIDBOX_BASE_URL` = root without `/fhir` (e.g. `http://localhost:8080`)
- `AIDBOX_FHIR_URL` = convenience alias = `AIDBOX_BASE_URL + /fhir` — for tooling only
- `AidboxClient` always appends `/fhir/` per method — never call `AIDBOX_BASE_URL` directly

**Prior bad assumption (bead mira-adapters-lnut, reversed in mira-adapters-xzjk)**:
The lnut bead routed `AidboxTopicDestination` to the admin path (`/AidboxTopicDestination/{id}`)
due to a misread 405 error. The 405 was PUT-only on the aidbox-format path; POST on `/fhir` works
fine. The lnut workaround was reverted in bead mira-adapters-xzjk.

**Admin-only resources** (genuinely not on /fhir — stay on admin path):
- `Client` (OAuth2 clients) → `PUT /{id}` via `putAdmin()`
- `AccessPolicy` → `PUT /{id}` via `putAdmin()`
- `$sql` → `POST /$sql` (special endpoint, not a FHIR resource)
- `BulkImportStatus` → `GET /BulkImportStatus/{id}` (Aidbox-internal, not FHIR)

### AidboxTrigger setup (mira flat tables)

SQL execution on FHIR CRUD, in-transaction:
```json
{
  "resourceType": "AidboxTrigger",
  "action": ["create", "update", "delete"],
  "resource": "Encounter",
  "sql": "INSERT INTO mira_backend.encounter_flat ... ON CONFLICT (id) DO UPDATE ..."
}
```
Only INSERT/UPDATE/DELETE SQL. `{{id}}` template substitution. Requires FHIR Schema mode.

### $materialize in mira

`$materialize` with `type=table` drops the entire table and rebuilds. 33M-row table on MCN production means >5min downtime.

**Never use in production for large tables.** Only for initial bootstrap (empty DB). See `references/flat-tables.md` for the production sync architecture.

### Mira infrastructure notes

- **Two instances exist**: `ignis.cognovis.de` (old) and `mira.cognovis.de` (production). Always use mira.
- **Seed data NOT auto-loaded**: `aidbox/seed/` volume is not auto-imported. Use `bun run seed:catalogs`.
- **413 via Caddy/nginx**: Large files (>10MB) may be rejected. Load via docker network directly.
- **GOA batch duplicate**: 1 duplicate ID causes 1 error per load — harmless (2,337/2,338 succeed).
- **ConceptMap in transaction**: Aidbox refuses PUT for existing ConceptMaps in transaction bundles. Use batch.
