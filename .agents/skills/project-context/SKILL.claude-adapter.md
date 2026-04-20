---
harness: claude
skill: project-context
model: inherit
argument-hint: "[--force] [--dry-run] [--section=<name>]"
---

# Project Context — Claude Harness Adapter

This file supplements `SKILL.md` with Claude-specific integrations and skill references.

## Integration: Bead Orchestrator

`docs/project-context.md` is consumed by the `bead-orchestrator` Phase 2 for context
injection into every implementation session. Keep this file updated when your architecture
changes significantly.

## Integration: Session Close

The `session-close` agent may append new architecture decisions after significant sessions.
Review its additions as part of your regular architecture maintenance.

## Related Claude Skills

- `/project-setup` — sets up a new project (run before this skill)
- `/project-health` — quality assessment (run independently)
- `/spec-developer` — deep feature specs (uses project-context as input context)

## Invocation (Claude slash-command syntax)

```
/project-context
/project-context --force
/project-context --dry-run
/project-context --section=module-map
```
