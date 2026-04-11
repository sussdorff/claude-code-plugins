# Flat Tables Architecture

## Overview

Flat tables in `mira_backend` schema denormalize FHIR JSONB resources into queryable SQL columns.
Used by billing proposals, tagesprotokoll, dashboard queries, and reporting.

## CRITICAL: Tables, NOT Materialized Views

Flat tables MUST be materialized as `type=table`, NEVER as `materialized-view`.

**Why:** AidboxTriggers keep flat tables in sync via `INSERT ... ON CONFLICT (id) DO UPDATE` (UPSERT).
Materialized views don't support INSERT/UPDATE — triggers silently fail, flat tables go stale.

**Rules:**
- `infra/viewdefinitions/*.json` → extension `"valueCode": "table"`
- `infra/setup-viewdefinitions.sh` → `$materialize` with `"valueCode":"table"`
- `$materialize` does DROP + full REBUILD — only for initial bootstrap (empty DB), never in production
- NEVER change back to `materialized-view` — this breaks real-time sync

## Real-Time Sync via AidboxTrigger

14 AidboxTriggers (7 resource types × upsert + delete) fire SQL in the SAME PostgreSQL
transaction as every FHIR write. Registered at API startup (`src/bootstrap.ts`).

- FHIR PUT/POST → trigger UPSERT → flat table row created/updated atomically
- FHIR DELETE → trigger DELETE → flat table row removed atomically
- No polling, no background jobs, no race conditions
- Trigger IDs: `mira-flat-<resource>-upsert`, `mira-flat-<resource>-delete`

### Code
- Trigger definitions: `src/lib/aidbox-triggers.ts` → `buildTriggerDefinitions()`
- SQL generation: `src/lib/viewdefinition-parser.ts` → `generateUpsertSql()`
- Registration: `src/bootstrap.ts` (calls `registerTriggers()`)
- Maintenance mode: `src/lib/maintenance-mode.ts` (deregister/re-register)

## Tables

| Table | Source | Key columns |
|-------|--------|-------------|
| `encounter_flat` | Encounter | id, period_start, subject_id, service_provider_id, participant_id, participant_display |
| `chargeitem_flat` | ChargeItem | id, status, code, code_display, code_system, encounter_id, subject_id, price_value |
| `condition_flat` | Condition | id, code, code_display, category_code, encounter_id, subject_id |
| `procedure_flat` | Procedure | id, code, encounter_id, subject_id, status |
| `servicerequest_flat` | ServiceRequest | id, encounter_id, category_code, code_display, status |
| `medicationrequest_flat` | MedicationRequest | id, encounter_id, medication_display, status |
| `auditevent_flat` | AuditEvent | id, type_code, entity_id, agent_id, batch_id, operation_type |
| `quarterly_revenue` | Computed | quartal, service_provider_id, participant_id, revenue, chargeitem_count |

## Data Sizes (MCN production, March 2026)

- `encounter_flat`: ~4.2M rows
- `chargeitem_flat`: ~33.7M rows
- `condition_flat`: ~25.4M rows
- `medicationrequest_flat`: ~35K rows

## ViewDefinitions

Located in `infra/viewdefinitions/*.json`. Registered in Aidbox at bootstrap.
Format: Aidbox-specific (name, resource, select with FHIRPath columns).

**Important**: ViewDefinitions do NOT support cross-resource joins. Each VD flattens one
resource type. Display names (e.g. `subject.display`, `participant.display`) come from the
FHIR Reference `.display` field — set by the PVS adapter at import time.
Never invent custom properties like `resolveDisplay` — Aidbox will reject them.

## Changes API (after bulk sync)

After bulk PVS-Sync, use Changes API to catch up flat tables:
`GET /<ResourceType>/$changes?version=$last_version&omit-resources=true`
→ get changed IDs → UPSERT only those rows → update last_version.

Code: `src/lib/aidbox-triggers.ts` → `buildChangesUrl()`, `parseChangesResponse()`

## Setup

Bootstrap (empty DB): `bash infra/setup-viewdefinitions.sh`
- Creates ViewDefinitions in Aidbox
- Runs `$materialize` with `type=table` (DROP + full rebuild)
- Creates UNIQUE indexes on `id` (required for trigger UPSERT)
- Creates secondary indexes for query performance

API restart: triggers are re-registered automatically by `src/bootstrap.ts`.

## Code Locations

- Bootstrap: `src/bootstrap.ts` — VD registration, trigger registration, index creation
- Triggers: `src/lib/aidbox-triggers.ts` — trigger definitions, Changes API
- VD Parser: `src/lib/viewdefinition-parser.ts` — parse VDs, generate UPSERT SQL
- Maintenance: `src/lib/maintenance-mode.ts` — deregister/re-register triggers
- Refresh: `src/lib/flat-table-refresh.ts` — refreshAll, targeted updates
- FHIR client: `src/lib/fhir-client.ts` — sql(), materialize()
- ViewDefs: `infra/viewdefinitions/*.json`
- Setup script: `infra/setup-viewdefinitions.sh`
- Config: `src/lib/config.ts` — aidboxConfig
