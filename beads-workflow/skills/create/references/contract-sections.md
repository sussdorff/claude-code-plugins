# Architecture Contracts Touched — Section Reference

When a bead touches an **architectural contract** (an ADR, a shared helper, or an enforcer),
it must declare this explicitly in its description. This makes the impact visible, keeps the
Architecture Trinity matrix accurate, and enables automated lint checks.

---

## The `touches-contract` Label

Add the label `touches-contract` to a bead when it:

- Implements a decision recorded in an ADR
- Modifies or adds a Helper (shared utility bound to an ADR)
- Changes an Enforcer-Proactive (codegen / builder)
- Changes an Enforcer-Reactive (lint rule / test)
- Introduces a gap that should become a new ADR, Helper, or Enforcer

**Do NOT add the label** for beads that only touch application logic with no
architectural significance (CRUD, UI tweaks, business rules that don't cross module
boundaries).

---

## Mandatory Section Structure

When `touches-contract` is set, the bead description **must** contain all three of
these sections in this order:

```markdown
## Architecture Contracts Touched
- ADR-NNN (Name): <how this bead uses / extends the contract>
- Helper: <path/to/helper>            # optional, include if applicable
- Enforcer-Proactive: <codegen tool>  # optional
- Enforcer-Reactive: <lint rule / test>  # optional

## Coverage Expected
- Packages: <list of packages touched>
- Status nach Bead: <which matrix cells turn green>

## Gaps to Close
- [ ] None
```

---

## Parser Rules

### Rule 3a — No empty sections

A section header without any bullet points is a lint failure. If you truly have
nothing to say, delete the section — but you should not have the `touches-contract`
label either in that case.

### Rule 3b — ADR bullet required

The `## Architecture Contracts Touched` section must contain **at least one** bullet
in the exact format:

```
- ADR-NNN (Name): <description of what this bead does with the contract>
```

Examples of **valid** ADR bullets:

```
- ADR-001 (Identity): extends typed ID helper for new PatientVisit entity
- ADR-007 (Caching): switches from in-memory to Redis via existing cache contract
```

Examples of **invalid** ADR bullets (fail rule 3b):

```
- ADR (Identity): missing number
- ADR-001: missing name in parentheses
- This bead uses ADR-001       # must start with "- ADR-"
```

Optional bullets (`- Helper:`, `- Enforcer-Proactive:`, `- Enforcer-Reactive:`) do **not**
satisfy rule 3b. They complement the mandatory ADR bullet.

### Rule 3c — Gaps to Close section is mandatory

Every `touches-contract` bead must have a `## Gaps to Close` section with at least
one checkbox bullet. Valid bullet values:

| Marker | Meaning |
|--------|---------|
| `- [ ] None` | No gaps — all contracts are fully addressed |
| `- [ ] [ADR-NEEDED] <description>` | A new ADR should be written |
| `- [ ] [HELPER-NEEDED] <description>` | A shared helper is missing |
| `- [ ] [ENFORCER-PROACTIVE-NEEDED] <description>` | Codegen / builder is missing |
| `- [ ] [ENFORCER-REACTIVE-NEEDED] <description>` | Lint rule or test is missing |

An empty `## Gaps to Close` section (header only, no bullets) fails rule 3c.
Free-text bullets without a recognised marker also fail.

**Mutual exclusion**: `- [ ] None` and any `[*-NEEDED]` markers cannot coexist in the same section. If there are no gaps, use only `- [ ] None`. If there are gaps, list them with `[*-NEEDED]` markers and omit `- [ ] None`.

### Rule Y — Label false-negative

If a bead description contains `## Architecture Contracts Touched` but the bead
lacks the `touches-contract` label, the linter reports a false-negative error.
This catches cases where the section was added manually but the label was forgotten.

---

## Running the Linter

```bash
# Check all open beads with 'touches-contract' label (default)
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bd_lint_contracts.py"

# Include closed beads
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bd_lint_contracts.py" --all

# Check a single bead
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bd_lint_contracts.py" --bead CCP-abc

# Only run the false-negative check (rule Y)
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bd_lint_contracts.py" --check-false-negatives

# via shell extension (requires sourcing bd-lint-extension.sh first)
bd lint --check=architecture-contracts
bd lint --check=architecture-contracts --all
bd lint --check=architecture-contracts --bead CCP-abc
```

**Install shell extension** (add to `~/.zshrc` or `~/.bashrc`):

```bash
source "${CLAUDE_PLUGIN_ROOT}/scripts/bd-lint-extension.sh"
```

---

## Complete Valid Example

```markdown
## Architecture Contracts Touched
- ADR-001 (Identity): adds typed ID helper for new `PatientVisit` entity;
  uses `makeIdHelper` from packages/core/helpers/entity-id.ts
- Helper: packages/core/helpers/entity-id.ts
- Enforcer-Reactive: lint/rules/no-raw-id-concat.js

## Coverage Expected
- Packages: core, pvs-adapter, mira-api
- Status nach Bead: ADR-001 green for PatientVisit layer

## Gaps to Close
- [ ] [ENFORCER-PROACTIVE-NEEDED] Codegen for PatientVisit ID type does not exist yet
- [ ] [ADR-NEEDED] No ADR yet for cross-entity ID resolution
```

---

## Architecture Trinity Vocabulary

| Term | Category | Role |
|------|----------|------|
| **ADR** | Decision Record | Documents the architectural law — context, decision, consequences |
| **Helper** | Utility | Encapsulates a common operation for reuse; passive |
| **Enforcer-Proactive** | Codegen / Builder | Generates code so the wrong pattern is structurally impossible |
| **Enforcer-Reactive** | Lint / Test | Checks existing code for violations after the fact |
