# Codex Skills

This document covers the full-fleet Codex skill export in this repository.
For the rollout history and design rationale, see
[`docs/codex-skills-rollout-plan.md`](codex-skills-rollout-plan.md).
For tracked Codex agents, see [`docs/codex-agents.md`](codex-agents.md).
For the governing architectural principle, see
[`docs/architecture/dev-repo-principle.md`](architecture/dev-repo-principle.md).

## Dev-Repo Principle

This repository is **dev-only**. Running `rm -rf $(pwd)` MUST leave Codex fully
operational. The only sync target is the user-scoped Codex skills directory:

- `~/.codex/skills/` (preferred)
- `~/.agents/skills/` (fallback, if the above does not exist)

There is **no in-repo mirror**. `.agents/skills/` does not exist in this repo and
is gitignored. The mirror pattern caused drift and CI failures — see CCP-h8h.

## sync-codex-skills

`scripts/sync-codex-skills` discovers every skill source in the monorepo and
copies the Codex-facing export directly into the user-scoped Codex directory.

Discovery is dynamic. The script scans the canonical skill roots:

- `beads-workflow/`
- `business/`
- `content/`
- `core/`
- `dev-tools/`
- `infra/`
- `medical/`
- `meta/`

Skills below `tests/`, `fixtures/`, `.claude/`, `.agents/`, or `.codex/` are
excluded from the export inventory.

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

If neither exists, the script prints a warning and exits 1. Create one of these
directories first, then re-run.

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

### Sync to the user-scoped Codex directory

```bash
scripts/sync-codex-skills
```

### Sync a subset of skills

```bash
scripts/sync-codex-skills --skills project-context,beads,codex
```

### Dry-run

```bash
scripts/sync-codex-skills --dry-run
```

### Check mode

`--check` verifies that the user-scoped target is in sync with the canonical
sources without writing files. It exits 0 when everything is in sync and 1 when
any exported skill differs.

```bash
scripts/sync-codex-skills --check
```

Example output when out of sync:

```text
  [ok]   user-scoped (/Users/you/.codex/skills): project-context
  [DIFF] user-scoped (/Users/you/.codex/skills): beads  (run sync-codex-skills to update)

Out of sync (1 target(s)):
  - user:beads
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
