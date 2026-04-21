# NBJ 12 Primitives — Evaluation Framework

From Nate's "Building Agents Is 80% Plumbing" framework.

## Scoring

| Status | Meaning | Risk |
|--------|---------|------|
| present | Clearly implemented — file/dir exists with substantial content | low |
| partial | Mentioned or started but incomplete | medium |
| missing | No evidence found | high |

## Tier Assessment

Count primitives with `present` status:

| Count | Tier |
|-------|------|
| 0–4   | Tier 1: Foundational |
| 5–8   | Tier 2: Operational |
| 9–12  | Tier 3: Advanced |

## The 12 Primitives

| # | Primitive | What it covers |
|---|-----------|----------------|
| 1 | **Tool Registry** | Structured registry of available tools/skills |
| 2 | **Permission System** | Access control, safety checks, guardrails |
| 3 | **Session Persistence** | State survives restarts/crashes |
| 4 | **Workflow State** | Task state machines, status tracking |
| 5 | **Token Budget** | Cost awareness, budget enforcement |
| 6 | **Streaming Events** | Real-time output, progress updates |
| 7 | **Event Logging** | Structured audit trail, event capture |
| 8 | **Verification Harness** | Test gates, review loops, CI checks |
| 9 | **Tool Pool Assembly** | Dynamic context loading, on-demand skills |
| 10 | **Transcript Compaction** | Context window management, summarization |
| 11 | **Permission Audit Trail** | Access logs, decision history |
| 12 | **Doctor + Provenance** | Health checks, origin tracking |

## Scoring Criteria

**present** requires all of:
- Dedicated file/directory with substantive content (not empty)
- Evidence of actual use (not just mentioned)
- Clearly operational (not "todo" or "planned")

**partial** applies when:
- File exists but content is thin or incomplete
- Mentioned in docs but no implementation
- One component present, peer component missing

**missing** applies when:
- No file, no reference, no evidence
