---
name: wave-orchestrator
description: >-
  Orchestrate parallel implementation of multiple beads across cmux panes in dependency-aware
  waves. Use when implementing a whole feature area, dispatching multiple beads at once, or
  running parallel cld -b sessions. MUST USE when user says "wave", "parallel beads",
  "implement all beads for X", "start the beads", or references implementing more than 2 beads
  at once. Also triggers on "cmux dispatch", "multi-bead", "wave orchestrator".
---

# Wave Orchestrator

Dispatches to the dedicated Sonnet subagent for all wave orchestration work.

## When to Use

- "wave" / "parallel beads" / "implement all beads for X" / "start the beads"
- "cmux dispatch" / "multi-bead" / "wave orchestrator"
- Implementing more than 2 beads at once

## Dispatch

```python
Invoke the configured wave-orchestration worker with the current input arguments.
Pass through the user's topic, bead IDs, and flags unchanged.
```

All wave orchestration logic (discovery, planning, dispatch, monitoring, integration-verification,
and learnings report) lives in the subagent at `beads-workflow/agents/wave-orchestrator.md`.

The subagent runs on Sonnet with an isolated context window and delegates monitoring to the
Haiku wave-monitor agent — parking the orchestrator during long idle periods.
