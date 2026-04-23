# Codex Skills

This document covers the full-fleet Codex skill export in this repository.
For the rollout history and design rationale, see
[`docs/codex-skills-rollout-plan.md`](codex-skills-rollout-plan.md).
For tracked Codex agents, see [`docs/codex-agents.md`](codex-agents.md).

## sync-codex-skills

`scripts/sync-codex-skills` discovers every skill source in the monorepo,
builds a Codex-facing export tree in `.agents/skills/`, and optionally mirrors
the same surface into the active user-scoped Codex directory.

Discovery is dynamic. The script scans the canonical skill roots:

- `beads-workflow/`
- `business/`
- `content/`
- `core/`
- `dev-tools/`
- `infra/`
- `medical/`
- `meta/`

Skills below `tests/`, `fixtures/`, `.claude/`, or `.agents/` are excluded from
the export inventory.

### Why a sync script instead of symlinks?

Symlinks create silent coupling between two directory trees. A copy-based sync
keeps `.agents/skills/` explicit, diffable, and committable, which matters when
Claude and Codex should see the same repo skill surface.

### Metadata strategy

Codex UI metadata lives in `agents/openai.yaml`.

- If a source skill already ships `agents/openai.yaml`, the export keeps it.
- If not, the export layer generates a minimal file with:
  - `interface.display_name`
  - `interface.short_description`
  - `interface.default_prompt`

This keeps source skills portable while still giving Codex a complete metadata
surface.

### Codex-only opt-out

If a skill must stay Claude-only, mark it in `SKILL.md` frontmatter:

```yaml
codex-support: disabled
codex-support-reason: Requires Claude-only runtime mechanics that are not portable yet.
```

Such skills are excluded from the Codex export and reported as `cc-only` by the
skill-auditor compatibility scan.

### User-scoped target discovery

The sync script resolves the user target in this order:

1. `~/.codex/skills/`
2. `~/.agents/skills/`

If neither exists, `--user` prints a warning and skips user-scoped sync.

## Discovery Helper

Use the inventory helper to inspect what will be exported:

```bash
python3 scripts/codex_skills.py
python3 scripts/codex_skills.py --json
python3 scripts/codex_skills.py --all
```

Default output shows only Codex-exportable skills. `--all` includes skills
marked `codex-support: disabled`.

## Usage

### Basic repo-scoped sync

```bash
scripts/sync-codex-skills
```

### Also sync to the user-scoped Codex directory

```bash
scripts/sync-codex-skills --user
```

### Sync a subset of skills

```bash
scripts/sync-codex-skills --skills project-context,beads,codex
```

### Dry-run

```bash
scripts/sync-codex-skills --dry-run
scripts/sync-codex-skills --user --dry-run
```

### Check mode

`--check` verifies that the generated export matches the repo/user target(s)
without writing files. It exits 0 when everything is in sync and 1 when any
exported skill differs.

```bash
scripts/sync-codex-skills --check
scripts/sync-codex-skills --check --user
```

Example output when out of sync:

```text
  [ok]   repo-scoped: project-context
  [DIFF] repo-scoped: beads  (run sync-codex-skills to update)

Out of sync (1 target(s)):
  - repo:beads
```

## Auditing Codex Compatibility

The sync script exports everything that is not explicitly disabled. Portability
cleanup is tracked separately by the skill-auditor:

```bash
python3 meta/skills/skill-auditor/scripts/scan-codex-compat.py
python3 meta/skills/skill-auditor/scripts/scan-codex-compat.py --fail-on-needs-fix
```

The report classifies each skill as:

- `works-as-is`
- `needs-fix`
- `cc-only`

That makes it possible to keep Claude/Codex inventory parity while still
tracking which portable cores need more cleanup.

## Wiring --check Into Pre-commit

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
        files: ^((beads-workflow|business|content|core|dev-tools|infra|medical|meta)/.*SKILL.*|\.agents/skills/) 
```

To also enforce the user-scoped copy on developer machines:

```yaml
        args: [--check, --user]
```

## Wiring --check Into GitHub Actions

```yaml
# .github/workflows/codex-skills-check.yml
name: Codex skills sync check

on:
  push:
    paths:
      - 'beads-workflow/**'
      - 'business/**'
      - 'content/**'
      - 'core/**'
      - 'dev-tools/**'
      - 'infra/**'
      - 'medical/**'
      - 'meta/**'
      - '.agents/skills/**'
  pull_request:
    paths:
      - 'beads-workflow/**'
      - 'business/**'
      - 'content/**'
      - 'core/**'
      - 'dev-tools/**'
      - 'infra/**'
      - 'medical/**'
      - 'meta/**'
      - '.agents/skills/**'

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check Codex skills are in sync
        run: scripts/sync-codex-skills --check
```

The user-scoped target (`--user`) remains intentionally omitted from CI because
home-directory skill roots do not exist on runners.
