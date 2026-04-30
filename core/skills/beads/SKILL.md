---
name: beads
model: sonnet
description: >-
  Dispatch bead implementation to the full implementation orchestrator (Phase 0–16 end-to-end
  including final closeout) or a quick-fix agent (lightweight, Phase 0–5 end-to-end including
  final closeout). Use when implementing a bead by ID, or to list ready beads.
  Triggers on implementiere bead, arbeite an bead, slice bead, bead zu gross.
requires_standards: [english-only]
---

# Beads Dispatcher

> **Context:** Full beads workflow (commands, phases, MoC rules, final closeout protocol) is
> injected at session start via the SessionStart hook — no need to repeat it here.

**Rules:** Never use `bd edit`. Never guess bead ID prefixes — `bd show 9yt` works with the hash only.

## Dispatch Table

| ARGUMENTS | Action |
|-----------|--------|
| `<bead-id>` | Auto-route: quick-fix (XS/S bug/chore/task) or full orchestrator |
| `<bead-id> --full` | Force full implementation orchestrator (skip auto-routing) |
| `<bead-id> --quick` | Force `quick-fix` agent (skip auto-routing) |
| `<bead-id> --dry-run` | Spawn orchestrator with `--dry-run` |
| `<bead-id> --skip-tests` | Spawn orchestrator with `--skip-tests` |
| `<bead-id> --skip-slicing` | Spawn orchestrator with `--skip-slicing` |
| *(empty)* | Show ready beads (cached or live), let user pick |

## If bead ID in ARGUMENTS

### Step 1: Auto-Route (unless `--full` or `--quick` forced)

```bash
bd show <id> --json | jq -r '.type, .metadata.effort // ""'
```

**Quick-fix routing** (spawn `quick-fix` agent):
- `effort` is `micro` or `small` AND `type` is `bug`, `chore`, or `task`

**Full orchestrator** (spawn the configured implementation orchestrator):
- `type: feature` (any effort)
- `effort` is `medium`, `large`, or `xl`
- `effort` is **empty** (orchestrator will auto-estimate and reroute to quick-fix if appropriate)

**Note:** When effort is empty, the full implementation orchestrator runs a haiku estimator in Phase 0. If the
estimated effort is micro/small and type is bug/chore/task, it returns `REROUTE_QUICK_FIX`.
In that case, spawn the quick-fix agent as a follow-up.

### Step 2: Spawn the agent

**Quick-fix path:**
```
Invoke the configured quick-fix implementation helper with:
  Bead ID: {BEAD_ID}
  Expectation: run Phase 0 through Phase 5 end-to-end, including final closeout.
```

**Full orchestrator path:**
```
Invoke the configured full implementation orchestrator with:
  Bead ID: {BEAD_ID}
  Flags: {FLAGS}
  Expectation: run Phase 0 through Phase 16 end-to-end, including final closeout.
```

Announce the routing decision: "Routing {BEAD_ID} → quick-fix (XS bug)" or "Routing {BEAD_ID} → full orchestrator (feature, M)".

## If ARGUMENTS is empty

Check cache first:
1. If the harness bead cache exists and is < 1h old and no dirty marker exists:
   → Read and display `ready` list from cache. Note: "(cached <N>min ago)"
2. Otherwise:
   → Run `bd ready` live, show results

Prompt: "Which bead? Invoke the beads skill with `<id>` to start."
