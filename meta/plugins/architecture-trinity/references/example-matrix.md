# Example Coverage Matrix Report

This is a realistic example of an architecture-scout report for a bead that touches
`packages/pvs-charly` and `packages/pvs-x-isynet`. It serves as both documentation
and a test fixture for verifying the scout's output format.

## Input

```json
{
  "bead_id": "CCP-2hd",
  "bead_description": "Add sync support for pvs-charly delta events and cross-adapter reconciliation",
  "touched_paths": ["packages/pvs-charly", "packages/pvs-x-isynet"],
  "mode": "advisor"
}
```

## JSON Output

```json
{
  "status": "VIOLATION",
  "mode": "advisor",
  "findings": [
    {
      "rule": "vision-boundary:platform-no-application-import",
      "concern": "packages/adapter-common/src/boundary-violation.ts imports from pvs-charly (layer:platform must not depend on layer:application)",
      "severity": "BLOCKING",
      "source": "packages/adapter-common/src/boundary-violation.ts:20"
    },
    {
      "rule": "implicit:repeated-event-kind",
      "concern": "event.kind === 'literal' pattern found in 4 files without ADR covering delta event semantics",
      "severity": "ADVISORY",
      "source": "packages/pvs-charly/src/sync.ts:20, packages/pvs-x-isynet/src/delta.ts:21, packages/pvs-charly/src/reconcile.ts:32, packages/pvs-x-isynet/src/processor.ts:29"
    },
    {
      "rule": "trinity-gap:error-envelope",
      "concern": "ADR 0003 (Error Envelope) is proposed (not yet accepted) and has no Proactive Enforcer or Reactive Enforcer",
      "severity": "ADVISORY",
      "source": "docs/adr/0003-error-envelope.md"
    },
    {
      "rule": "trinity-gap:schema-codegen",
      "concern": "ADR 0002 (Schema Codegen) applies to pvs-charly but is missing a Reactive Enforcer (no lint rule or test enforcing codegen usage)",
      "severity": "INFO",
      "source": "docs/adr/0002-schema-codegen.md"
    }
  ]
}
```

## Markdown Coverage Matrix

## Coverage Matrix (architecture-scout)

**Bead**: CCP-2hd — Add sync support for pvs-charly delta events and cross-adapter reconciliation
**Mode**: advisor
**Status**: VIOLATION ❌

### Existing Contracts

| Contract | ADR | Helper | Proactive | Reactive | Status |
|----------|-----|--------|-----------|----------|--------|
| ID Taxonomy | ✅ | ✅ | ✅ | ✅ | full-trinity |
| Error Envelope | ⚠️ | ✅ | ❌ | ❌ | pre-trinity |
| Schema Codegen | ✅ | ✅ | ✅ | ❌ | partial |

**Evidence:**
- **ID Taxonomy** (`docs/adr/0001-id-taxonomy.md`): Helper in `packages/adapter-common/src/id-taxonomy.ts`, Proactive in `scripts/gen-id-types.ts`, Reactive in `packages/adapter-common/src/id-taxonomy.test.ts`
- **Error Envelope** (`docs/adr/0003-error-envelope.md`): ADR status is `proposed` (⚠️) — Helper exists (`error-envelope.ts`), but no Proactive or Reactive Enforcer yet
- **Schema Codegen** (`docs/adr/0002-schema-codegen.md`): Helper and Proactive present; no ESLint rule or test enforces correct usage

### Implicit Contracts Detected

| Pattern | Location | Suggested Triple |
|---------|----------|-----------------|
| `repeated-event-kind` | `pvs-charly/src/sync.ts:20`, `pvs-x-isynet/src/delta.ts:21`, `pvs-charly/src/reconcile.ts:32`, `pvs-x-isynet/src/processor.ts:29` | ADR-0004: delta-event-kind + `makeDeltaKindHelper` + `no-stringly-typed-event-kind` |

### Recommended Triples

- [ ] ADR-0004: delta-event-kind — documents delta event semantics used in pvs-charly and pvs-x-isynet; add `makeDeltaKindHelper` in `adapter-common` + lint rule `no-stringly-typed-event-kind`
- [ ] Advance Error Envelope (ADR-0003 is `proposed`): accept the ADR, then add Proactive Enforcer (`createErrorEnvelope` codegen) + lint rule `no-inline-error-shape` + tests enforcing the envelope shape
- [ ] Add Reactive Enforcer for Schema Codegen: ESLint rule `no-manual-schema-definition` to prevent bypassing the codegen pipeline

### Findings Detail

⛔ **BLOCKING** — Vision Boundary Violation:
`packages/adapter-common/src/boundary-violation.ts:20` imports from `pvs-charly`.
According to `vision.md`: layer `platform` must not depend on layer `application`.
`adapter-common` is classified as `platform`; `pvs-charly` is `application`.
**Action required**: Remove the forbidden import before proceeding.

⚠️ **ADVISORY** — Implicit Contract `repeated-event-kind`:
The pattern `event.kind === 'literal'` appears in 4 source files. This is an undocumented
contract — any developer can add new event kinds without validation. Consider promoting
this to ADR-0004 before implementing new delta sync logic to avoid creating more debt.

⚠️ **ADVISORY** — Trinity Gap `error-envelope`:
ADR-0003 is proposed but not implemented. The new sync feature will likely produce errors —
without a shared envelope, each adapter will invent its own error shape.

ℹ️ **INFO** — Trinity Gap `schema-codegen`:
Schema Codegen is mostly covered but lacks a Reactive Enforcer. Not blocking for this feature,
but worth tracking.

---

## Notes for Test Fixture Usage

This example is based on the `mira-adapters-snapshot` fixture at:
`dev-tools/skills/project-context/tests/fixtures/mira-adapters-snapshot/`

The fixture provides:
- `docs/adr/0001-id-taxonomy.md` — full-trinity contract
- `docs/adr/0002-schema-codegen.md` — partial contract
- `docs/adr/0003-error-envelope.md` — pre-trinity contract
- `packages/pvs-charly/src/sync.ts` — contains `repeated-event-kind` pattern (occurrence 1)
- `packages/pvs-x-isynet/src/delta.ts` — second occurrence of pattern (occurrence 2)
- `packages/pvs-charly/src/reconcile.ts` — third occurrence of pattern (occurrence 3)
- `packages/pvs-x-isynet/src/processor.ts` — fourth occurrence of pattern (occurrence 4, meets 3+ threshold)
- `scripts/gen-id-types.ts` — Proactive Enforcer for ID Taxonomy
- `vision.md` — boundary table declaring platform → application forbidden
- `packages/adapter-common/src/boundary-violation.ts` — the forbidden import (BLOCKING finding)
