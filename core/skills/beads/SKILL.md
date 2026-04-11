---
name: beads
model: sonnet
description: >-
  Dispatch bead implementation to the bead-orchestrator agent (Phase 0–5 workflow).
  Use when implementing a bead by ID, or to list ready beads.
  Triggers on implementiere bead, arbeite an bead, slice bead, bead zu gross.
---

# Beads Dispatcher

> **Context:** Full beads workflow (commands, phases, MoC rules, session-close protocol) is
> injected at session start via the SessionStart hook — no need to repeat it here.

**Rules:** Never use `bd edit`. Never guess bead ID prefixes — `bd show 9yt` works with the hash only.

## Dispatch Table

| ARGUMENTS | Action |
|-----------|--------|
| `<bead-id>` | Spawn `bead-orchestrator` agent |
| `<bead-id> --dry-run` | Spawn orchestrator with `--dry-run` |
| `<bead-id> --skip-tests` | Spawn orchestrator with `--skip-tests` |
| `<bead-id> --skip-slicing` | Spawn orchestrator with `--skip-slicing` |
| *(empty)* | Show ready beads (cached or live), let user pick |

## If bead ID in ARGUMENTS

Spawn a `general-purpose` agent with this prompt:

```
Read ~/.claude/agents/bead-orchestrator/agent.md for your workflow instructions.

Bead ID: {BEAD_ID}
Flags: {FLAGS}

Execute the full orchestration workflow (Phase 0–5) for this bead.
```

## If ARGUMENTS is empty

Check cache first:
1. If `~/.claude/state/beads-cache.json` exists and is < 1h old and no `~/.claude/state/beads-cache.dirty` exists:
   → Read and display `ready` list from cache. Note: "(cached <N>min ago)"
2. Otherwise:
   → Run `bd ready` live, show results

Prompt: "Which bead? Run `/beads <id>` to start."
