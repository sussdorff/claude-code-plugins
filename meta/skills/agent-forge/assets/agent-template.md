---
name: agent-name
description: Describe when and why to use this agent. Be specific with trigger keywords. Include phrases like "Use PROACTIVELY when..." or "Delegate when..." for better auto-delegation.
tools: Read, Grep, Glob
model: sonnet
color: blue
---

# Purpose

Define the agent's role and area of expertise. What specialized knowledge or capabilities does this agent provide?

## Instructions

Provide numbered, actionable steps that the agent should follow:

1. [First action - be specific and concrete]
2. [Second action - what to do with results from step 1]
3. [Third action - how to analyze or process]
4. [Fourth action - what decisions to make]
5. [Final action - how to format and deliver results]

## Script Boundaries

- Keep deterministic collection, parsing, polling, and transformation logic in bundled `scripts/`
- Use this prompt for judgment, prioritization, and branching only
- If a helper returns multiple fields or actionable failures, require the `execution-result` JSON envelope
- Use bare stdout only for single atomic values (for example one path, one UUID, or one count)

## Best Practices

List domain-specific best practices relevant to this agent's work:

- [Best practice 1 - specific to the domain]
- [Best practice 2 - common pitfalls to avoid]
- [Best practice 3 - quality criteria]
- [Best practice 4 - safety considerations]

## Pre-flight Checklist

Checks the agent MUST verify BEFORE taking action:

- [ ] [Precondition 1 — e.g., "Is the target file under version control?"]
- [ ] [Precondition 2 — e.g., "Are tests currently passing?"]
- [ ] [Precondition 3 — e.g., "Does the target project exist?"]

## Responsibility

| Owns | Does NOT Own |
|------|-------------|
| [What this agent is responsible for] | [What is explicitly out of scope] |
| [e.g., "Writing unit tests"] | [e.g., "Modifying production code"] |
| [e.g., "Reporting test results"] | [e.g., "Deploying changes"] |

## Output Format

Define the expected structure of the agent's response:

```
### Section 1: [Purpose]
[What information goes here]

### Section 2: [Details]
[What analysis or findings go here]

### Section 3: [Recommendations]
[What actionable items go here]

### Summary
[How to summarize the overall result]
```

## VERIFY

Shell commands the agent runs to verify its work before reporting success:

```bash
# [Describe what this verifies]
[command 1 — e.g., uv run pytest tests/ -x]

# [Describe what this verifies]
[command 2 — e.g., python3 scripts/validate-agent.py .claude/agents/my-agent/]
```

## LEARN

Documented anti-patterns and mistakes this agent type should avoid:

- **[Anti-pattern name]**: [What to avoid and why — e.g., "Never mock the function under test"]
- **[Anti-pattern name]**: [What to avoid and why — e.g., "Don't expand scope beyond the ticket"]
- **[Anti-pattern name]**: [What to avoid and why — e.g., "Don't report success without running verification"]

## Debrief

Before returning your final result, create a structured debrief documenting what you learned during this task. Include this section in your return message.

### What to include:

**Decisions** — What choices did you make and why? (patterns, approaches, trade-offs)
**Challenges & Resolutions** — What obstacles did you hit? How did you solve them?
**Surprises** — What was unexpected? Edge cases discovered?
**Follow-up Items** — What should be done next? Any technical debt created?

### Format:
```markdown
## Debrief

### Decisions
- [decision]: [rationale]

### Challenges & Resolutions
- [challenge]: [resolution]

### Surprises
- [unexpected finding]

### Follow-up Items
- [suggested next action]
```

---

## Template Customization Guide

### Frontmatter Fields

**name** (required)
- Use kebab-case (lowercase with hyphens)
- Be descriptive and specific
- Examples: `code-reviewer`, `test-runner`, `security-auditor`

**description** (required)
- Critical for auto-delegation - include trigger keywords!
- Be specific about WHEN to use the agent
- Include scenarios and use cases
- Use phrases: "Use PROACTIVELY when...", "Delegate when...", "MUST BE USED for..."
- Examples:
  - "Reviews code for security vulnerabilities. Use PROACTIVELY when code changes are made."
  - "Runs tests and analyzes failures. Use when implementing features or fixing bugs."

**tools** (optional, but recommended)
- Omit to inherit ALL tools (including MCP) - use with caution!
- Specify minimal required tools for security and focus
- Common patterns:
  - Read-only: `Read, Grep, Glob`
  - Implementation: `Read, Write, Edit, Bash, Grep, Glob`
  - Research: `Read, WebFetch, WebSearch, Grep, Glob`
  - Orchestration: `Agent, Read`
- See agent-frontmatter-reference.md for complete tool list

**model** (optional)
- Defaults to `inherit` (caller's model) if omitted — always set explicitly
- Options: `haiku` | `sonnet` | `opus` | `inherit`
  - `opus`: Full reasoning, best quality
  - `sonnet`: Balanced, good for moderate complexity (recommended default)
  - `haiku`: Fast, routine, deterministic tasks only (test running, formatting, linting)
  - `inherit`: Match caller's model (can cause surprises in pipelines)

**color** (optional)
- Visual identifier in CLI output
- Options: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`
- Suggested usage:
  - `red`: Critical/security agents
  - `green`: Success/test agents
  - `blue`: Analysis/review agents
  - `purple`: Orchestration/meta agents
  - `cyan`: Generation/creation agents

### System Prompt Guidelines

**Keep it lean (<3k tokens ideal)**
- Lightweight agents are more composable and perform better
- Move detailed documentation to references/ if needed
- Use numbered steps instead of verbose explanations
- One clear example is better than many similar ones

**Structure recommendations**:
1. **# Purpose** - Define role and expertise (1-2 sentences)
2. **## Instructions** - Numbered, actionable steps
3. **## Best Practices** - Domain-specific guidance
4. **## Pre-flight Checklist** - Checks before taking action (mandatory)
5. **## Responsibility** - Scope boundaries: owns vs does-not-own (mandatory)
6. **## Output Format** - Expected response structure
7. **## VERIFY** - Shell commands to verify work (mandatory)
8. **## LEARN** - Anti-patterns to avoid (mandatory)

**Writing style**:
- Use imperative/infinitive form (verb-first)
- Be specific and concrete
- Avoid vague language ("might", "could", "possibly")
- Include decision criteria
- Specify edge cases to handle

### Testing Your Agent

After creating, test auto-delegation:

```bash
# Try phrases that should trigger your agent
"Review this code" → code-reviewer
"Run the tests" → test-runner
"Audit for security issues" → security-auditor
```

If auto-delegation fails, improve the description with more specific trigger keywords.

### Common Patterns

**Single-Purpose Agent** (recommended starting point):
- Focused on one clear task
- Minimal tool set
- <3k tokens
- Examples: code-reviewer, test-runner, formatter

**Pipeline Agent** (part of workflow):
- Clear input/output expectations
- Status tracking (READY_FOR_*)
- Handoff to next agent
- Examples: pm-spec → architect-review → implementer-tester

**Orchestrator Agent** (coordinates others):
- Uses Task tool to delegate
- TodoWrite for tracking
- Minimal other tools
- Usually Sonnet or Opus model

**Meta-Agent** (generates other agents):
- Opus model for complex reasoning
- Write access to create files
- WebFetch for documentation
- Template generation capability

### Resources

See references/ directory for comprehensive guides:
- `agent-vs-skill-vs-command.md` - When to use agents vs other components
- `agent-frontmatter-reference.md` - Complete field documentation
- `agent-best-practices.md` - 2025 best practices and patterns
- `execution-result-contract.md` - Canonical JSON envelope for script-first workflows
- `agent-patterns.md` - Real-world examples and templates
