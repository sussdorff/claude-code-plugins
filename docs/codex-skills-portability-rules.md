# Codex Skills Portability Rules

This document defines the portability contract for splitting a skill into a portable core and a harness-specific adapter.

## Rule 1: Portable core (`SKILL.md`)

The portable core contains instructions that should work for any capable agent runtime:

- Use generic language for tools, workflows, and data sources.
- Prefer relative repository paths such as `docs/specs/` over harness-home paths.
- Describe fallbacks when an optional capability is unavailable.
- Keep the main workflow readable without requiring harness-specific context.

Portable cores MUST NOT include:

- Named `mcp__...` tool invocations
- `~/.claude/...` paths
- Slash-command invocation syntax such as `/spec-developer`
- Harness-specific agent names such as `bead-orchestrator` or `session-close`

## Rule 2: Harness adapter (`SKILL.<harness>-adapter.md`)

The harness adapter contains the mechanics that only apply to one runtime:

- Named MCP tools and their exact invocation syntax
- Harness-specific filesystem paths, home directories, or config files
- Slash-command examples or command-router syntax
- Harness-specific agents, orchestration hooks, or session tools

The adapter supplements the portable core; it does not replace it.

## Rule 3: Naming convention

Harness adapters use the sibling naming convention `SKILL.<harness>-adapter.md`.

Examples:

- `SKILL.claude-adapter.md`
- `SKILL.codex-adapter.md`

## Rule 4: Graceful fallback

Every harness-specific step must have a graceful fallback in `SKILL.md`.

That means the portable core should say what to do when:

- the bug log is absent
- the event log is unavailable
- cross-session memory is unsupported
- a harness-specific planner or orchestrator does not exist

The core stays usable even when the adapter is never read.

## Rule 5: YAML frontmatter metadata

Not all YAML frontmatter keys are portable. Classify each key before placing it:

**Portable frontmatter keys** (safe in `SKILL.md`):

- `name` — skill identifier, harness-agnostic
- `description` — human-readable purpose, harness-agnostic
- `tags` — categorization labels, harness-agnostic

**Harness-specific frontmatter keys** (must go in `SKILL.<harness>-adapter.md` only):

- `model:` — selects a Claude model (e.g. `opus`, `inherit`); meaningless outside Claude Code
- `disable-model-invocation:` — Claude Code routing flag; no equivalent in other runtimes
- `argument-hint:` — populates Claude Code's slash-command UI hint; harness-specific display metadata

**Template variables**:

- `$ARGUMENTS` — a Claude Code template variable that is replaced at invocation time. It MUST NOT appear in `SKILL.md`. Replace it with plain prose describing what arguments the skill accepts.

## Pilot Skills

| Skill | Portable core keeps | Claude adapter keeps |
|------|------|------|
| `bug-triage` | 4-phase workflow, fallback investigation steps, `bd` and test commands | `buglog.py`, `~/.claude/events.db`, `mcp__open-brain__search`, `/event-log` |
| `spec-developer` | Q&A workflow, spec generation rules, default `docs/specs/` output path | `~/.claude/CLAUDE.md`, Claude save-path override, slash-command examples |
| `project-context` | Context-generation workflow, `docs/project-context.md`, orchestration-agnostic wording | `bead-orchestrator`, `session-close`, related Claude slash-command integrations |

## Checklist

Use this checklist before considering a skill split complete:

- No `mcp__` tool names appear in `SKILL.md`
- No `~/.claude/` paths appear in `SKILL.md`
- No slash-command invocation syntax appears in `SKILL.md`
- No `bead-orchestrator` or `session-close` names appear in `SKILL.md`
- Every harness-specific step has a fallback in `SKILL.md`
- Harness details live only in `SKILL.<harness>-adapter.md`
- No `model:` or `disable-model-invocation:` frontmatter keys in `SKILL.md`
- No `$ARGUMENTS` template variable in `SKILL.md`
