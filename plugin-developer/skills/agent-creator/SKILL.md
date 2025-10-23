---
name: agent-creator
description: Guide for creating Claude Code agents (subagents). Use when creating specialized AI assistants with isolated context, custom system prompts, and configurable tool access. Use when user wants to create agents, needs guidance on agent vs skill vs command decisions, or asks about agent best practices and patterns.
---

# Agent Creator

Guide for creating effective Claude Code agents (subagents) - specialized AI assistants with isolated context windows, custom system prompts, and configurable tool permissions.

## Overview

Agents are specialized AI assistants that Claude Code can delegate to for specific tasks. Unlike skills (which provide knowledge) or commands (which are user-triggered), agents operate in isolated context windows with custom behaviors, making them ideal for complex, specialized workflows.

**Key characteristics:**
- Isolated context (prevents main conversation pollution)
- Custom system prompts (specialized behavior)
- Configurable tool access (security and focus)
- Configurable model selection (Haiku/Sonnet/Opus)
- Can be auto-delegated or explicitly invoked

## When to Use Agents

Consult `references/agent-vs-skill-vs-command.md` for complete decision guidance.

**Use agents when:**
- Need isolated context for complex subtasks
- Require custom system prompt and behavior
- Want different tool permissions than main agent
- Building multi-agent workflows or pipelines
- Need model selection different from main conversation

**Use skills instead when:**
- Providing procedural knowledge or workflows
- No need for context isolation
- Should influence main conversation context

**Use commands instead when:**
- User explicitly triggers the operation
- Simple, direct workflow
- No need for specialized behavior

## Agent Creation Workflow

Follow this workflow for creating effective agents. Each step references detailed guidance in bundled resources.

### Step 1: Decide Agent is Appropriate

Before creating an agent, verify it's the right component type.

**Decision criteria:**
- Complex, specialized task? → Agent
- Procedural knowledge? → Skill
- User-triggered shortcut? → Command

**Reference:** `references/agent-vs-skill-vs-command.md` for complete decision tree with examples.

**Output:** Clear decision that agent is the right choice.

---

### Step 2: Design Agent Purpose and Scope

Define what the agent will do and its boundaries.

**Design questions:**
- What is the agent's single, focused purpose?
- What triggers its invocation (auto-delegation keywords)?
- What tools does it minimally need?
- What model is appropriate for complexity level?
- Is it standalone or part of a pipeline?

**Best practices:**
- Single responsibility (one clear goal)
- Token-efficient (<3k tokens ideal for system prompt)
- Minimal tool access (security and focus)
- Specific, keyword-rich description for auto-delegation

**Common patterns:**
- **Single-purpose:** code-reviewer, test-runner, security-auditor
- **Pipeline stage:** pm-spec → architect-review → implementer-tester
- **Orchestrator:** task-orchestrator (delegates to other agents)
- **Meta-agent:** meta-agent (generates other agents)

**Reference:** `references/agent-patterns.md` for real-world examples and complete agent files.

**Output:** Clear agent purpose, scope, and pattern.

---

### Step 3: Initialize Agent File

Use the init-agent.py script to create agent with proper structure.

**Usage:**
```bash
python3 scripts/init-agent.py <agent-name>
```

**Optional path specification:**
```bash
python3 scripts/init-agent.py <agent-name> --path .claude/agents/
```

**Example:**
```bash
python3 plugin-developer/skills/agent-creator/scripts/init-agent.py code-reviewer
```

The script will:
- Validate agent name (kebab-case)
- Create agent file with template structure
- Include frontmatter with all fields
- Add TODO markers for customization

**Alternative:** Copy `assets/agent-template.md` and customize manually.

**Output:** Agent file initialized at `.claude/agents/<agent-name>.md`.

---

### Step 4: Configure Frontmatter

Update the YAML frontmatter with agent metadata and configuration.

**Required fields:**

```yaml
name: agent-name          # Kebab-case identifier
description: |            # Specific, keyword-rich (critical for auto-delegation!)
  Describe when and why to use this agent.
  Use PROACTIVELY when [trigger scenario].
```

**Recommended fields:**

```yaml
tools: Read, Grep, Glob   # Minimal required tools (omit for all tools)
model: sonnet             # haiku|sonnet|opus|inherit (default: sonnet)
color: blue               # Visual identifier (optional)
```

**Model selection strategy:**
- `haiku`: Fast, routine, deterministic tasks (test running, formatting)
- `sonnet`: Balanced for most specialized work (code review, implementation) - DEFAULT
- `opus`: Complex reasoning, orchestration, critical decisions (architecture, security)
- `inherit`: Match main conversation model

**Tool access patterns:**
- Read-only (review, analysis): `Read, Grep, Glob`
- Implementation (coding): `Read, Write, Edit, Bash, Grep, Glob`
- Research: `Read, WebFetch, WebSearch, Grep, Glob`
- Orchestration: `Task, TodoWrite, Read`

**Reference:** `references/agent-frontmatter-reference.md` for complete field documentation with all options and examples.

**Output:** Properly configured frontmatter.

---

### Step 5: Write System Prompt

Create the agent's system prompt with clear instructions and guidelines.

**Structure recommendations:**

```markdown
# Purpose
[One clear sentence defining role and expertise]

## Instructions
1. [First concrete action]
2. [Second concrete action]
3. [etc.]

## Best Practices
- [Domain-specific best practice]
- [Common pitfall to avoid]

## Output Format
[Define expected response structure]
```

**Writing guidelines:**
- Keep lean (<3k tokens ideal, <10k max)
- Use numbered steps for clarity
- Be specific and concrete (avoid vague language)
- Include decision criteria
- Define output format explicitly
- Use imperative/infinitive form (not second person)

**Best practices (2025):**
- Token efficiency first (lightweight agents are more composable)
- Single responsibility (one clear goal)
- Minimal tools (only what's necessary)
- Right model (Haiku for routine, Sonnet for specialized, Opus for complex)
- Clear description (auto-delegation depends on it!)

**Reference:** `references/agent-best-practices.md` for comprehensive 2025 best practices including token efficiency, model economics, and multi-agent patterns.

**Output:** Complete agent system prompt.

---

### Step 6: Validate Agent

Use the validate-agent.py script to check structure and quality.

**Usage:**
```bash
python3 scripts/validate-agent.py .claude/agents/<agent-name>.md
```

**Example:**
```bash
python3 plugin-developer/skills/agent-creator/scripts/validate-agent.py .claude/agents/code-reviewer.md
```

The validator checks:
- ✅ YAML frontmatter structure
- ✅ Required fields (name, description)
- ✅ Name format (kebab-case)
- ✅ Description quality (trigger keywords)
- ✅ Tool validity
- ✅ Model selection
- ✅ Color validity
- ✅ System prompt structure
- ✅ Token count estimate
- ✅ TODO markers

**Output:** Validation report with errors (must fix) and warnings (should consider).

---

### Step 7: Test Agent

Test auto-delegation and functionality.

**Auto-delegation testing:**

Try phrases that should trigger your agent:

```bash
# Examples
"Review this code" → should trigger code-reviewer
"Run the tests" → should trigger test-runner
"Audit for security issues" → should trigger security-auditor
"Write a spec for this feature" → should trigger pm-spec
```

**Explicit invocation testing:**

```bash
"Use the <agent-name> agent to [task]"
"Have the <agent-name> agent [action]"
```

**Functional testing:**

- Does agent have necessary tools?
- Is model appropriate for task complexity?
- Does output match expected format?
- Is context properly isolated?
- Does it complete tasks successfully?

**Iteration:**

If auto-delegation fails:
1. Improve description with more trigger keywords
2. Add specific scenarios and use cases
3. Include phrases users might say
4. Test again

**Output:** Validated, working agent ready for use.

---

### Step 8: Document and Deploy

Finalize agent for team use or distribution.

**Documentation:**
- Add usage examples
- Document expected inputs
- Clarify when to use vs other agents
- Note any prerequisites or setup

**Storage locations:**
- **Project-level:** `.claude/agents/` (highest priority, checked into git)
- **User-level:** `~/.claude/agents/` (personal use)
- **Plugin:** `agents/` directory in plugin structure

**For plugin distribution:**
- Include agent in plugin `agents/` directory
- Reference in plugin.json if needed
- Document in plugin README
- Test installation process

**Output:** Deployed agent ready for use.

---

## Common Agent Patterns

See `references/agent-patterns.md` for complete examples with full agent files.

### Single-Purpose Agents

**Code Reviewer:**
- Tools: `Read, Grep, Glob` (read-only for safety)
- Model: `sonnet` (needs judgment)
- Focus: Security, performance, best practices

**Test Runner:**
- Tools: `Bash, Read, Grep, Glob, Edit` (execute and fix)
- Model: `haiku` (fast, cost-effective)
- Focus: Run tests, analyze failures, suggest fixes

### Multi-Agent Pipelines

**Three-stage development workflow:**

1. **pm-spec** (Sonnet) → Writes specifications
2. **architect-review** (Opus) → Validates design, produces ADR
3. **implementer-tester** (Sonnet) → Implements code and tests

Key elements:
- Clear handoff points (status transitions)
- Increasing tool permissions
- Slug-based artifact linking

### Meta-Agents

**Agent Generator:**
- Tools: `Write, Read, WebFetch, Grep, Glob`
- Model: `opus` (complex meta-reasoning)
- Focus: Generate new agent configurations
- Recursive: Agent creates agents

### Orchestrator Agents

**Task Orchestrator:**
- Tools: `Task, TodoWrite, Read`
- Model: `sonnet`
- Focus: Decompose complex tasks, coordinate specialized agents
- Pattern: Sonnet orchestrator + Haiku workers = 60-70% cost savings

---

## Model Selection Best Practices (2025)

### The Model Economics

**Haiku 4.5:**
- 90% of Sonnet quality for agentic tasks
- 2x faster execution
- 3x cost savings ($1/$5 vs $3/$15)
- Game-changer for agent economics

**Strategy:**
- Start with Haiku for routine tasks
- Use Sonnet for specialized work (default)
- Reserve Opus for critical reasoning
- Multi-model orchestration: Sonnet orchestrator + Haiku workers

**Reference:** `references/agent-best-practices.md` section on "Model Selection Strategy" for detailed patterns.

---

## Troubleshooting

### Agent Never Auto-Delegates

**Problem:** Agent never triggers automatically

**Solutions:**
- Improve description with specific trigger keywords
- Add phrases users might say
- Include "Use PROACTIVELY when..." or "MUST BE USED for..."
- Test with typical user requests

### Agent Lacks Necessary Tools

**Problem:** Agent can't perform required operations

**Solutions:**
- Add needed tools to `tools:` field
- Remember: omitting `tools` grants ALL tools
- Verify tool names are correct (case-sensitive)
- Check tool availability with `/tools` command

### System Prompt Too Large

**Problem:** Validator warns about token count

**Solutions:**
- Move detailed docs to references/ (loaded as needed)
- Use numbered lists instead of verbose explanations
- Remove repetitive examples
- Split into multiple specialized agents
- Target <3k tokens for best performance

### Agent Uses Wrong Model

**Problem:** Task too slow or too expensive

**Solutions:**
- Haiku: Routine, fast, deterministic (test running, formatting)
- Sonnet: Balanced, most tasks (default)
- Opus: Complex reasoning only (architecture, security audit)
- Check if Haiku sufficient (90% quality, 3x cheaper)

---

## Quick Reference

### Agent vs Skill vs Command

| Component | When to Use | Context | Invocation |
|-----------|-------------|---------|------------|
| **Agent** | Complex specialized task, isolated context | Separate | Auto or explicit |
| **Skill** | Procedural knowledge, workflows | Main conversation | Auto by Claude |
| **Command** | User-triggered shortcut | Main conversation | User explicit |

### Frontmatter Quick Reference

```yaml
---
name: kebab-case-name              # Required
description: Specific keywords...  # Required (critical for auto-delegation!)
tools: Read, Write, Bash           # Optional (omit for all tools)
model: haiku|sonnet|opus|inherit   # Optional (default: sonnet)
color: blue                        # Optional (visual identifier)
---
```

### Tool Access Patterns

```yaml
# Read-only (review/analysis)
tools: Read, Grep, Glob

# Implementation (coding)
tools: Read, Write, Edit, Bash, Grep, Glob

# Research
tools: Read, WebFetch, WebSearch, Grep, Glob

# Orchestration
tools: Task, TodoWrite, Read
```

### Model Selection

```yaml
model: haiku   # Fast, routine (test running, formatting) - 3x cheaper
model: sonnet  # Balanced, most tasks (default) - recommended
model: opus    # Complex reasoning only (architecture, security) - 3x expensive
model: inherit # Match main conversation
```

---

## Resources

This skill includes comprehensive references and utilities:

### scripts/

**init-agent.py** - Initialize new agent with proper template
- Validates agent name (kebab-case)
- Creates agent file with all frontmatter fields
- Includes TODO markers for easy customization

**validate-agent.py** - Validate agent structure and quality
- Checks frontmatter format and required fields
- Validates name, description, tools, model, color
- Estimates token count
- Reports errors (must fix) and warnings (should consider)

### references/

**agent-vs-skill-vs-command.md** - Complete decision guide
- Quick decision tree
- Detailed comparison table
- Use cases and examples
- Hybrid patterns
- Migration patterns

**agent-frontmatter-reference.md** - Complete field documentation
- All frontmatter fields explained
- Valid values and options
- Common patterns by agent type
- Best practices and examples
- Complete validation checklist

**agent-best-practices.md** - 2025 best practices
- Token efficiency principles
- Model selection strategy (Haiku 4.5 economics)
- Tool permission hygiene
- Multi-agent orchestration patterns
- Security patterns
- Performance optimization
- Common anti-patterns to avoid

**agent-patterns.md** - Real-world examples
- Single-purpose agents (code-reviewer, test-runner)
- Multi-agent pipelines (pm-spec → architect → implementer)
- Meta-agents (agent generator)
- Orchestrator agents (task coordination)
- Complete agent files with annotations

### assets/

**agent-template.md** - Starter template with customization guide
- Complete frontmatter structure
- System prompt sections
- Inline documentation
- Customization guidelines
- Common patterns

---

## Summary

Create effective Claude Code agents by:

1. **Decide**: Confirm agent is appropriate (vs skill or command)
2. **Design**: Define purpose, scope, and pattern
3. **Initialize**: Use init-agent.py script
4. **Configure**: Set frontmatter (description is critical!)
5. **Write**: Create system prompt (<3k tokens ideal)
6. **Validate**: Run validate-agent.py
7. **Test**: Verify auto-delegation and functionality
8. **Deploy**: Document and make available to team

**Key principles:**
- Token efficiency (<3k tokens)
- Single responsibility (one clear goal)
- Minimal tools (only necessary)
- Right model (Haiku for routine, Sonnet for specialized, Opus for complex)
- Clear description (specific trigger keywords for auto-delegation)

Leverage the bundled references for detailed guidance on decisions, configuration, best practices, and patterns throughout the agent creation process.
