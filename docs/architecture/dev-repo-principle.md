# Dev-Repo Principle: This Repository Is Dev-Only

**Adopted:** 2026-04-23 (CCP-h8h)

## The Invariant

```
rm -rf $(pwd)
```

Running the above on this repository MUST leave Codex and Claude Code fully
operational on the developer's machine. They re-fetch the repo via `git clone`
only when the developer wants to make changes — not as a precondition for
execution.

## What This Means

This repository is where plugins, skills, and agents are **developed and authored**.
It is the source from which humans and Claude/Codex evolve the marketplace plugins.

It is **NOT** the place where Codex or Claude reads skills/agents at runtime.

Runtime consumers (Codex CLI, Claude Code CLI, downstream agents) MUST read their
resources from user-scoped or system-scoped install locations:

- `~/.codex/skills/` — Codex user-scoped skill discovery path
- `~/.codex/agents/` — Codex user-scoped agent discovery path
- `~/.claude/plugins/` — Claude Code marketplace-installed plugins
- `~/.claude/skills/` — Claude Code user-scoped skills

These locations are populated by running:

```bash
scripts/sync-codex-skills    # syncs skills to ~/.codex/skills/
scripts/sync-codex-agents    # syncs agents to ~/.codex/agents/
claude plugins install ...   # installs plugins to ~/.claude/plugins/
```

## Implications

1. **No in-repo mirrors.** `.agents/skills/` and `.codex/agents/` no longer exist
   in this repo. They are gitignored. They MUST NOT be re-introduced.

2. **No symlinks back into the repo from runtime locations.** Sync = copy, never link.
   Linking would re-introduce the runtime dependency on the repo being present.

3. **The repo never imports its own skill/agent definitions at runtime.** Only
   build/sync scripts read from canonical paths in the repo.

4. **CI scans canonical paths only.** `.agents/` and `.codex/` do not exist, so
   they cannot fail CI. The `skill-audit.yml` workflow scans the canonical skill
   directories (`*/skills/<name>/SKILL.md`) using `meta/skills/skill-auditor/`.

5. **Sync is one-directional:** canonical source (in repo) → user-scoped target.
   Never the reverse.

6. **Session-close** still invokes `sync-codex-skills` after a plugin-touching
   commit, but the sync target is always user-scoped (`~/.codex/skills/`), never
   a directory inside this repo.

## Canonical Skill / Agent Sources

| Type | Canonical Location |
|------|--------------------|
| Marketplace skills | `*/skills/<name>/SKILL.md` (per plugin) |
| Codex agent TOML sources | `dev-tools/codex-agents/*.toml` |
| Claude Code agents | `core/agents/*.md` |
| Build / sync scripts | `scripts/sync-codex-*` |

## History and Context

Prior to CCP-h8h (2026-04-23), the repo maintained in-tree mirrors:

- `.agents/skills/` — populated by `scripts/sync-codex-skills`
- `.codex/agents/` — populated by `scripts/sync-codex-agents`

These mirrors caused:

1. **Drift** — every canonical skill change had to be re-synced or the mirror
   diverged silently.
2. **CI failures** — the mirror tree was scanned by `skill-audit.yml`, so even
   when canonical skills passed, stale mirror copies failed CI.
3. **Wrong source of truth** — a development repository should never host runtime
   artifacts that other tools depend on.

CCP-h8h removed both directories, gitignored them, updated all sync scripts to
target user-scoped paths only, and updated CI to scan canonical paths only.

## Testing

The invariant is enforced by `tests/test_dev_repo_principle.py`:

- Asserts `.agents/` and `.codex/` have no committed files.
- Asserts both directories are gitignored.
- Asserts no canonical source script references either path as a target.
- Asserts `sync-codex-skills` and `sync-codex-agents` define no `REPO_TARGET`.
- Asserts this document exists and references the `rm -rf` invariant.
