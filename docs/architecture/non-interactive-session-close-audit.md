# Non-Interactive Session-Close: Interactive Points Audit

**Bead:** CCP-k1m
**Date:** 2026-04-22
**Status:** Accepted

---

## Purpose

This document audits every interactive point in `core/agents/session-close.md` and
classifies each one so that a `--non-interactive` mode can apply deterministic defaults
without human input.

---

## Classification Scheme

| Label | Meaning |
|-------|---------|
| `needs-human` | Requires genuine human judgment; cannot be safely defaulted. Block and return structured response. |
| `can-default` | A safe deterministic default exists. Apply it automatically in non-interactive mode. |
| `can-pre-specify` | Caller can supply the value in the invocation prompt; fall back to a safe default if omitted. |

---

## Interactive Points Table

| # | Location | Interaction | Classification | Safe Default |
|---|----------|-------------|----------------|--------------|
| 1 | Step 5 — Review with user: unstaged / untracked files | Ask which files to stage | `can-default` | Auto-stage all `.git_state.unstaged[]` files; log untracked files as advisory |
| 2 | Step 5 — Review with user: bun audit `high`/`critical` | Ask whether to proceed despite vulnerabilities | `can-default` | Auto-proceed; log vulnerability list to bead notes via `bd update <id> --append-notes` |
| 3 | Step 6 — Conventional commit: determine type, scope, description | Interactive commit message construction with user | `can-pre-specify` | Use `BEAD_ID + BEAD_TITLE + type` from caller prompt; fallback: `chore: automated session close [bead-id]` |
| 4 | Step 6 — Stage files and commit | Confirm staged files before commit | `can-default` | Stage all files from `git_state.staged[]` plus any auto-staged unstaged files; commit without confirmation |
| 5 | Phase A — Learnings extraction subagent | May surface questions back to user | `can-default` | Run with `--non-interactive` context; subagent returns structured output without prompting |
| 6 | Step 16b — Close beads: missing close reason (exit 3) | For each `missing_reason[]` bead, compose a close reason | `can-default` | Auto-compose close reason from bead title + commit message; stamp and rerun |
| 7 | Step 14/15 — Second merge / feature merge: merge conflict | Conflict requires manual resolution | `needs-human` | Return structured BLOCKED response immediately |
| 8 | Step 16 — Push: screen locked | Push blocked by OS screen lock | `needs-human` | Return structured BLOCKED response immediately |
| 9 | Step 16a — Pipeline watch: CI pipeline failed | CI ran and failed; human must investigate | `needs-human` | Return structured BLOCKED response immediately |

---

## Non-Interactive Mode Protocol Reference

When `--non-interactive` is set (flag in prompt or `SESSION_CLOSE_NON_INTERACTIVE=1` env var):

1. **No interactive prompts.** Every interactive point uses its safe default from the table above.
2. **Structured BLOCKED response** is returned for any genuine `needs-human` condition
   (e.g. merge conflict, screen lock) — never deadlock waiting for input.
3. **Audit warnings** are logged to bead notes, not presented interactively.
4. **Commit message** is constructed from caller-supplied context or the fallback pattern.
5. **Resume detection** runs automatically and routes to the correct checkpoint.

See `core/agents/session-close.md § Non-Interactive Mode` for implementation details.
