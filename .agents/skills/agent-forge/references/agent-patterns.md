# Agent Patterns & Examples

Real-world patterns for Claude Code agents. Choose the pattern that fits your use case, then compose into pipelines.

## Pattern Summary

| Pattern | Model | Tools | Use case |
|---------|-------|-------|----------|
| Code Reviewer | sonnet | Read, Grep, Glob | Isolated analysis, read-only |
| Test Runner | haiku | Bash, Read, Grep, Edit | Fast execution, fix feedback |
| Security Auditor | opus | Read, Grep, Glob, WebFetch | Critical security, CVSS scoring |
| Feature Implementer | sonnet | Read, Write, Edit, Bash, Grep, Glob | Full dev toolkit |
| Task Orchestrator | sonnet | Agent, Read | Decomposes work, coordinates specialists |
| Meta-Agent | opus | Write, Read, WebFetch, Grep | Creates other agents |
| API Researcher | sonnet | Read, WebFetch, WebSearch, Grep | External integrations |

## Single-Purpose Agent (Complete Example)

```markdown
---
name: code-reviewer
description: Reviews code for security vulnerabilities, performance issues, and best practices. Use proactively when code changes are made or user requests code review.
tools: Read, Grep, Glob
model: sonnet
color: blue
---

# Purpose

Expert code reviewer for security, performance, and best practices.

## Instructions

1. Identify changed files via git diff or user specification
2. Read all relevant files for context
3. Analyze for: security (OWASP Top 10), performance anti-patterns, best practices
4. Generate prioritized findings with severity ratings

## Output Format

### Critical Issues
[file:line, description, fix]

### High Priority
[file:line, description, fix]

### Summary
- Total: X issues (Critical: Y, High: Z)
- Risk: [Low/Medium/High]
- Recommendation: [Approve/Request Changes/Reject]
```

Key characteristics: read-only tools (safe), sonnet (needs judgment), structured output.

## Multi-Agent Pipeline Pattern

Three stages with clear handoffs and status transitions:

```yaml
# Stage 1: PM Specification → sets status READY_FOR_ARCH
name: pm-spec
tools: Read, Write, WebFetch
model: sonnet

# Stage 2: Architect Review → sets status READY_FOR_BUILD
name: architect-review
tools: Read, Write, Grep, Glob
model: opus

# Stage 3: Implementation → sets status DONE
name: implementer-tester
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
```

Key principles:
- Clear handoff points (status field in spec file)
- Increasing tool permissions (read → write → full)
- Model matches complexity (Sonnet → Opus → Sonnet)
- Slug-based artifact linking: `FEAT-{timestamp}`

## Orchestrator Pattern

```markdown
---
name: task-orchestrator
description: Decomposes complex tasks and coordinates specialized agents. Use PROACTIVELY for multi-step workflows requiring coordination.
tools: Agent, Read
model: sonnet
color: purple
---

## Instructions

1. Analyze task and identify independent vs sequential subtasks
2. For independent tasks: spawn parallel agents via Agent tool
3. For dependent tasks: run sequentially, pass results forward
4. Collect and integrate results
5. Quality-gate before reporting completion

## Execution Patterns

Parallel (independent): unit-test + integration-test + lint → collect → report
Sequential: pm-spec → architect-review → implementer-tester
Hybrid: spec → parallel(backend, frontend) → integration-test
```

## Meta-Agent (Self-Generating) Pattern

```yaml
name: meta-agent
description: Generates complete Claude Code agent configurations from user descriptions. Use when creating new agents.
tools: Write, Read, WebFetch, Grep
model: opus
color: cyan
```

Meta-agents need opus (complex meta-reasoning) and Write access to create agent files.

## Model Selection Summary

| Task Type | Model | Reason |
|-----------|-------|--------|
| Routine/deterministic | haiku | Fast, cost-effective |
| Moderate complexity | sonnet | Balanced judgment |
| Complex reasoning / critical | opus | Full reasoning, high stakes |

Multi-model cost optimization: haiku workers + sonnet orchestrator = 50-70% cost reduction vs all-sonnet.

## Tool Access Patterns

```yaml
# Read-only analysis
tools: Read, Grep, Glob

# Research
tools: Read, WebFetch, WebSearch, Grep, Glob

# Implementation
tools: Read, Write, Edit, Bash, Grep, Glob

# Orchestration
tools: Agent, Read
```

Always use minimal tools for the agent's purpose — reduces attack surface and keeps agents focused.
