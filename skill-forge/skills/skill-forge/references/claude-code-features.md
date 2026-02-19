# Claude Code SKILL.md Features

Features beyond the base [Agent Skills](https://agentskills.io) specification, specific to Claude Code.

## Subagent Execution

### `context: fork`

Run the skill in an isolated subagent. The skill content becomes the subagent's task prompt. No access to conversation history.

```yaml
---
context: fork
---
```

Use for standalone tasks: research, code generation, analysis. NOT for reference/convention skills (subagent gets guidelines but no actionable task).

### `agent` Field

Specify which subagent type executes the forked skill. Only meaningful with `context: fork`.

```yaml
---
context: fork
agent: Explore
---
```

Options: `Explore` (read-only codebase search), `Plan` (architecture planning), `general-purpose` (full tool access), or any custom agent from `.claude/agents/`.

## Invocation Control

### `user-invocable`

```yaml
user-invocable: false  # Hide from /slash menu, Claude-only
```

Use for background knowledge skills users shouldn't invoke directly. Example: `legacy-system-context` explains how an old system works -- Claude should know this when relevant but `/legacy-system-context` isn't a meaningful action.

### `disable-model-invocation`

```yaml
disable-model-invocation: true  # Manual /name only, Claude never auto-invokes
```

Use for workflows with side effects: `/deploy`, `/commit`, `/send-message`. Prevents Claude from deciding to deploy because code looks ready.

## Tool Restriction

### `allowed-tools`

Space-delimited list of tools the skill can use without asking permission.

```yaml
allowed-tools: Read Grep Glob
```

Creates a scoped permission set. Useful for read-only analysis skills or skills that need specific CLI access like `Bash(gh *)`.

## Model Override

### `model`

Override the model for this skill's execution.

```yaml
model: haiku
```

Use for simple, high-frequency skills where speed matters more than capability.

## String Substitutions

### Arguments

| Variable | Description | Example |
|----------|-------------|---------|
| `$ARGUMENTS` | All arguments as a single string | `/skill-name foo bar` -> `foo bar` |
| `$ARGUMENTS[N]` | Argument by 0-based index | `$ARGUMENTS[0]` -> `foo` |
| `$N` | Shorthand for `$ARGUMENTS[N]` | `$0` -> `foo`, `$1` -> `bar` |

If `$ARGUMENTS` is not present in skill content, arguments are appended as `ARGUMENTS: <value>`.

```yaml
---
name: fix-issue
---
Fix GitHub issue $ARGUMENTS following our coding standards.
```

### Session Variable

| Variable | Description |
|----------|-------------|
| `${CLAUDE_SESSION_ID}` | Current session ID for logging, session-specific files |

## Dynamic Context Injection

### `` !`command` `` Syntax

Shell commands inside `` !`...` `` run before the skill content is sent to Claude. Output replaces the placeholder.

```yaml
---
name: pr-summary
context: fork
---
## Context
- PR diff: !`gh pr diff`
- Changed files: !`gh pr diff --name-only`

Summarize this pull request.
```

Processing order:
1. Each `` !`command` `` executes immediately (preprocessing)
2. Output replaces the placeholder in skill content
3. Claude receives fully-rendered prompt with actual data

This is NOT Claude executing commands -- Claude only sees the final rendered text.

## Hooks in Skills

Skills can define lifecycle hooks via the `hooks` frontmatter field. See the hooks documentation for configuration format. Hook events can trigger before/after tool use within the skill's execution context.

## Advanced Patterns

### Multi-Mode Skills

Route different user intents through a single skill using a mode table:

```markdown
| Mode | Trigger | Action |
|------|---------|--------|
| **Create** | "create X", "new X" | Scaffold and build |
| **Review** | "review X", "check X" | Evaluate quality |
| **Audit** | "audit all" | Fleet-wide scan |
```

### Script-Backed Skills

Bundle executable scripts for repeatable operations:

```markdown
Run `scripts/init.sh $ARGUMENTS` to scaffold the project.
```

Scripts handle the mechanical work; the SKILL.md handles orchestration and decision-making.

### Reference-Heavy Skills

For skills with deep domain knowledge:

```
SKILL.md           # Routing, overview, workflow skeleton (~200 lines)
references/
  spec.md          # Format specification
  guide.md         # Step-by-step how-to
  patterns.md      # Common patterns and examples
  checklist.md     # Quality criteria
```

SKILL.md points to references with clear "when to load" guidance. Total token budget: < 10000.
