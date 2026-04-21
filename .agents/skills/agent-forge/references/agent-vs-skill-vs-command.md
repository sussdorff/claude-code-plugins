# Agent vs Skill vs Command: Decision Guide

This reference helps determine when to use agents, skills, or commands in Claude Code.

## Quick Decision Tree

```
Does the user need to INVOKE it explicitly?
├─ YES → Is it a simple, direct operation?
│  ├─ YES → Use COMMAND (slash command)
│  └─ NO → Use AGENT (with explicit invocation)
└─ NO → Should Claude decide when to use it?
   ├─ Provides procedural knowledge/workflows → Use SKILL
   └─ Performs specialized multi-step tasks → Use AGENT (auto-delegation)
```

## Detailed Comparison

### Commands (Slash Commands)

**What they are:** User-invoked shortcuts that expand to prompts

**Use when:**
- User explicitly triggers the operation (`/deploy`, `/test`, `/review-pr`)
- Single, well-defined workflow
- Needs to accept parameters from user
- Should be discoverable in command palette

**Characteristics:**
- User-triggered only (never automatic)
- Can accept arguments
- Expands to a prompt in the main conversation
- Inherits main agent's context and tools

**Examples:**
- `/deploy-staging` - Deploy to staging environment
- `/review-pr 123` - Review pull request #123
- `/run-tests` - Execute test suite

**Storage:** `.claude/commands/` or plugin `commands/` directory

---

### Skills

**What they are:** Procedural knowledge packages that Claude invokes contextually

**Use when:**
- Claude should decide when to use it based on task
- Provides specialized knowledge or workflows
- Includes reusable resources (scripts, references, assets)
- Focuses on "how to do X" rather than "perform X for me"

**Characteristics:**
- Auto-invoked by Claude based on description
- Loads into main conversation context
- No isolated context window
- Can include bundled resources
- Progressive disclosure (metadata → SKILL.md → resources)

**Examples:**
- `database-query` - How to query company database with schema docs
- `code-review` - Code review guidelines and checklist
- `pdf-processing` - PDF manipulation with helper scripts

**Storage:** `.claude/skills/` or plugin `skills/` directory

---

### Agents (Subagents)

**What they are:** Specialized AI assistants with isolated context and custom system prompts

**Use when:**
- Need isolated context (prevent main conversation pollution)
- Complex, multi-step specialized task
- Requires custom system prompt and behavior
- Needs different tool permissions than main agent
- Part of multi-agent workflow/pipeline

**Characteristics:**
- Can be auto-delegated OR explicitly invoked
- Isolated context window (separate from main conversation)
- Custom system prompt
- Configurable tool access
- Can specify model (Haiku/Sonnet/Opus)
- Reusable across projects

**Examples:**
- `code-reviewer` - Isolated code review analysis
- `test-runner` - Run tests and analyze failures
- `pm-spec` - Write specifications from requirements
- `meta-agent` - Generate new agent configurations

**Storage:** `.claude/agents/` or plugin `agents/` directory

---

## When to Use Each: Decision Matrix

| Scenario | Recommendation | Reasoning |
|----------|----------------|-----------|
| User wants `/commit` shortcut | **Command** | Explicit user trigger, simple workflow |
| User wants "help me write better commit messages" | **Skill** | Provides knowledge Claude uses contextually |
| User wants "review this code in isolation" | **Agent** | Complex task needing isolated context |
| Deploy to production workflow | **Command** | User-triggered, needs explicit confirmation |
| Database schema documentation | **Skill** | Reference knowledge for queries |
| Security audit analysis | **Agent** | Complex analysis with focused context |
| Format code with prettier | **Command** | Simple, direct operation |
| Company coding standards | **Skill** | Knowledge Claude applies when coding |
| Run tests and analyze failures | **Agent** | Multi-step with isolated analysis |
| Generate API documentation | **Command** | User-triggered document generation |
| API design patterns | **Skill** | Knowledge for designing APIs |
| Architecture review | **Agent** | Complex specialized review |

---

## Hybrid Patterns

### Command + Skill
Command triggers workflow that uses skill's knowledge:
- `/review` command invokes review, uses `code-review` skill for guidelines

### Command + Agent
Command explicitly invokes an agent:
- `/security-audit` command delegates to `security-auditor` agent

### Agent + Skill
Agent uses skill's knowledge in isolated context:
- `test-runner` agent uses `testing-patterns` skill

### Multi-Agent Pipeline
Agents coordinate sequentially:
- `pm-spec` → `architect-review` → `implementer-tester`

---

## Tool Access Patterns

### Commands
- Inherit all tools from main conversation
- Cannot restrict tool access

### Skills
- Inherit all tools from main conversation
- Cannot restrict tool access
- Can bundle scripts that execute independently

### Agents
- **Configurable tool access** via `tools:` frontmatter
- Grant only necessary tools for security/focus
- Can omit `tools:` field to inherit all tools
- Examples:
  - Read-only agent: `tools: Read, Grep, Glob`
  - Implementation agent: `tools: Read, Write, Edit, Bash, Grep, Glob`
  - Research agent: `tools: Read, WebFetch, WebSearch`

---

## Context Management

### Commands
- Expand in main conversation context
- Add to context window
- No isolation

### Skills
- Load into main conversation when triggered
- SKILL.md body loaded (<5k words recommended)
- References loaded as needed by Claude
- Scripts can execute without loading

### Agents
- **Isolated context window** (key benefit!)
- Separate from main conversation
- Prevents context pollution
- Results returned to main conversation
- Ideal for complex subtasks

---

## Model Selection

### Commands
- Use main conversation model
- No configuration

### Skills
- Use main conversation model
- No configuration

### Agents
- **Configurable model** via `model:` frontmatter
- Options: `haiku`, `sonnet`, `opus`, `inherit`
- Default: `sonnet` if not specified
- Strategy:
  - Haiku: Fast, cost-effective for routine tasks (90% quality, 2x speed, 3x cost savings)
  - Sonnet: Balanced for most specialized tasks
  - Opus: Complex reasoning, orchestration
  - Inherit: Match main conversation model

---

## Best Practices Summary

**Use Commands for:**
- User-triggered shortcuts
- Simple workflows
- Operations needing explicit user control

**Use Skills for:**
- Procedural knowledge
- Reusable workflows
- Domain expertise
- Bundled resources (scripts, docs, templates)

**Use Agents for:**
- Complex specialized tasks
- Isolated analysis
- Custom system prompts
- Restricted tool access
- Multi-agent pipelines
- Token-efficient specialized roles

---

## Migration Patterns

### From Command to Agent
If your command has become complex:
- Convert to agent for isolated context
- Add custom system prompt for specialized behavior
- Configure specific tools only

### From Skill to Agent
If your skill needs:
- Isolated context (prevent pollution)
- Different tool permissions
- Custom model selection
- Complex multi-step workflow

### From Agent to Skill
If your agent:
- Doesn't need isolated context
- Primarily provides knowledge vs performs tasks
- Should influence main conversation context
