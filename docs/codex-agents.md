# Codex Agents

This document covers the tracked Codex agent sync path in this repository.
For the related skill surface, see
[`docs/codex-skills.md`](codex-skills.md).

## Layout

Codex agents use a three-surface layout:

- `dev-tools/codex-agents/`
  Tracked source of truth. Edit custom Codex agent TOMLs here.
- `.codex/agents/`
  Repo-scoped export surface. This is the project-local Codex discovery path.
- `~/.codex/agents/`
  Optional user-scoped mirror for the local machine.

Edit once in `dev-tools/codex-agents/`, then sync the repo and user targets.

## Discovery Helper

Use the inventory helper to inspect the tracked agent set:

```bash
python3 scripts/codex_agents.py
python3 scripts/codex_agents.py --json
```

## sync-codex-agents

`scripts/sync-codex-agents` copies every tracked agent source into
`.codex/agents/` and optionally into `~/.codex/agents/`.

### Basic repo sync

```bash
scripts/sync-codex-agents
```

### Also sync the user-scoped Codex agent directory

```bash
scripts/sync-codex-agents --user
```

### Sync a subset

```bash
scripts/sync-codex-agents --agents session-close,bead-orchestrator
```

### Dry-run

```bash
scripts/sync-codex-agents --dry-run
scripts/sync-codex-agents --user --dry-run
```

### Check mode

`--check` verifies that the tracked sources match the repo and optional user
targets without writing files. It exits 0 when all selected agents are in sync
and 1 when any selected target differs.

```bash
scripts/sync-codex-agents --check
scripts/sync-codex-agents --check --user
```

Example output when out of sync:

```text
  [ok]   repo-scoped: session-close
  [DIFF] repo-scoped: bead-orchestrator  (run sync-codex-agents to update)

Out of sync (1 target(s)):
  - repo:bead-orchestrator
```

## Relationship To Skill Sync

Claude and Codex parity now uses two parallel sync flows:

- `scripts/sync-codex-skills`
  Portable skill cores from the monorepo into `.agents/skills/` and optionally
  `~/.codex/skills/`
- `scripts/sync-codex-agents`
  Tracked custom Codex agents into `.codex/agents/` and optionally
  `~/.codex/agents/`

Run both when changing shared Codex surfaces.
