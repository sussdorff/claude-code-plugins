---
name: beads
model: sonnet
description: >-
  Dispatch bead implementation to the bead-orchestrator (full, Phase 0–16 end-to-end
  including session-close) or quick-fix agent (lightweight, Phase 0–5 end-to-end including
  session-close). Use when implementing a bead by ID, or to list ready beads.
  Triggers on implementiere bead, arbeite an bead, slice bead, bead zu gross.
---

# Beads Dispatcher

> **Context:** Full beads workflow (commands, phases, MoC rules, session-close protocol) is
> injected at session start via the SessionStart hook — no need to repeat it here.

**Rules:** Never use `bd edit`. Never guess bead ID prefixes — `bd show 9yt` works with the hash only.

## Dispatch Table

| ARGUMENTS | Action |
|-----------|--------|
| `<bead-id>` | Auto-route: quick-fix (XS/S bug/chore/task) or full orchestrator |
| `<bead-id> --full` | Force full `bead-orchestrator` (skip auto-routing) |
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

**Full orchestrator** (spawn `bead-orchestrator` agent):
- `type: feature` (any effort)
- `effort` is `medium`, `large`, or `xl`
- `effort` is **empty** (orchestrator will auto-estimate and reroute to quick-fix if appropriate)

**Note:** When effort is empty, the bead-orchestrator runs a haiku estimator in Phase 0. If the
estimated effort is micro/small and type is bug/chore/task, it returns `REROUTE_QUICK_FIX`.
In that case, spawn the quick-fix agent as a follow-up.

### Step 2: Spawn the agent

**Quick-fix path:**
```
Agent(subagent_type="beads-workflow:quick-fix", prompt="
  Bead ID: {BEAD_ID}. Execute quick-fix workflow end-to-end: Phase 0 through Phase 5
  (session-close). Do not stop after any intermediate phase. Session-close auto-triggers
  in Phase 5.
")
```

**Full orchestrator path:**
```
Agent(subagent_type="beads-workflow:bead-orchestrator", prompt="
  Bead ID: {BEAD_ID}
  Flags: {FLAGS}
  Execute the full orchestration workflow end-to-end: Phase 0 through Phase 16
  (session-close). Do not stop after any intermediate phase. Session-close auto-triggers
  in Phase 16.
")
```

Announce the routing decision: "Routing {BEAD_ID} → quick-fix (XS bug)" or "Routing {BEAD_ID} → full orchestrator (feature, M)".

## If ARGUMENTS is empty

Check cache first:
1. If `~/.claude/state/beads-cache.json` exists and is < 1h old and no `~/.claude/state/beads-cache.dirty` exists:
   → Read and display `ready` list from cache. Note: "(cached <N>min ago)"
2. Otherwise:
   → Run `bd ready` live, show results

Prompt: "Which bead? Run `/beads <id>` to start."
