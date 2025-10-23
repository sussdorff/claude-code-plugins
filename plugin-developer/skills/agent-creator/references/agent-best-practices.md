# Agent Best Practices (2025)

Comprehensive best practices for Claude Code agent engineering based on 2025 patterns and real-world production usage.

## Core Design Principles

### 1. Token Efficiency First

**Principle:** Carefully engineer how many tokens your agent needs to initialize.

**Why it matters:**
- Lightweight agents (<3k tokens) are significantly more composable
- Heavy agents (25k+ tokens) create bottlenecks in multi-agent workflows
- Token count directly impacts speed, cost, and context availability

**How to achieve:**
- Keep system prompts concise and focused
- Move detailed documentation to references (loaded as needed)
- Use numbered steps instead of verbose explanations
- Avoid repetitive examples - one clear example is better than five similar ones

**Measurements:**
```
Lightweight:  <3k tokens  ✅ Ideal for frequent use, composability
Moderate:     3-10k tokens ✅ Most specialized agents
Heavy:        10-25k tokens ⚠️  Use sparingly, only when necessary
Very Heavy:   >25k tokens  ❌ Avoid - creates workflow bottlenecks
```

---

### 2. Single Responsibility Agents

**Principle:** Each agent should have one clear goal, input, output, and handoff rule.

**Benefits:**
- Easier to test and debug
- More predictable behavior
- Better composability
- Clearer delegation decisions

**Examples:**

✅ **GOOD - Focused agents:**
```yaml
name: security-reviewer
description: Reviews code for security vulnerabilities only
```

```yaml
name: performance-analyzer
description: Analyzes code for performance bottlenecks only
```

❌ **BAD - Multi-purpose agent:**
```yaml
name: code-analyzer
description: Reviews code for security, performance, style, tests, and documentation
```

**Fix:** Split into specialized agents that can be composed.

---

### 3. Minimal Tool Access (Permission Hygiene)

**Principle:** Restrict tool access intentionally. Grant only necessary tools.

**Security benefits:**
- Prevents accidental destructive operations
- Reduces attack surface
- Forces focused agent design

**Performance benefits:**
- Clearer agent purpose
- Better decision making
- Reduced cognitive load

**Common patterns by agent role:**

```yaml
# PM/Specification agents - read and research
tools: Read, WebFetch, WebSearch, Grep, Glob

# Architect agents - read and write specs
tools: Read, Write, WebFetch, Grep, Glob

# Implementer agents - full development toolkit
tools: Read, Write, Edit, Bash, Grep, Glob

# Reviewer agents - read and analyze only
tools: Read, Grep, Glob

# Test runner agents - execute and analyze
tools: Bash, Read, Grep, Glob, Edit

# Orchestrator agents - coordinate others
tools: Task, TodoWrite, Read

# Research agents - fetch and summarize
tools: Read, WebFetch, WebSearch, Grep, Glob
```

**Anti-pattern:** Omitting `tools` field unless you explicitly want ALL tools including MCP tools.

---

## Model Selection Strategy

### The 2025 Model Economics

**Claude Haiku 4.5** (released October 2025):
- 90% of Sonnet 4.5's agentic performance
- 2x faster
- 3x cost savings ($1/$5 vs $3/$15)
- Game-changer for agent economics

**Strategy:** Dynamic Model Selection
- Start with Haiku 4.5
- Escalate to Sonnet 4.5 if validation fails
- Reserve Opus 4 for critical reasoning

### Model Selection by Agent Type

```yaml
# Routine, deterministic tasks → Haiku
name: test-runner
model: haiku
# Why: Fast execution, predictable task, cost-effective

name: code-formatter
model: haiku
# Why: Deterministic, style rules, speed matters

name: linter
model: haiku
# Why: Rule-based checking, fast feedback needed

# Moderate complexity, specialized analysis → Sonnet (default)
name: code-reviewer
model: sonnet
# Why: Needs judgment, context understanding, security analysis

name: bug-investigator
model: sonnet
# Why: Root cause analysis, moderate complexity

name: api-designer
model: sonnet
# Why: Design decisions, trade-off analysis

# Complex reasoning, orchestration, critical decisions → Opus
name: meta-agent
model: opus
# Why: Generates other agents, complex reasoning, meta-level design

name: architect-review
model: opus
# Why: System design decisions, architectural trade-offs, long-term implications

name: security-auditor
model: opus
# Why: Critical security analysis, adversarial thinking, high stakes
```

### Multi-Model Orchestration Pattern

**Proven architecture for cost optimization:**

```yaml
# Orchestrator: Sonnet (task decomposition & quality validation)
name: task-orchestrator
model: sonnet
tools: Task, TodoWrite, Read

# Workers: Haiku (execute specialized subtasks in parallel)
name: test-worker
model: haiku
tools: Bash, Read, Grep

name: lint-worker
model: haiku
tools: Bash, Read, Edit

name: format-worker
model: haiku
tools: Bash, Read, Edit

# Reviewer: Sonnet (quality gate)
name: quality-reviewer
model: sonnet
tools: Read, Grep, Glob
```

**Results:** 2-2.5x cost reduction while maintaining 85-95% quality.

---

## Auto-Delegation Optimization ("Tool SEO")

### Principle: Description Quality Determines Auto-Delegation Success

Your agent's `description` field is like SEO for agent routing. Optimize it!

### Best Practices for Auto-Delegation

**1. Use explicit trigger phrases:**
```yaml
# Good - explicit triggers
description: Use PROACTIVELY when code changes are made

description: MUST BE USED at the start of new feature development

description: Delegate when security review is needed
```

**2. Include specific keywords users might say:**
```yaml
# Good - matches user language
description: |
  Runs tests and analyzes failures. Use when:
  - implementing new features
  - fixing bugs
  - user says "run tests" or "test this"
  - preparing for commits
```

**3. Be specific about the domain:**
```yaml
# Bad - too vague
description: Helps with code

# Good - specific domain
description: Reviews Python code for PEP-8 compliance, type hints, and common anti-patterns. Use for Python file changes.
```

**4. Mention handoff conditions:**
```yaml
# Good - clear handoffs
description: Writes specification from requirements. Sets status READY_FOR_ARCH when complete. Use at start of feature development.
```

### Testing Auto-Delegation

After creating an agent, test if it auto-delegates correctly:

```bash
# Test phrases that should trigger your agent
"Review this code for security issues"      → security-reviewer
"Run the tests"                            → test-runner
"Write a spec for this feature"            → pm-spec
"Is this architecture sound?"              → architect-review
```

If auto-delegation fails, revise the description with more specific trigger keywords.

---

## Agent Workflow Design

### 1. Clear Step-by-Step Instructions

**Use numbered steps** for agent instructions:

✅ **GOOD:**
```markdown
## Instructions

1. Read all changed files in the current branch
2. Identify security vulnerabilities using OWASP Top 10 criteria
3. Check for sensitive data exposure (API keys, passwords, tokens)
4. Analyze authentication and authorization logic
5. Generate prioritized list of findings with severity ratings
6. Suggest specific fixes with code examples
```

❌ **BAD:**
```markdown
## Instructions

Review the code and look for security problems. Think about what could go wrong. Check for vulnerabilities and provide feedback.
```

### 2. Define Clear Success Criteria

Include "Definition of Done" in your agent:

```markdown
## Definition of Done

- [ ] All changed files reviewed
- [ ] Security findings documented with severity (Critical/High/Medium/Low)
- [ ] Specific fix suggestions provided for each finding
- [ ] No false positives (validated findings only)
- [ ] Summary report generated
```

### 3. Specify Output Format

Tell agents HOW to structure their response:

```markdown
## Output Format

Provide findings in this structure:

### Critical Issues
1. [Issue description]
   - File: `path/to/file.py:123`
   - Risk: [Specific risk]
   - Fix: ```python
   [Suggested code]
   ```

### High Priority Issues
[...]

### Summary
- Critical: X issues
- High: Y issues
- Overall risk: [assessment]
```

---

## Multi-Agent Patterns

### Pattern 1: Three-Stage Pipeline

**Recommended starting point for development workflows:**

```yaml
# Stage 1: Specification
name: pm-spec
description: Writes specifications and clarifying questions. Sets status READY_FOR_ARCH when complete.
tools: Read, Write, WebFetch
model: sonnet

# Stage 2: Architecture Review
name: architect-review
description: Validates design against platform constraints. Produces ADR. Sets status READY_FOR_BUILD.
tools: Read, Write, Grep, Glob
model: opus

# Stage 3: Implementation
name: implementer-tester
description: Implements code and tests. Updates docs. Sets status DONE.
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
```

**Key elements:**
- Clear handoff points (status transitions)
- Increasing tool permissions (read → write → full)
- Appropriate model selection per stage

### Pattern 2: Parallel Workers with Orchestrator

**For parallelizable tasks:**

```yaml
# Orchestrator
name: parallel-orchestrator
model: sonnet
tools: Task, TodoWrite, Read
# Decomposes work, launches workers, validates results

# Workers (can run simultaneously)
name: unit-test-runner
model: haiku
tools: Bash, Read, Grep

name: integration-test-runner
model: haiku
tools: Bash, Read, Grep

name: lint-checker
model: haiku
tools: Bash, Read, Edit
```

### Pattern 3: Review Loop

**For iterative quality improvement:**

```yaml
# Implementer
name: implementer
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet

# Reviewer (provides feedback)
name: code-reviewer
tools: Read, Grep, Glob
model: sonnet

# Quality Gate (approves or rejects)
name: quality-gate
tools: Read, Grep, Glob, TodoWrite
model: opus
```

**Flow:** Implement → Review → Fix → Review → Quality Gate → Done

### Pattern 4: External Integration

**Integrate external LLMs/tools via MCP:**

```yaml
# Primary agent
name: implementation-agent
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet

# External reviewer via MCP
name: external-reviewer
description: Calls external GPT-5 API for specialized review. Sets status PENDING_REVIEW then conditionally READY_FOR_* based on verdict.
tools: Read, mcp__external-llm__review
model: haiku  # Haiku sufficient for API orchestration
```

---

## Hook-Based Orchestration

### Principle: Chain with Hooks, Not Prompt Glue

**Use lifecycle events** to orchestrate agent handoffs:

✅ **GOOD - Hook-based:**
```json
{
  "hooks": [
    {
      "event": "SubagentStop",
      "agent": "pm-spec",
      "condition": "status == READY_FOR_ARCH",
      "action": "suggest-next",
      "message": "Specification complete. Ready for architect-review agent."
    }
  ]
}
```

❌ **BAD - Prompt-based:**
```markdown
After writing the spec, tell the user to invoke the architect-review agent.
```

**Benefits of hook-based:**
- Automatic handoff suggestions
- Consistent workflow
- Less prompt engineering needed
- Trackable state transitions

---

## Context Management Best Practices

### 1. CLAUDE.md Independence

**Important:** Custom agents don't inherit project CLAUDE.md

**Benefits:**
- Prevents context pollution
- Ensures consistent behavior across projects
- Clearer agent scope

**Implication:** Include all necessary context in agent system prompt

### 2. Slug-Based Tracking

**Use identifiers** to tie artifacts together:

```markdown
## Instructions

1. Generate slug: `FEAT-{timestamp}`
2. Create spec file: `specs/{slug}.md`
3. Create ADR file: `adrs/{slug}.md`
4. Link artifacts via slug in all documents
```

**Benefits:**
- Track related artifacts across agent invocations
- Easy to find specification → architecture → implementation
- Audit trail for decisions

### 3. State Management

**Use explicit state markers:**

```yaml
# Agent sets clear status
Status: READY_FOR_ARCH
Status: READY_FOR_BUILD
Status: PENDING_REVIEW
Status: DONE
```

**Track in files or TodoWrite:**
```markdown
## Status
- Specification: ✅ DONE
- Architecture: 🔄 IN_PROGRESS
- Implementation: ⏳ PENDING
```

---

## Testing & Validation

### 1. Test Auto-Delegation

```bash
# Method 1: Direct request
"Review this code"  # Should trigger code-reviewer

# Method 2: Contextual
[Make code changes]
"What do you think?" # Should proactively suggest code-reviewer

# Method 3: Explicit
"Use the code-reviewer agent to check this"  # Should work
```

### 2. Test Tool Permissions

```bash
# Agent with only Read, Grep, Glob
# Should NOT be able to:
- Write files
- Execute bash commands
- Make changes

# Should error gracefully with clear message
```

### 3. Test Model Appropriateness

```bash
# Haiku agent should complete routine tasks in <10s
# Sonnet agent should handle moderate complexity
# Opus agent should handle complex reasoning

# Monitor: speed, quality, cost
```

### 4. Test Isolated Context

```bash
# Agent should NOT have access to:
- Main conversation history
- Other agents' contexts

# Agent should ONLY have:
- Its own system prompt
- The specific task delegation
- Tool results from its execution
```

---

## Performance Optimization

### 1. Progressive Agent Loading

**Don't load everything upfront:**

```yaml
# Lightweight initial agent
name: entry-point
model: haiku
tools: Read, Task
# Delegates to specialized agents as needed
```

### 2. Agent Composition Over Complexity

**Instead of one complex agent:**
```yaml
name: super-agent
model: opus
tools: [everything]
# 30k token system prompt
```

**Use composed specialists:**
```yaml
name: orchestrator + worker-1 + worker-2 + worker-3
# Each <5k tokens
# Haiku workers, Sonnet orchestrator
# 50-70% cost reduction
```

### 3. Result Caching

**For repeated operations:**

```markdown
## Instructions

1. Check if analysis exists in `.claude/cache/{file-hash}.json`
2. If cache valid (file unchanged), return cached results
3. Otherwise, perform analysis and update cache
```

**Benefits:**
- Faster iteration
- Consistent results
- Cost savings

---

## Security Patterns

### 1. Principle of Least Privilege

```yaml
# Start with minimal tools
tools: Read, Grep, Glob

# Add incrementally as needed
# Document why each tool is necessary
```

### 2. Safe Bash Patterns

```yaml
# For agents that need Bash, add safeguards:
tools: Bash, Read, Grep, Glob

# In system prompt:
```markdown
When using Bash:
- NEVER use destructive commands (rm -rf, dd, mkfs)
- ALWAYS use --dry-run for testing
- NEVER modify system files
- ALWAYS validate user intent before destructive operations
```

### 3. Secrets Management

```markdown
## Security Rules

- NEVER log API keys, passwords, or tokens
- Check for secrets before committing files
- Validate that sensitive data is properly masked
- Use environment variables for credentials
```

### 4. User Confirmation for Critical Operations

```yaml
tools: AskUserQuestion, Bash, Write

# In system prompt:
```markdown
Before executing destructive operations:
1. Summarize what will happen
2. Use AskUserQuestion to get explicit confirmation
3. Proceed only with clear approval
```

---

## Common Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: The Swiss Army Knife Agent

```yaml
name: do-everything-agent
description: Does code review, testing, deployment, documentation, and makes coffee
tools: [every tool]
model: opus
```

**Problem:** Too broad, expensive, slow, unpredictable
**Solution:** Split into focused agents

### ❌ Anti-Pattern 2: The Novel-Length System Prompt

```markdown
# 50k token system prompt with:
- Entire coding standards doc
- All company policies
- Complete API reference
- 100 examples
```

**Problem:** Token waste, slow loading, context pollution
**Solution:** Use references/, load as needed

### ❌ Anti-Pattern 3: The Permission Maximalist

```yaml
tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch, WebSearch, Task, Skill, TodoWrite, AskUserQuestion, NotebookEdit
# Plus all MCP tools
```

**Problem:** Security risk, unclear purpose, decision paralysis
**Solution:** Minimal tool set for focused purpose

### ❌ Anti-Pattern 4: The Vague Delegator

```yaml
description: Helps with stuff
```

**Problem:** Never auto-delegates, unclear purpose
**Solution:** Specific, keyword-rich description

### ❌ Anti-Pattern 5: The Wrong Model

```yaml
name: code-formatter  # Deterministic task
model: opus           # Most expensive model
```

**Problem:** 10x more expensive than needed
**Solution:** Haiku for routine tasks

### ❌ Anti-Pattern 6: The Context Polluter

Agents that output verbose logs, status updates, and internal reasoning to main conversation.

**Problem:** Clutters main conversation, wastes context
**Solution:** Isolated context, concise final output only

---

## Maintenance & Iteration

### 1. Version Your Agents

```yaml
# In agent file or git commit
# v1.0.0 - Initial release
# v1.1.0 - Added performance analysis
# v2.0.0 - Changed tool permissions (breaking change)
```

### 2. Measure Agent Performance

**Track metrics:**
- Invocation frequency (is it being used?)
- Success rate (does it complete tasks?)
- Cost per invocation (is it cost-effective?)
- Speed (is it fast enough?)
- User satisfaction (manual feedback)

### 3. Iterate Based on Usage

```markdown
## Iteration Checklist

- [ ] Review auto-delegation accuracy (being invoked correctly?)
- [ ] Check tool usage (using all granted tools? Need more?)
- [ ] Validate model choice (is complexity appropriate?)
- [ ] Review output quality (meeting expectations?)
- [ ] Optimize token count (can system prompt be leaner?)
```

---

## Summary: The Five Pillars of Agent Design

1. **Token Efficiency** - Keep system prompts lean (<3k tokens ideal)
2. **Single Responsibility** - One clear purpose per agent
3. **Minimal Tools** - Grant only necessary permissions
4. **Right Model** - Haiku for routine, Sonnet for specialized, Opus for complex
5. **Clear Description** - Specific, keyword-rich for auto-delegation

Follow these principles and you'll create fast, cost-effective, reliable agents that compose beautifully into powerful multi-agent workflows.
