# Agent Frontmatter Reference

Complete reference for all agent frontmatter fields in Claude Code.

## Structure

Agent files use Markdown with YAML frontmatter:

```markdown
---
name: agent-name
description: When and why to use this agent
tools: Tool1, Tool2, Tool3
model: sonnet
color: blue
---

# Agent system prompt content here

... rest of agent instructions ...
```

## Required Fields

### `name` (Required)

**Type:** String
**Format:** kebab-case (lowercase with hyphens)
**Purpose:** Unique identifier for the agent

**Rules:**
- Must be unique across all agents
- Use kebab-case only (e.g., `code-reviewer`, not `Code Reviewer` or `code_reviewer`)
- Be descriptive and specific
- Keep concise (2-4 words ideal)

**Examples:**
```yaml
name: code-reviewer
name: test-runner
name: security-auditor
name: pm-spec
name: meta-agent
```

**Bad examples:**
```yaml
name: CodeReviewer      # Wrong: use kebab-case
name: code_reviewer     # Wrong: use hyphens not underscores
name: cr                # Too abbreviated
name: agent-for-reviewing-code-and-security  # Too long
```

---

### `description` (Required)

**Type:** String (can be multi-line)
**Purpose:** Determines when Claude delegates to this agent (critical for auto-delegation!)

**Rules:**
- Be specific about WHEN to use the agent
- Include triggering keywords and scenarios
- Use action-oriented language
- For auto-delegation: include "use PROACTIVELY" or "MUST BE USED"
- Write in third person for skills/agents
- Can be multi-line using YAML block scalars (`|` or `>`)

**Good description patterns:**

```yaml
# Pattern 1: Direct and specific
description: Reviews code for security vulnerabilities, performance issues, and best practices. Use proactively when code changes are made.

# Pattern 2: Use cases enumerated
description: Runs tests and analyzes failures. Use when: (1) implementing new features, (2) fixing bugs, (3) user requests test execution, or (4) preparing for commits.

# Pattern 3: Multi-line with clear triggers
description: |
  Generates complete Claude Code sub-agent configuration from user descriptions.
  Use this to create new agents. Use proactively when the user asks to create
  a new sub-agent.

# Pattern 4: Explicit must-use
description: Writes detailed specifications from user requirements. MUST BE USED at the start of new feature development before any implementation begins.
```

**Poor descriptions:**
```yaml
description: Helps with code    # Too vague
description: An agent          # Tells nothing
description: Reviews stuff     # Not specific enough
```

**Pro tip:** The description is like SEO for agents - include the exact phrases users might say!

---

## Optional Fields

### `tools` (Optional)

**Type:** Comma-separated string
**Default:** All available tools (if omitted)
**Purpose:** Restrict which tools the agent can access

**Rules:**
- Comma-separated list (e.g., `Read, Write, Grep`)
- **If omitted:** Agent inherits ALL available tools (including MCP tools)
- **Security principle:** Only grant necessary tools
- Tool names are case-sensitive

**Available core tools:**
- `Read` - Read files
- `Write` - Write new files
- `Edit` - Edit existing files
- `Bash` - Execute shell commands
- `Grep` - Search file contents
- `Glob` - Find files by pattern
- `WebFetch` - Fetch web content
- `WebSearch` - Search the web
- `Task` - Launch other agents
- `Skill` - Invoke skills
- `TodoWrite` - Manage todo lists
- `AskUserQuestion` - Ask clarifying questions
- `NotebookEdit` - Edit Jupyter notebooks
- Plus any MCP tools installed

**Common patterns:**

```yaml
# Read-only agent (research, analysis)
tools: Read, Grep, Glob, WebFetch, WebSearch

# Implementation agent (coding)
tools: Read, Write, Edit, Bash, Grep, Glob

# Review agent (analysis only)
tools: Read, Grep, Glob

# Orchestrator agent (delegates to others)
tools: Read, Task, TodoWrite

# Documentation agent
tools: Read, Write, Grep, Glob, WebFetch

# Test runner agent
tools: Read, Bash, Grep, Glob, Edit

# No restrictions (all tools)
# Simply omit the tools field entirely
```

**Best practice:** Start with minimal tools, add more only if needed. Token-efficient agents with focused tool sets are more reliable.

---

### `model` (Optional)

**Type:** String
**Default:** `sonnet` (if omitted)
**Purpose:** Specify which Claude model to use

**Valid values:**
- `haiku` - Claude Haiku 4.5 (fastest, most cost-effective)
- `sonnet` - Claude Sonnet 4.5 (balanced, default)
- `opus` - Claude Opus 4 (most capable, complex reasoning)
- `inherit` - Use same model as main conversation

**Model selection strategy (2025 best practices):**

```yaml
# Haiku: Fast, routine tasks (90% of Sonnet quality, 2x speed, 3x cost savings)
model: haiku
# Use for: test running, linting, formatting, simple reviews, routine checks

# Sonnet: Balanced for most specialized work (DEFAULT)
model: sonnet
# Use for: code review, implementation, moderate complexity analysis
# Can also omit - sonnet is default

# Opus: Complex reasoning, orchestration, critical decisions
model: opus
# Use for: architecture decisions, meta-agents, complex problem solving,
#         security-critical analysis

# Inherit: Match main conversation
model: inherit
# Use for: maintaining consistency with main agent model selection
```

**Examples by agent type:**

```yaml
# Test runner - speed matters, deterministic task
name: test-runner
model: haiku

# Code reviewer - needs good judgment
name: code-reviewer
model: sonnet

# Meta-agent - complex reasoning
name: meta-agent
model: opus

# Architecture reviewer - critical decisions
name: architect-review
model: opus

# Formatter - simple, fast
name: code-formatter
model: haiku
```

**Cost optimization pattern:**
```yaml
# Use Haiku workers with Sonnet orchestrator
# Saves 60-70% on costs while maintaining quality

# Orchestrator
name: task-orchestrator
model: sonnet
tools: Task, TodoWrite

# Workers
name: test-runner
model: haiku
tools: Bash, Read

name: linter
model: haiku
tools: Bash, Read, Edit
```

---

### `color` (Optional)

**Type:** String
**Default:** None (no color coding)
**Purpose:** Visual distinction in CLI output

**Valid values:**
- `red`
- `blue`
- `green`
- `yellow`
- `purple`
- `orange`
- `pink`
- `cyan`

**Usage tips:**
```yaml
# Color by function type
color: red      # Critical/security agents
color: green    # Success/validation agents
color: blue     # Analysis/review agents
color: yellow   # Warning/linting agents
color: purple   # Meta/orchestration agents
color: cyan     # Generation/creation agents
color: orange   # Performance/optimization agents
color: pink     # Documentation agents
```

**Examples:**
```yaml
name: security-auditor
color: red

name: test-runner
color: green

name: code-reviewer
color: blue

name: meta-agent
color: cyan
```

**Note:** Color is purely visual and doesn't affect agent behavior.

---

## Complete Examples

### Minimal Agent (required fields only)

```yaml
---
name: simple-reviewer
description: Reviews code for basic quality issues. Use when code changes are made.
---

Review the code for:
1. Syntax errors
2. Basic logic issues
3. Code style violations

Provide clear, actionable feedback.
```

### Typical Agent (common configuration)

```yaml
---
name: code-reviewer
description: Reviews code for security vulnerabilities, performance issues, and best practices. Use proactively when code changes are made or user requests review.
tools: Read, Grep, Glob
model: sonnet
color: blue
---

# Purpose

Expert code reviewer focusing on security, performance, and best practices.

## Instructions

1. Read all changed files
2. Analyze for security vulnerabilities
3. Check performance implications
4. Verify best practices adherence
5. Provide prioritized, actionable feedback
```

### Advanced Agent (full configuration)

```yaml
---
name: meta-agent
description: |
  Generates complete Claude Code sub-agent configuration from user descriptions.
  Use this to create new agents. Use PROACTIVELY when the user asks to create
  a new sub-agent or mentions needing specialized automation.
tools: Write, Read, WebFetch, Grep, Glob
model: opus
color: cyan
---

# Purpose

Expert agent architect specializing in designing robust Claude Code sub-agents.
Transform user prompts into complete, production-ready sub-agent configuration files.

## Instructions

1. **Fetch Latest Documentation:** Retrieve current sub-agent docs from official sources
2. **Analyze User Intent:** Deeply examine the user's prompt for purpose and requirements
3. **Generate Agent Name:** Create concise, kebab-case identifier
4. **Select Visual Identity:** Choose appropriate color
5. **Craft Delegation Description:** Write clear, action-oriented description
6. **Determine Required Tools:** Identify minimal tool set needed
7. **Develop System Prompt:** Create comprehensive instructions
8. **Define Workflow:** Establish numbered action sequence
9. **Document Best Practices:** List domain-specific best practices
10. **Write Agent File:** Create file at `.claude/agents/<agent-name>.md`

## Best Practices

- Prioritize clarity in delegation descriptions for accurate routing
- Select only essential tools for focused capabilities
- Include specific, actionable steps rather than vague directives
- Define clear success criteria and output expectations
```

### Read-Only Research Agent

```yaml
---
name: api-researcher
description: Researches API documentation and external services. Use when integrating with new APIs or external services.
tools: Read, WebFetch, WebSearch, Grep, Glob
model: sonnet
color: purple
---

# Purpose

Specialized researcher for API documentation, service integration patterns, and external service capabilities.

## Instructions

1. Understand integration requirements
2. Fetch and analyze API documentation
3. Search for integration examples and best practices
4. Summarize findings with code examples
5. Flag potential issues or limitations
```

### Fast Worker Agent (Haiku)

```yaml
---
name: test-runner
description: Runs tests and analyzes failures. Use when implementing features, fixing bugs, or user requests test execution.
tools: Bash, Read, Grep, Glob, Edit
model: haiku
color: green
---

# Purpose

Fast, efficient test runner focused on executing tests and providing clear failure analysis.

## Instructions

1. Run relevant test suite
2. Parse test output for failures
3. Identify root causes
4. Suggest specific fixes
5. Re-run tests after fixes
```

---

## Frontmatter Validation Checklist

Before deploying an agent, verify:

- [ ] `name` is in kebab-case
- [ ] `name` is unique across all agents
- [ ] `description` is specific and includes trigger keywords
- [ ] `description` mentions when to use the agent
- [ ] `tools` (if specified) includes only necessary tools
- [ ] `model` (if specified) is appropriate for task complexity
- [ ] `color` (if specified) is from valid set
- [ ] YAML syntax is valid (no tabs, proper indentation)
- [ ] Frontmatter closes with `---`

---

## Common Mistakes to Avoid

### Mistake 1: Vague description
```yaml
# BAD
description: Helps with code

# GOOD
description: Reviews Python code for PEP-8 compliance and common bugs. Use when Python files are modified.
```

### Mistake 2: Too many tools
```yaml
# BAD - grants everything explicitly
tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch, WebSearch, Task, Skill, TodoWrite

# GOOD - minimal set
tools: Read, Grep, Glob
```

### Mistake 3: Wrong model for task
```yaml
# BAD - using Opus for simple task (expensive!)
name: code-formatter
model: opus

# GOOD - using Haiku for deterministic task
name: code-formatter
model: haiku
```

### Mistake 4: Inconsistent naming
```yaml
# BAD
name: TestRunner          # Wrong case
name: test_runner         # Wrong separator
name: test-runner-agent   # Redundant suffix

# GOOD
name: test-runner
```

### Mistake 5: Missing trigger words in description
```yaml
# BAD - no clear trigger
description: An agent that reviews code

# GOOD - clear triggers
description: Reviews code for security issues. Use PROACTIVELY when code changes or security review is needed.
```

---

## Reference: Priority Loading Order

When multiple agents have same name, priority order is:

1. Project-level (`.claude/agents/`) - HIGHEST
2. CLI-defined (`--agents` flag)
3. User-level (`~/.claude/agents/`)
4. Plugin agents - LOWEST

Keep this in mind when naming agents to avoid conflicts.
