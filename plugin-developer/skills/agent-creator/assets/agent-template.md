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

## Best Practices

List domain-specific best practices relevant to this agent's work:

- [Best practice 1 - specific to the domain]
- [Best practice 2 - common pitfalls to avoid]
- [Best practice 3 - quality criteria]
- [Best practice 4 - safety considerations]

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
  - Orchestration: `Task, TodoWrite, Read`
- See agent-frontmatter-reference.md for complete tool list

**model** (optional)
- Defaults to `sonnet` if omitted
- Options: `haiku` | `sonnet` | `opus` | `inherit`
- Choose based on task complexity:
  - `haiku`: Fast, routine, deterministic tasks (test running, formatting, linting)
  - `sonnet`: Balanced for most specialized work (code review, implementation)
  - `opus`: Complex reasoning, meta-tasks, critical decisions (architecture, security audit)
- Cost: Haiku 3x cheaper than Sonnet, Sonnet 3x cheaper than Opus

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
4. **## Output Format** - Expected response structure
5. Optional sections: **## Analysis Framework**, **## Quality Criteria**, etc.

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
- `agent-patterns.md` - Real-world examples and templates
