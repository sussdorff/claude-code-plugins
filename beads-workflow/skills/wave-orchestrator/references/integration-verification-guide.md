# Integration-Verification Guide

Reference for Phase 6.5 of the wave-orchestrator: post-epic cross-bead invariant checks.

## Why Integration-Verification?

Individual bead reviews catch implementation errors within a single bead. They cannot catch
architectural gaps that only appear when all beads are combined — for example:

- A universal-scope that every bead needs but no single bead creates
- A cross-bead interface where both sides evolved independently
- A missing value in a shared enum that is written by Bead A and read by Bead B

This guide documents the canonical-catalog regression scenario that motivated Phase 6.5,
and explains how to write project-specific integration checks.

## Regression Scenario: KBV/DIMDI Universal-Scope (Medical Codes Migration)

**Epic**: Medical codes migration (eUeberweisung + eArztbrief, ~30 beads, April 2026)

**What happened:**
- All 30 sub-beads completed successfully. Each implemented its own scope with adapter-prefix
  (e.g. `kbv-eueberweisung`, `kbv-earztbrief`).
- The Architecture Council (Phase 1.5b) reviewed the wave but did NOT ask: "Do KBV/DIMDI
  catalogs need a universal scope without adapter-prefix?"
- After epic close, a manual live-Aidbox invariant query revealed:
  - KBV Fachabteilungsschlüssel (hospital department codes): the CodeSystem URL returned 0
    results in a universal scope — because it was only loaded under per-adapter prefixed
    scopes (`kbv-eueberweisung`, `kbv-earztbrief`), not as a shared universal resource
  - DIMDI ICD catalog: same issue — no shared universal scope

**What went wrong:**
- Council prompt lacked a canonical-catalog detection check
- No integration-verification phase existed to catch cross-bead gaps before epic close
- 30 individual bead reviews all PASSED — the gap was invisible at bead level

**Would the new Council check have caught it?**
YES. The new Phase 1.5b council prompt includes:

> **Step 2 — External Authorities**: Does this domain have canonical reference catalogs?
> Medical: KBV, DIMDI, ICD (WHO), LOINC, SNOMED CT, IFA...
> If yes → CRITICAL finding: "Missing Universal-Scope for <catalog>"

A council review for any of the 30 beads (or for the epic-level architecture bead) would
have flagged: "KBV Fachabteilungsschlüssel requires a universal scope without adapter-prefix".

**Would an integration-verification have caught it?**
YES. A `.beads/integration-check.sh` for Aidbox would have queried the CodeSystem URL in
universal scope (no adapter-prefix). The check detects absence-of-universal-scope: if
`.total == 0`, the CodeSystem was never loaded as a shared universal resource — only under
per-adapter scopes. For example:

```bash
# Check: Is KBV Fachabteilungsschlüssel present in universal scope?
curl -s "$AIDBOX_URL/fhir/CodeSystem?url=http://fhir.de/CodeSystem/dkgev/Fachabteilungsschluessel" \
  | jq '.total // 0'
# Expected: > 0 (universal scope exists)
# Actual: 0 (only per-adapter scopes existed — universal scope absent)
```

`.total == 0` → CRITICAL finding ("not found in universal scope") → follow-up bead created
before epic was declared complete.

## Canonical-Catalog Taxonomy by Domain

Use this as a reference when reviewing beads or writing integration checks.

### Medical / Healthcare (Germany)
| Authority | Catalog | Scope pattern |
|-----------|---------|---------------|
| KBV | Fachabteilungsschlüssel (hospital), Fachgruppenschlüssel (GP) | universal, no adapter-prefix |
| DIMDI / BfArM | ICD-10-GM, OPS | universal |
| WHO | ICD-11, ICD-10 international | universal |
| Regenstrief | LOINC (lab codes) | universal |
| SNOMED International | SNOMED CT | universal |
| IFA | Pharmazentralnummer (PZN), Artikelstamm | universal |
| ABDA | Pharmacy product data | universal |
| ARGE Kodierrichtlinien | DRG codes | universal |

### Finance
| Authority | Catalog | Scope pattern |
|-----------|---------|---------------|
| SWIFT | BIC codes | universal |
| IBAN structure | IBAN format (ISO 13616) | universal |
| ISO | ISIN (ISO 6166), currency codes (ISO 4217) | universal |
| Visa/MC | MCC codes | universal |
| GLEIF | LEI (Legal Entity Identifier) | universal |

### Legal (Germany/EU)
| Authority | Catalog | Scope pattern |
|-----------|---------|---------------|
| Bundesanzeiger | BGBl (Bundesgesetzblatt) | universal |
| EUR-Lex | EU regulations, directives | universal |
| Handelsregister | Company register numbers | universal |

### Logistics
| Authority | Catalog | Scope pattern |
|-----------|---------|---------------|
| UN/CEFACT | UN/LOCODE (port/location codes) | universal |
| WCO | HS codes (customs) | universal |
| GS1 | EAN/GTIN, GLN, SSCC | universal |

### Identity
| Authority | Catalog | Scope pattern |
|-----------|---------|---------------|
| ORCID | ORCID (researcher IDs) | universal |
| NPI (US CMS) | National Provider Identifier | universal |
| EIN (US IRS) | Employer Identification Number | universal |

## Writing a .beads/integration-check.sh

Create this file in the project root under `.beads/` to enable automated integration checks.

### Structure

```bash
#!/usr/bin/env bash
# .beads/integration-check.sh — Project-specific cross-bead invariant checks
#
# Called by wave-orchestrator Phase 6.5 after all beads in a wave are closed.
# Must output JSON matching the integration-check schema.
# Exit 0 = PASS, Exit 1 = FAIL, Exit 2 = error

set -uo pipefail

FINDINGS="[]"
STATUS="PASS"

add_finding() {
  local severity="$1" category="$2" description="$3" recommendation="$4"
  FINDINGS=$(echo "$FINDINGS" | jq \
    --arg sev "$severity" --arg cat "$category" \
    --arg desc "$description" --arg rec "$recommendation" \
    '. + [{"severity": $sev, "category": $cat, "description": $desc, "recommendation": $rec}]')
  if [[ "$severity" == "CRITICAL" ]]; then
    STATUS="FAIL"
  fi
}

# --- Project-specific checks below ---

# Example: Check that universal CodeSystems exist in Aidbox
if [[ -n "${AIDBOX_URL:-}" ]]; then
  # Note: transport failures (Aidbox unreachable, HTTP error) are treated as absence by design.
  # To distinguish infrastructure errors from invariant violations, check AIDBOX_URL is reachable
  # before running individual checks (e.g. curl -sf "$AIDBOX_URL/health" || { echo "Aidbox unreachable"; exit 2; })
  # KBV Fachabteilungsschlüssel (specialty codes) — must be in universal scope
  KBV_COUNT=$(curl -sf "$AIDBOX_URL/fhir/CodeSystem?url=http://fhir.de/CodeSystem/dkgev/Fachabteilungsschluessel" \
    | jq -r '.total // 0' 2>/dev/null || echo 0)
  if [[ "${KBV_COUNT:-0}" =~ ^[0-9]+$ ]] && [[ "${KBV_COUNT:-0}" -eq 0 ]]; then
    add_finding "CRITICAL" "missing_scope" \
      "KBV Fachabteilungsschlüssel not found in universal scope" \
      "Create CodeSystem resource at http://fhir.de/CodeSystem/dkgev/Fachabteilungsschluessel without adapter-prefix"
  fi
fi

# --- Output ---

jq -n \
  --arg status "$STATUS" \
  --argjson findings "$FINDINGS" \
  --arg env "${INTEGRATION_ENV:-unknown}" \
  --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{status: $status, findings: $findings, environment: $env, checked_at: $ts}'

if [[ "$STATUS" == "FAIL" ]]; then
  exit 1
fi
```

### Tips
- Load `$AIDBOX_URL`, `$DATABASE_URL`, or other env vars from `.env.local`
- Use `curl -sf` (silent + fail-on-error) for HTTP checks
- Use `psql "$DATABASE_URL" -c "SELECT ..."` for database invariants
- Run multiple checks and collect all findings before exiting (don't exit-early on first failure)
- Keep checks idempotent (safe to re-run, no side effects)
- Target: < 30 seconds total runtime
