# Codex Agents

This document covers the tracked Codex agent sync path in this repository.
For the related skill surface, see [`docs/codex-skills.md`](codex-skills.md).
For the governing architectural principle, see
[`docs/architecture/dev-repo-principle.md`](architecture/dev-repo-principle.md).

## Dev-Repo Principle

This repository is **dev-only**. Running `rm -rf $(pwd)` MUST leave Codex fully
operational. The only sync target is the user-scoped Codex agents directory:
`~/.codex/agents/`.

There is **no in-repo mirror**. `.codex/agents/` no longer exists in this repo
and is gitignored. The mirror pattern caused drift — see CCP-h8h.

## Layout

Codex agents use a two-surface layout:

- `dev-tools/codex-agents/`
  Canonical source of truth. Edit custom Codex agent TOMLs here.
- `~/.codex/agents/`
  User-scoped runtime directory. Codex CLI reads from here.

Edit once in `dev-tools/codex-agents/`, then sync to `~/.codex/agents/`.

## Discovery Helper

Use the inventory helper to inspect the tracked agent set:

```bash
python3 scripts/codex_agents.py
python3 scripts/codex_agents.py --json
```

## sync-codex-agents

`scripts/sync-codex-agents` copies every tracked agent source into `~/.codex/agents/`.

### Sync to user-scoped Codex directory

```bash
scripts/sync-codex-agents
```

### Sync a subset

```bash
scripts/sync-codex-agents --agents session-close,bead-orchestrator
```

### Dry-run

```bash
scripts/sync-codex-agents --dry-run
```

### Check mode

`--check` verifies that the tracked sources match the user-scoped target without
writing files. It exits 0 when all selected agents are in sync and 1 when any
selected target differs.

```bash
scripts/sync-codex-agents --check
```

Example output when out of sync:

```text
  [ok]   user-scoped (/Users/you/.codex/agents): session-close
  [DIFF] user-scoped (/Users/you/.codex/agents): bead-orchestrator  (run sync-codex-agents to update)

Out of sync (1 target(s)):
  - user:bead-orchestrator
```

## Relationship To Skill Sync

Claude and Codex parity uses two parallel sync flows:

- `scripts/sync-codex-skills`
  Portable skill cores from the monorepo into `~/.codex/skills/`
- `scripts/sync-codex-agents`
  Tracked custom Codex agents into `~/.codex/agents/`

Run both when changing shared Codex surfaces.
