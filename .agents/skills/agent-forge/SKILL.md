---
name: agent-forge
description: >-
  Create and review agents (subagents). Use when creating specialized AI
  assistants, reviewing/auditing existing agents, deciding between agent vs skill vs
  command, or asking about agent best practices, multi-agent pipelines, and model selection.
  MUST BE USED when the user says "create agent", "new subagent", "review agent",
  "audit agent", "agent vs skill", or asks about multi-agent architecture.
disableModelInvocation: true
---

# Agent Forge

Create, review, and improve agents -- specialized AI assistants with isolated context windows, custom system prompts, and configurable tool permissions.

## When to Use

**Triggers:** "create an agent", "new subagent", "review agent", "audit my agents", "agent vs skill", "multi-agent pipeline", "agent best practices", "improve this agent"

**Use agents when:**
- Task needs isolated context (prevents main conversation pollution)
- Custom system prompt and behavior required
- Different tool permissions or model than main agent
- Building multi-agent workflows

**Not agents -- use instead:**
- Procedural knowledge, no isolation needed -> Skill
- User-triggered shortcut, simple workflow -> Command

Full decision tree: `references/agent-vs-skill-vs-command.md`

## Agent Creation Workflow

### Step 1: Confirm Agent is Appropriate

Verify against the decision criteria above. If skill or command fits better, say so and stop.

### Step 2: Design Purpose and Scope

Define before writing any code:
- Single, focused purpose (one clear goal)
- Trigger keywords for auto-delegation
- Minimal required tools
- Appropriate model for complexity level
- Standalone or part of a pipeline?

Patterns: single-purpose, pipeline stage, orchestrator, meta-agent.
Single responsibility keeps agents composable and token-efficient.

Details and real-world examples: `references/agent-patterns.md`

### Step 3: Initialize Agent File

```bash
# Creates <name>.md single-file agent with YAML frontmatter
python3 scripts/init-agent.py <agent-name>
```

Creates a single `.md` file with YAML frontmatter and system prompt.
See your harness adapter for the exact storage path and supported formats.

```
agents/<agent-name>.md    # Frontmatter + system prompt in one file (portable path)
```

### Step 4: Configure Frontmatter

```yaml
---
name: kebab-case-name              # Required
description: |                     # Required (critical for auto-delegation!)
  Describe when and why to use this agent.
  Use PROACTIVELY when [trigger scenario].
tools: Read, Grep, Glob           # Optional (omit = all tools)
model: sonnet                     # haiku|sonnet|opus|inherit (default: inherit)
---
```

**All supported frontmatter fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | — | Kebab-case identifier |
| `description` | string | Yes | — | When to delegate (critical for auto-delegation) |
| `tools` | list | No | all | Tools the agent can use |
| `disallowedTools` | list | No | — | Tools to deny from inherited set |
| `model` | string | No | inherit | `haiku`, `sonnet`, `opus`, `inherit`, or full model ID |
| `permissionMode` | string | No | default | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan` |
| `mcpServers` | list | No | — | MCP servers (inline or string references) |
| `hooks` | object | No | — | PreToolUse, PostToolUse, Stop hooks |
| `skills` | list | No | — | Skill names to preload |
| `memory` | string | No | — | `user`, `project`, or `local` |
| `maxTurns` | integer | No | — | Auto-stop after N turns |
| `color` | string | No | — | Visual identifier in CLI |

**Model selection:**
- `inherit` -- match caller's model (default when omitted)
- `haiku` -- fast, routine, deterministic (cheapest, use for simple transforms)
- `sonnet` -- balanced, good for moderate complexity work
- `opus` -- full reasoning power, best quality

**Important:** `model` defaults to `inherit`, not `opus`. An agent without `model:` gets whatever model the caller uses. Always set model explicitly to avoid surprises in pipelines.

**Tool access patterns:**
- Read-only: `Read, Grep, Glob`
- Implementation: `Read, Write, Edit, Bash, Grep, Glob`
- Research: `Read, WebFetch, WebSearch, Grep, Glob`
- Orchestration: `Agent, Read`

Minimal tools reduce attack surface and keep the agent focused.

Full field documentation: `references/agent-frontmatter-reference.md`

### Step 5: Write System Prompt

```markdown
# Purpose
[One clear sentence defining role and expertise]

## Instructions
1. [First concrete action]
2. [Second concrete action]

## Output Format
[Define expected response structure]
```

**Guidelines:**
- Keep lean (<3k tokens ideal, <10k max)
- Imperative form ("Analyze the code" not "You should analyze")
- Specific and concrete (avoid vague language)
- Define output format explicitly
- Include decision criteria for judgment calls
- Include a `## Tool Usage` section with WHEN/HOW per tool to reduce hallucinated tool choice

Token efficiency keeps agents composable -- lightweight agents combine better in pipelines.

Comprehensive writing guide: `references/agent-best-practices.md`

### Step 6: Validate

```bash
python3 scripts/validate-agent.py <agent-path>
```

Checks: frontmatter structure, required fields, name format, description quality, tool validity, model selection, token count, TODO markers.

### Step 7: Test

**Auto-delegation:** Try phrases that should trigger the agent. If it fails, improve description with more trigger keywords.

**Functional:** Verify tools are sufficient, model is appropriate, output matches expected format, context is properly isolated.

### Step 8: Deploy

**Storage locations:** See your harness adapter for the exact paths and priority order.
In general, agents can be stored at project-level (highest priority), user-level (personal use),
and plugin-level. Consult your harness documentation for the exact directory names.

Document usage examples, expected inputs, and when to use vs other agents.

## Agent Review Workflow

Use this when asked to review, audit, or improve an existing agent.

### Step 1: Load and Analyze

Read the agent `.md` file. Check:
- Is the YAML frontmatter well-formed?
- Does the description contain specific trigger keywords?
- Are tools minimal for the agent's purpose?
- Is the model appropriate for task complexity?

### Step 2: Run Validation

```bash
python3 scripts/validate-agent.py <agent-path>
```

Review errors and warnings. Fix errors first, then address warnings.

### Step 3: Assess Prompt Quality

Evaluate the system prompt against these criteria:
- **Clarity**: Are instructions specific and actionable?
- **Token efficiency**: Is the prompt lean or bloated?
- **Output format**: Is the expected output clearly defined?
- **Scope boundaries**: Does the agent know what it owns and doesn't own?
- **Edge cases**: Are decision criteria provided for ambiguous situations?

### Step 4: Check Auto-Delegation

Test whether the agent's description matches realistic user phrases. If the agent should auto-trigger but doesn't, the description needs more trigger keywords. If it triggers incorrectly, the description is too broad.

### Step 5: Report Findings

Structure findings as:
- **Errors** (must fix): broken metadata, missing required fields, security issues
- **Improvements** (should fix): weak description, excessive tools, wrong model tier
- **Suggestions** (nice to have): prompt restructuring, better output format

## Do NOT

- Create agents for tasks a skill or command handles better.
  Agents have context isolation overhead -- unnecessary for simple knowledge injection or user shortcuts.
- Grant more tools than minimally required.
  Excess tools expand attack surface and dilute agent focus.
- Write system prompts over 10k tokens.
  Attention dilution causes the agent to ignore instructions.
- Skip the validation step before deploying.
  Malformed frontmatter silently breaks auto-delegation.
- Omit the `model` field assuming it defaults to opus — it defaults to `inherit`.
  Always set model explicitly. In pipelines, an inherited model may not be what you expect.
- Default to haiku to save costs before verifying the agent works correctly.
  Premature downgrade causes subtle quality issues.

## Resources

### references/
| File | Content |
|------|---------|
| `agent-vs-skill-vs-command.md` | Decision tree, comparison table, hybrid patterns |
| `agent-frontmatter-reference.md` | All frontmatter fields, valid values, examples |
| `agent-best-practices.md` | Token efficiency, model economics, multi-agent patterns |
| `agent-patterns.md` | Complete agent files: single-purpose, pipelines, orchestrators |
| `troubleshooting.md` | Auto-delegation failures, tool issues, prompt sizing |

### scripts/
| Script | Purpose |
|--------|---------|
| `init-agent.py` | Initialize new agent with validated template |
| `validate-agent.py` | Check structure, frontmatter, token count |

### assets/
| File | Purpose |
|------|---------|
| `agent-template.md` | Starter template for manual creation |
