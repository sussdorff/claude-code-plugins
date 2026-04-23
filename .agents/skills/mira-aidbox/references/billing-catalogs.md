# Billing Catalogs in Aidbox

## Current State (verified 2026-03)

### ChargeItemDefinitions (queried by BillingCatalog service)

| Catalog | Seed File | System URL | Count |
|---------|-----------|-----------|-------|
| EBM | `ebm-catalog.json` | `http://fhir.de/CodeSystem/ebm` | 2,884 |
| GOÄ | `goae-catalog.json` | `http://fhir.de/CodeSystem/goae` | 2,337 |
| HZV Bayern | `hzv-bayern-catalog.json` | `http://mira.cognovis.de/fhir/CodeSystem/hzv-bayern-ek` | 35 |

### CodeSystems (terminology references)

| CodeSystem | ID | URL |
|-----------|-----|-----|
| EBM | `ebm` | `http://fhir.de/CodeSystem/ebm` |
| HZV Bayern EK | `hzv-bayern-ek` | `http://mira.cognovis.de/fhir/CodeSystem/hzv-bayern-ek` |
| ICD-10-GM 2026 | `icd10gm-2026` | `http://fhir.de/CodeSystem/bfarm/icd-10-gm` |

**Total**: 5,256 ChargeItemDefinitions + 3 CodeSystems

## Seed & Update Scripts

```bash
bun run seed:catalogs                          # All seed files
bun run seed:icd10                             # ICD-10-GM from BfArM
bun run catalog:update                         # All catalogs (ETL + diff + load)
bun run catalog:update -- --catalog=ebm        # EBM only
bun run catalog:update -- --diff-only          # Show diff, don't load
bun run catalog:update -- --load               # ETL + diff + load into Aidbox
bun run catalog:update -- --skip-etl           # Skip ETL, just diff + load
```

## ETL Pipelines (in etl/)

| Catalog | Source | Auto-Download? |
|---------|--------|----------------|
| EBM | KVB PDF + KBV Suffix CSV | Yes (kvb.de, update.kbv.de) |
| GOÄ | XML from gesetze-im-internet.de | Yes |
| HZV Bayern | Curated JSON (manual) | No (PDFs from haev.de) |
| ICD-10-GM | BfArM FHIR package | Yes (terminologien.bfarm.de) |

**EBM update**: `parse.py` auto-downloads. Requires `uv` + `pdfplumber`.
**GOÄ update**: Stable (1982 law). New reform expected mid-2026.
**HZV Bayern**: Manual — download PDFs, update JSON in `etl/hzv-bayern/data/`, run `to_fhir.py`.

## Querying Billing Codes

```bash
# Count by system
curl -s -u $AIDBOX_AUTH "$AIDBOX_FHIR_URL/ChargeItemDefinition?_count=6000&_elements=code" \
  | jq '[.entry[].resource.code.coding[0].system] | group_by(.) | map({system: .[0], count: length})'

# Search EBM code
curl -s -u $AIDBOX_AUTH "$AIDBOX_FHIR_URL/ChargeItemDefinition?code=http://fhir.de/CodeSystem/ebm|03220"
```

## ICD-10-GM Loading

```bash
bun run seed:icd10    # Automated — downloads + imports via NDJSON $import
```
