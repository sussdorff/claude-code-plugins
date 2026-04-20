---
harness: claude
skill: spec-developer
---

# Spec Developer — Claude Harness Adapter

This file supplements `SKILL.md` with Claude-specific paths and skill integrations.

## Phase 0 Claude Extension

After reading `./CLAUDE.md`, also read `~/.claude/CLAUDE.md` (user global profile) for
user-level conventions and preferences.

## Phase 3 Claude Extension: Save Path

On Claude Code projects, save specs to `malte/plans/spec-<feature-name>.md` rather than
the default `docs/specs/` path, unless the project has a different convention in its `CLAUDE.md`.

## Skill Integrations (Claude-specific)

This skill is designed to work in a pipeline with other Claude skills:

- Runs *before*: `/epic-init`, `/plan` — pass the generated spec as input context
- Uses the project context from `/project-context` for informed questioning

## Invocation Examples (Claude slash-command syntax)

```
/spec-developer
/spec-developer "Patient intake FHIR workflow"
/spec-developer --explore "CLI log rotation tool"
/spec-developer --review malte/plans/spec-intake.md
```
