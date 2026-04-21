---
name: entropy-scan
description: >-
  Scan the agent harness (skills, hooks, agents, standards) for invariant violations
  and entropy. Produces a violation report with actionable fix instructions. Triggers on:
  entropy scan, harness check, harness validate, invariants check.
---

# Entropy Scan

Mechanically validate the agent harness against invariants defined in `docs/HARNESS_SPEC.md`. Detects structural violations, reports each with an actionable `FIX:` instruction.

## Overview

Entropy Scan checks four agent harness artifact types — skills, hooks, agents, and standards — against a fixed set of 17 structural invariants (SKILL-01..05, HOOK-01..04, AGENT-01..04, STD-01..04). Each violation includes the offending path, a description of the problem, and an actionable `FIX:` instruction. The scan is read-only: it reports but never modifies files.

## When to Use

- "entropy scan" / "harness check" / "harness validate"
- "check invariants" / "scan invariants" / "harness health"
- After adding or modifying skills, hooks, agents, or standards
- As part of project-health checks (see harness adapter for integration details)
- Before pushing harness changes to ensure no violations

Do NOT use for: feature implementation, bug fixes, or documentation updates unrelated to harness structure.

## Running entropy-scan

Run the `entropy-scan.sh` script from the skill's `scripts/` directory, from the repo root.
See your harness adapter for the exact invocation path.

Optional: scan a specific directory by passing `--dir /path/to/project` to the script.

**Exit codes:** 0 = clean, 1 = violations found, 2 = execution error.

**Output format:**
```
VIOLATION [SKILL-01]: <skills-dir>/foo/ — SKILL.md missing — FIX: Create <skills-dir>/foo/SKILL.md with required frontmatter
VIOLATION [HOOK-01]: <hooks-dir>/my-hook.sh — Missing exit-code comment block — FIX: Add comment block (# exit 0 = allow, # exit 2 = deny)
...
Total violations: N
```

## What Is Checked

The script validates four categories. For full invariant definitions with rationale, see `docs/HARNESS_SPEC.md`.

| ID | Category | What is checked |
|----|----------|-----------------|
| SKILL-01 | Skills | Every skill dir has a `SKILL.md` |
| SKILL-02 | Skills | Frontmatter has `name:` and `description:` (150–300 chars, spaces included) |
| SKILL-03 | Skills | Required sections (`## Overview`, `## When to Use`) exist and are ordered correctly |
| SKILL-04 | Skills | `SKILL.md` does not exceed 500 lines |
| SKILL-05 | Skills | Only known file extensions at top level (`.md`, `.yml`, `.yaml`, `.sh`, `.py`, `.json`) |
| HOOK-01 | Hooks | Comment block documents exit codes (`# exit 0`, `# exit 2`) |
| HOOK-02 | Hooks | Bash hooks have `set -euo pipefail`; Python hooks have `try/except` |
| HOOK-03 | Hooks | Bash hooks use `INPUT=$(cat)` for stdin; Python uses `sys.stdin.read()` |
| HOOK-04 | Hooks | Hook exits with valid code (0, 1, or 2) |
| AGENT-01 | Agents | Every agent dir has `agent.yml` |
| AGENT-02 | Agents | `agent.yml` has `name:`, `description:` (≤300 chars), and `tools:` |
| AGENT-03 | Agents | `tools:` values are valid Claude Code tool names |
| AGENT-04 | Agents | Optional fields are non-empty if present |
| STD-01 | Standards | Every `path:` in `index.yml` resolves to an existing `.md` file |
| STD-02 | Standards | Paths are relative and reference `.md` files only |
| STD-03 | Standards | Each standard entry has a non-empty `triggers:` list |
| STD-04 | Standards | Standard `.md` files have a title (`# `) and sections (`## `) |

## Resources

- `docs/HARNESS_SPEC.md` — Complete invariant definitions, rationale, and fix guidance
- `scripts/entropy-scan.sh` (in this skill's scripts/ directory) — Executable implementation (single source of truth)
- `tests/test_entropy_scan.sh` (in this skill's tests/ directory) — Fixture-based test suite
- The project-health skill — Integration that runs entropy-scan as part of health checks

## Out of Scope

- Fixing violations automatically (report only)
- Checking runtime behaviour of skills/hooks (structure validation only)
- Performance profiling or optimisation
- Validating files outside the harness directories (see harness adapter for exact paths)
