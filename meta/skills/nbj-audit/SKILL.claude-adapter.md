---
harness: claude
skill: nbj-audit
---

# NBJ Audit — Claude Harness Adapter

This file supplements `SKILL.md` with Claude-specific paths.
A Codex user does NOT need to read this file.

## Harness Mode Detection (Claude)

In Claude Code projects, harness mode is detected when the cwd contains BOTH:
- `malte/skills/` — the skills directory
- `malte/agents/` — the agents directory

The `nbj-audit.sh` script checks for these paths automatically.

## History File (Claude)

Audit history is saved to `.beads/nbj-audit-history.json` relative to the project root.
This path assumes a beads-managed project. If `.beads/` is absent, save to `docs/nbj-audit-history.json`
or skip history persistence and note that delta tracking is unavailable.
