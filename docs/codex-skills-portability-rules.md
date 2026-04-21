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

**Note — multi-harness conventions files**: When a project ships both `CLAUDE.md` and `AGENTS.md`
(one per harness), the correct portable pattern is to **load all found conventions files and
concatenate them with a source header per file** (e.g. `# From CLAUDE.md` / `# From AGENTS.md`).
Do NOT pick only one file — silently dropping the other causes the skill to miss content that is
relevant for the running harness. If only one file exists, load that file alone (no regression).

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

**Runtime-consumed harness keys** (MUST remain in `SKILL.md`, adapter copy is documentation only):

Some frontmatter keys are harness-specific in semantics but must stay in `SKILL.md` because the
harness loader reads frontmatter **only from `SKILL.md`** — it never reads adapter files.
Moving these to the adapter silently drops runtime behavior.

- `model:` — selects the model used at dispatch time (e.g. `model: opus`). Codex-users can
  ignore it; Claude Code needs it in `SKILL.md` to route correctly.
- `disable-model-invocation:` — Claude Code routing flag. Same rule: must be in `SKILL.md`
  for the runtime to see it.

These keys MAY also be duplicated in the adapter for human documentation, but `SKILL.md` is
the **source of truth** for their values.

**Non-runtime harness display keys** (adapter only, safe to omit from `SKILL.md`):

- `argument-hint:` — populates the Claude Code slash-command UI hint; no runtime effect;
  adapter-only is fine.

**Template variables**:

- `$ARGUMENTS` — a Claude Code template variable replaced at invocation time. It MUST NOT
  appear in `SKILL.md`. Replace it with plain prose describing what arguments the skill accepts.

## Rule 6: No harness tool identifiers in portable instructions

Portable cores MUST NOT name the harness's concrete tool identifiers in imperative workflow
steps. Naming them creates instructions that are meaningless or misleading on other runtimes.

Examples of **forbidden** phrasing in `SKILL.md`:
- `Use Read and Glob tools (NOT grep/find/cat).`
- `Call the Bash tool to run the command.`
- `Read \`./CLAUDE.md\` (project context, …)`

Required replacement pattern:
1. **Tool references** → describe the *capability*: "load the file", "glob for matching files",
   "run the shell command". Let the harness adapter name the concrete tool.
2. **Harness convention files** (`CLAUDE.md`) → reference abstractly as "the project
   conventions file" or "load `./CLAUDE.md` or the equivalent conventions file for your
   harness (see your harness adapter for the exact path and read mechanism)."

The adapter may then say: "In Claude Code, use the `Read` tool to load `./CLAUDE.md`."

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
- No harness tool identifiers (`Read`, `Glob`, `Grep`, `Bash`, `Edit`, `Write`, etc.) appear in imperative instructions in `SKILL.md`
- No direct imperative to `Read ./CLAUDE.md` — reference abstractly as "project conventions file"
- Every harness-specific step has a fallback in `SKILL.md`
- Harness details live only in `SKILL.<harness>-adapter.md`
- Runtime-consumed keys (`model:`, `disable-model-invocation:`) remain in `SKILL.md` (Rule 5)
- Non-runtime display keys (`argument-hint:`) belong in adapter only
- No `$ARGUMENTS` template variable in `SKILL.md`
