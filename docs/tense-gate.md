# tense-gate: Prescriptive-Present Enforcement

`scripts/tense-gate.py` is a lint script that enforces the "present-tense truth" contract
on `vision.md` and any document declared as `document_type: prescriptive-present`.

## Why

A prescriptive-present document (especially `vision.md`) states principles that hold **now**.
Future-tense language — "will support", "TBD", "by Q3", "eventually" — smuggles roadmap
commitments into what should be immutable architectural truth. This breaks the contract:
readers plan against the principles as if they are implemented, not as aspirations.

The rule: if it is not true now, it does not belong here. Roadmap lives in beads.

## Which files are scanned

1. Any file named `vision.md` (regardless of path).
2. Any file with YAML frontmatter containing `document_type: prescriptive-present`.

## Markers flagged (case-insensitive)

| Marker pattern | Tag | Reason |
|---|---|---|
| `will <verb>` | `will` | Future tense |
| `should <verb>` | `should` | Deferral / conditional |
| `plan to` / `planning to` | `plan to` | Planning language |
| `going to` | `going to` | Planning language |
| `by Q[1-4]` | `by Qn` | Roadmap quarter |
| `by <month name>` | `by <month>` | Roadmap month |
| `by <4-digit year>` | `by <year>` | Roadmap year |
| `eventually` | `eventually` | Temporal deferral |
| `later` | `later` | Temporal deferral |
| `in the future` | `in the future` | Temporal deferral |
| `TBD` | `TBD` | Placeholder |
| `STUB` | `STUB` | Placeholder |
| `TODO` | `TODO` | Placeholder |
| `to be locked by` | `to be locked by` | Explicit deferral |
| `to be decided` | `to be decided` | Explicit deferral |
| `to be determined` | `to be determined` | Explicit deferral |

## Output format

```
docs/vision.md:42:1: [will] Future-tense marker in prescriptive document.
  Found: 'The platform will support multi-tenant routing'
  Suggest: rewrite as principle (present-tense) OR move to bead/roadmap
```

## Allowlist mechanism

Place a comment `<!-- tense-gate-ignore: <reason> -->` on the line **immediately before**
the violating line to suppress that violation:

```markdown
<!-- tense-gate-ignore: historical reference in architectural note -->
The system will eventually migrate to async messaging.
```

The reason is required (though not validated) — it documents why the exception exists.

## Usage

```bash
# Lint a single file
python3 scripts/tense-gate.py docs/vision.md

# Lint multiple files
python3 scripts/tense-gate.py docs/vision.md docs/strategy.md

# Exit codes: 0 = clean, 1 = violations found, 2 = usage error
```

## Pre-commit integration

Install [pre-commit](https://pre-commit.com/) and add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/your-org/claude-code-plugins
    rev: main
    hooks:
      - id: tense-gate
```

The hook configuration lives in `.pre-commit-hooks.yaml` at the repo root.

## Fixing violations

For each flagged line, choose one of:

1. **Rewrite as a present-tense principle** — state what is architecturally true now.
   Example: "The platform will support X" → "The platform supports X."

2. **Move to a bead** — if the work is not done, create a bead and remove the
   forward-looking language from the vision doc entirely. Link the bead in a footnote.

3. **Allowlist with justification** — only for cases where the future-tense phrasing
   is genuinely unavoidable (e.g., quoting a historical decision verbatim). Use sparingly.
