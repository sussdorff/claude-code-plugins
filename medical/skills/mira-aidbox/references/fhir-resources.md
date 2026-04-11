# FHIR Resources — Mira-Specific Patterns

> For general FHIR/Aidbox resource patterns (concept storage, pagination, bulk import, bundle types, PostgreSQL parameter limits), see the samurai-skills plugin.

## Mira Billing Resource Architecture

| Use Case | FHIR Resource | Example |
|----------|--------------|---------|
| Terminology / Diagnosen | CodeSystem | ICD-10-GM, SNOMED, LOINC |
| Abrechenbare Leistungen mit Preisen | ChargeItemDefinition | EBM-Ziffern, GOA-Ziffern |
| Referenz-Vokabular | CodeSystem | EBM CodeSystem (Codes + Punktwerte) |

**Key insight**: Mira billing catalogs use BOTH:
- **CodeSystem** = Terminology reference (Code + Display + Properties)
- **ChargeItemDefinition** = Operative billing data (prices, multipliers, rules)

The `BillingCatalog` service in `src/lib/billing/catalog.ts` queries ChargeItemDefinitions.

## ETL Load Order (Referential Integrity)

Aidbox enforces referential integrity. Mira seed/sync must follow this order:
1. Organizations, Locations (no dependencies)
2. Practitioners, PractitionerRoles (-> Organizations)
3. Patients (-> Organizations)
4. Encounters, Conditions (-> Patients + Practitioners)
5. Claims, ChargeItems (-> Encounters + Patients)

## Date Format

FHIR requires ISO 8601 (`2026-01-01`), NOT German format (`01.01.2026`). Aidbox returns 422 for non-ISO dates. Especially relevant for mira ETL from German PVS systems that use `DD.MM.YYYY`.

## Mira Known Issues

- **Seed data NOT auto-loaded**: `aidbox/seed/` volume is not auto-imported. Use `bun run seed:catalogs`.
- **413 via Caddy/nginx**: Large files (>10MB) may be rejected. Load via docker network directly.
- **ConceptMap in transaction**: Aidbox refuses PUT for existing ConceptMaps in transaction bundles. Use batch.
- **GOA batch duplicate**: 1 duplicate ID causes 1 error per load — harmless (2,337/2,338 succeed).
- **Two instances exist**: `ignis.cognovis.de` (old) and `mira.cognovis.de` (production). Always use mira.
