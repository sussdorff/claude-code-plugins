# Agent Best Practices

## Core Design Principles

### 1. Token Efficiency First

Keep system prompts lean. Token bloat dilutes attention.

```
<3k tokens   ✅ Ideal for composability
3-10k tokens ✅ Most specialized agents
>10k tokens  ⚠️  Use sparingly
```

- Use numbered steps instead of verbose explanations
- One clear example beats five similar ones
- Move reference material to `references/` (loaded as needed)

### 2. Single Responsibility

Each agent: one goal, one input type, one output format, one handoff rule.

❌ `name: code-analyzer` — reviews security, performance, style, tests, docs  
✅ Separate `security-reviewer`, `performance-analyzer`, etc., composed via orchestrator

### 3. Minimal Tool Access

Restrict tools intentionally. Grant only what's necessary.

```yaml
PM/Spec agents:       Read, WebFetch, WebSearch, Grep, Glob
Architect agents:     Read, Write, WebFetch, Grep, Glob
Implementer agents:   Read, Write, Edit, Bash, Grep, Glob
Reviewer agents:      Read, Grep, Glob
Orchestrator agents:  Agent, Read
```

Omitting `tools` grants ALL tools including MCP — always specify explicitly.

## Model Selection

**Haiku** — routine, fast, deterministic tasks (90% of Sonnet performance, 3x cheaper)  
**Sonnet** — moderate complexity, balanced judgment (default)  
**Opus** — complex reasoning, critical decisions, orchestration

Multi-model pattern: haiku workers + sonnet orchestrator = 50-70% cost reduction.

## Description Quality ("Tool SEO")

The `description` field drives auto-delegation. Make it specific:

```yaml
# Bad: too vague
description: Helps with code

# Good: explicit triggers, specific domain
description: |
  Reviews Python code for PEP-8, type hints, and anti-patterns.
  Use PROACTIVELY when: code changes made, user says "review" or "check code"
```

Test after creating: try user phrases that should trigger the agent. If it fails, add more trigger keywords.

## Workflow Design

**Numbered steps** for instructions — specific and concrete, not vague directives.

**Define output format explicitly** — tell agents HOW to structure responses.

**Include a `## Tool Usage` section** — specify WHEN/HOW to use each tool to reduce hallucinated tool choice.

## Deterministic Work Belongs in Scripts

Do not embed executable workflows in agent prompts when a bundled helper can do the work predictably.

- Prompts decide; scripts execute deterministic collection, parsing, polling, and transformation.
- Prefer Python helpers over inline shell glue when the logic spans multiple steps.
- If a helper returns more than one field or has meaningful failure modes, emit the canonical execution-result envelope.
- Use bare stdout only for a single atomic value with no branching semantics.

Reference:
- `meta/skills/agent-forge/references/execution-result-contract.md`
- `core/contracts/execution-result.schema.json`

## Context Management

- Custom agents don't inherit project CLAUDE.md — include all needed context in the system prompt
- Use slug-based artifact tracking (`FEAT-{timestamp}`) to link spec → ADR → implementation
- Use explicit status markers (`READY_FOR_ARCH`, `READY_FOR_BUILD`, `DONE`) for pipeline handoffs

## Hook-Based Orchestration

Use lifecycle hooks for agent handoffs — more reliable than prompt-based instructions:

```json
{
  "hooks": [{
    "event": "SubagentStop",
    "agent": "pm-spec",
    "condition": "status == READY_FOR_ARCH",
    "action": "suggest-next",
    "message": "Specification complete. Ready for architect-review."
  }]
}
```

## Filesystem & Paths

Subagents navigate harness symlinks by reading the filesystem (`ls -la`) — don't hard-code resolved paths in orchestrator prompts. See your harness adapter for the exact home directory and symlink conventions.

## The Five Pillars

1. **Token Efficiency** — lean system prompts (<3k ideal)
2. **Single Responsibility** — one clear purpose per agent
3. **Minimal Tools** — only necessary permissions
4. **Right Model** — haiku/sonnet/opus by complexity
5. **Clear Description** — specific, keyword-rich for auto-delegation
