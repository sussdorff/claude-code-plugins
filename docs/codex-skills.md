# Codex Skills

This document covers the sync tooling for the pilot Codex skills in this repository.
For the broader rollout plan and design rationale, see
[`docs/codex-skills-rollout-plan.md`](codex-skills-rollout-plan.md).

## sync-codex-skills

`scripts/sync-codex-skills` copies selected pilot skills from their plugin-scoped
source (`dev-tools/skills/<name>/`) into the repo-scoped Codex export layer
(`.agents/skills/`) and optionally into a user-scoped Codex skills directory.

### Why a sync script instead of symlinks?

Symlinks create silent coupling between two directory trees — a change in the
plugin source appears in `.agents/skills/` without any explicit action, which makes
it hard to tell what Codex actually loaded at a given point in time. A copy-based
sync keeps the export layer explicit: you can inspect `.agents/skills/` in isolation,
diff it against the source, and commit its contents independently.

### Pilot skills

| Skill | Source |
|---|---|
| `project-context` | `dev-tools/skills/project-context/` |
| `spec-developer` | `dev-tools/skills/spec-developer/` |
| `bug-triage` | `dev-tools/skills/bug-triage/` |

### User-scoped target discovery (Phase 0)

The script auto-detects the user Codex skills directory in this order:

1. `~/.codex/skills/`
2. `~/.agents/skills/`

If neither exists, user-scoped operations are skipped with a warning (never a hard
failure). As of 2026-04-20, `~/.codex/skills/` is the confirmed active Codex load
path on this machine.

### Usage

#### Basic repo-scoped sync (default)

Copies all three pilot skills into `.agents/skills/`:

```bash
scripts/sync-codex-skills
```

#### Also sync to user-scoped Codex directory

Copies to `.agents/skills/` **and** to the resolved user-scoped target
(e.g. `~/.codex/skills/`):

```bash
scripts/sync-codex-skills --user
```

The script prints which user-scoped directory it resolved and wrote to.

#### Sync a subset of skills

```bash
scripts/sync-codex-skills --skills project-context,bug-triage
```

#### Dry-run (no files written)

```bash
scripts/sync-codex-skills --dry-run
scripts/sync-codex-skills --user --dry-run
```

#### Check mode (CI / pre-commit)

Diffs source against target(s) without writing anything. Exits 0 if all targets
are in sync, exits 1 if any file differs.

```bash
# Check repo-scoped only
scripts/sync-codex-skills --check

# Check both repo-scoped and user-scoped
scripts/sync-codex-skills --check --user
```

Example output when out of sync:

```
  [ok]   repo-scoped: project-context
  [DIFF] repo-scoped: spec-developer  (run sync-codex-skills to update)
  [ok]   repo-scoped: bug-triage

Out of sync (1 target(s)):
  - repo:spec-developer
```

---

## Wiring --check into pre-commit

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: sync-codex-skills-check
        name: Codex skills in sync
        language: script
        entry: scripts/sync-codex-skills
        args: [--check]
        pass_filenames: false
        # Only run when plugin skill sources or the .agents export layer change
        files: ^(dev-tools/skills/(project-context|spec-developer|bug-triage)|\.agents/skills)/
```

To also enforce the user-scoped copy (useful on developer machines but not in CI):

```yaml
        args: [--check, --user]
```

---

## Wiring --check into GitHub Actions

```yaml
# .github/workflows/codex-skills-check.yml
name: Codex skills sync check

on:
  push:
    paths:
      - 'dev-tools/skills/project-context/**'
      - 'dev-tools/skills/spec-developer/**'
      - 'dev-tools/skills/bug-triage/**'
      - '.agents/skills/**'
  pull_request:
    paths:
      - 'dev-tools/skills/project-context/**'
      - 'dev-tools/skills/spec-developer/**'
      - 'dev-tools/skills/bug-triage/**'
      - '.agents/skills/**'

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check Codex skills are in sync
        run: scripts/sync-codex-skills --check
```

The user-scoped target (`--user`) is intentionally omitted from CI — user home
directories do not exist in CI runners.
