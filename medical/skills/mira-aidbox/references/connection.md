# Aidbox Connection Details

## Connection URLs

```bash
# Production (Caddy → nginx → aidbox)
AIDBOX_URL="https://mira.cognovis.de/aidbox"
AIDBOX_FHIR_URL="https://mira.cognovis.de/aidbox/fhir"

# Docker-internal (from API container)
AIDBOX_URL="http://aidbox:8080"
AIDBOX_FHIR_URL="http://aidbox:8080/fhir"

# MCN production
# See .env — SSH to mcn-mira for details
```

Config: `src/lib/config.ts` — `aidboxConfig.fhirBaseUrl` (FHIR), `aidboxConfig.aidboxBaseUrl` (native, derived by stripping `/fhir`).

## Infrastructure

| Component | Internal | External |
|---|---|---|
| Aidbox | `aidbox:8080` | `mira.cognovis.de/aidbox/` |
| API | `api:3001` | `mira.cognovis.de/api/` |
| Frontend | `frontend:3000` | `mira.cognovis.de/` |
| PostgreSQL | `aidbox-db:5432` | not exposed |

Elysium: LXC 114 (demo/test). MCN: bare-metal (production).

## Quick Commands

```bash
# Resource counts
curl -s -u $AIDBOX_AUTH "$AIDBOX_FHIR_URL/metadata" | jq '.rest[0].resource[] | {type, count: .extension[0].valueInteger}'

# Search (always set _count explicitly!)
curl -s -u $AIDBOX_AUTH "$AIDBOX_FHIR_URL/Patient?_count=5"

# Count (use _summary=count, NOT .entry length)
curl -s -u $AIDBOX_AUTH "$AIDBOX_FHIR_URL/Patient?_summary=count" | jq '.total'

# Direct SQL
curl -s -u $AIDBOX_AUTH "$AIDBOX_URL/$sql" -d '["SELECT count(*) FROM patient"]'
```
