# Architecture Contracts Touched — Reference

This document covers the `touches-contract` label convention, the mandatory section
structure it requires in bead descriptions, the three parser rules enforced by
`bd-lint-contracts`, and valid Gap markers.

---

## What is the `touches-contract` Label?

The `touches-contract` label is an **opt-in convention** applied to beads that interact
with a documented architectural decision (ADR) or its associated tooling (Helpers,
Enforcer-Proactive, Enforcer-Reactive).

When a bead:
- Implements, extends, or modifies an ADR
- Uses a Helper that encodes an architectural rule
- Adds or changes an Enforcer (code-gen or lint/test)
- Exposes a gap in the current architectural tooling

...it should carry the `touches-contract` label.

**When NOT to use it:** Routine feature work, bug fixes, dependency updates, or chores
that do not interact with any documented architectural pattern.

---

## Mandatory Section Structure

When the `touches-contract` label is set, the bead description **must** include these
three sections. They appear together at the end of the description.

```markdown
## Architecture Contracts Touched
- ADR-NNN (Name): <what this bead does, how it relates to the ADR>
- Helper: <path/to/helper.ts>           (optional)
- Enforcer-Proactive: <codegen/builder> (optional)
- Enforcer-Reactive: <lint-rule or test> (optional)

## Coverage Expected
- Packages: <list of affected packages>
- Status nach Bead: <what turns green in the matrix after this bead>

## Gaps to Close
- [ ] None
```

### ADR bullet format

The `- ADR-NNN (Name): description` bullet is **required**. The format must match:

```
- ADR-<digits> (<Name>): <non-empty description>
```

Examples:
- `- ADR-001 (TypedIDs): This bead uses typed ID helpers throughout the adapter layer.`
- `- ADR-042 (EventSourcing): Adds domain event recording to the payment module.`

Optional bullets (`Helper:`, `Enforcer-Proactive:`, `Enforcer-Reactive:`) may appear in
any order after the ADR bullet. They are valid if used, but not required.

---

## Parser Rules

The linter (`bd_lint_contracts.py`) enforces three rules, plus one false-negative check.

### Rule 3a — Empty Section

**Condition:** `## Architecture Contracts Touched` header exists but has zero bullet points.

**Error:** `rule=3a: '## Architecture Contracts Touched' section exists but contains no bullet points`

**Fix:** Add at least one `- ADR-NNN (Name): ...` bullet.

---

### Rule 3b — ADR Bullet Required

**Condition:** Section has bullets, but none match the ADR format
`- ADR-NNN (Name): description`.

**Error:** `rule=3b: ... must contain at least one ADR bullet in format: '- ADR-NNN (Name): <description>'`

**Fix:** Add a correctly formatted ADR bullet. Note:
- `ADR001` (no hyphen) → invalid
- `- ADR-001 TypedIDs: ...` (no parens) → invalid
- `- ADR-001 (TypedIDs): ...` → valid

---

### Rule 3c — Gaps to Close Section

**Condition (3c-missing):** `## Architecture Contracts Touched` is present but
`## Gaps to Close` section is missing entirely.

**Condition (3c-empty):** `## Gaps to Close` exists but has no bullet points.

**Condition (3c-invalid):** `## Gaps to Close` has bullets but none match valid patterns.

**Error:** `rule=3c: ...`

**Fix:** Add a `## Gaps to Close` section with at least one valid bullet.

#### Valid Gap Bullets

All gap bullets use checkbox format `- [ ]` followed by exactly one of:

| Bullet | Meaning |
|--------|---------|
| `- [ ] None` | Explicit acknowledgement that no gaps remain |
| `- [ ] [ADR-NEEDED] <description>` | A decision needs to be formally documented |
| `- [ ] [HELPER-NEEDED] <description>` | A helper utility should be created |
| `- [ ] [ENFORCER-PROACTIVE-NEEDED] <description>` | A code-gen/builder should be created |
| `- [ ] [ENFORCER-REACTIVE-NEEDED] <description>` | A lint rule or test should be created |

**Invalid examples:**
- `- No gaps identified` → missing checkbox
- `- [ ] We should look into this` → no keyword
- `- [ ] [FIX-NEEDED] something` → unknown keyword

---

### Rule Y — Label False-Negative Check

**Condition:** A bead description contains `## Architecture Contracts Touched` but
the bead does NOT have the `touches-contract` label.

**Error:** `rule=Y: Bead description contains '## Architecture Contracts Touched' section but does NOT have the 'touches-contract' label.`

**Fix:** Either add the `touches-contract` label (`bd label add <id> touches-contract`) or
remove the section from the description.

---

## Running the Linter

### Direct Python invocation

```bash
# Lint all open beads with touches-contract label (+ false-negative check)
python3 beads-workflow/scripts/bd_lint_contracts.py

# Include closed beads
python3 beads-workflow/scripts/bd_lint_contracts.py --all

# Check a single bead
python3 beads-workflow/scripts/bd_lint_contracts.py --bead CCP-0hr

# False-negative check only
python3 beads-workflow/scripts/bd_lint_contracts.py --check-false-negatives
```

### Via shell wrapper (bd lint syntax)

Source the extension once in your shell profile or session:

```bash
source beads-workflow/scripts/bd-lint-extension.sh
```

Then use:

```bash
bd lint --check=architecture-contracts
bd lint --check=architecture-contracts --all
bd lint --check=architecture-contracts --bead CCP-0hr
```

---

## Complete Valid Example

```markdown
## Architecture Contracts Touched
- ADR-001 (TypedIDs): This bead migrates all entity ID references in the adapter
  layer to use the typed ID helper, preventing raw string concatenation.
- Helper: lib/id-helpers.ts
- Enforcer-Reactive: eslint/no-raw-id-concat

## Coverage Expected
- Packages: lib/adapters, lib/core
- Status nach Bead: ADR-001 column turns green in the matrix for lib/adapters

## Gaps to Close
- [ ] [ENFORCER-PROACTIVE-NEEDED] Generate ID accessor functions at build time
```

---

## Architecture Trinity Vocabulary

This convention is built around four precise terms:

| Term | Role |
|------|------|
| **ADR** | Documents the architectural decision ("the law") |
| **Helper** | Utility that encapsulates a common operation (passive, no enforcement) |
| **Enforcer-Proactive** | Code-gen / builder — makes the wrong pattern structurally impossible |
| **Enforcer-Reactive** | Lint rule or test — catches violations after the fact |

See `CLAUDE.md` (Architecture Trinity Vocabulary section) for full definitions.
