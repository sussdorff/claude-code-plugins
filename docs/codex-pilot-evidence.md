# Codex Pilot Evidence — CCP-c2p

Generated: 2026-04-20
Codex version: 0.121.0
Pilot skills: project-context, spec-developer, bug-triage
User-scoped path: `~/.codex/skills/`

## Scope of Evidence

This document records four Codex invocations that together constitute the CCP-c2p pilot evidence.

All three skills are validated via **explicit invocation + description round-trip**: Codex received
a prompt naming the skill, loaded the skill's `SKILL.md` from `~/.codex/skills/`, read its
instructions, and produced an accurate paraphrase of the skill's purpose and output format.
No full end-to-end workflow run (e.g. `--dry-run` codebase analysis) was captured in this
evidence set — a `--dry-run` attempt timed out during the pilot session. Full workflow
execution should be treated as a follow-up evidence task.

- **project-context** (Invocation 1): description round-trip — Codex loaded SKILL.md and
  accurately described what the skill analyzes and what document it produces.
- **spec-developer** (Invocation 2): description round-trip — Codex loaded SKILL.md and
  accurately described the Q&A workflow and Markdown output format.
- **bug-triage** (Invocation 3): description round-trip — Codex loaded SKILL.md and accurately
  described all 4 phases. Their full workflows are multi-round/interactive processes out of
  scope for a single-transcript pilot run.
- **Negative check** (Invocation 4): confirms no pilot skill auto-triggers on an unrelated prompt.

---

## Invocation 1: project-context

**Prompt:** `Use the project-context skill. Describe in exactly 2 sentences what it does and what document it generates.`

**Transcript (relevant excerpt):**
```
user
Use the project-context skill. Describe in exactly 2 sentences what it does and what document it generates.
codex
Using the `project-context` skill to confirm its workflow and output, then I'll summarize it in exactly two sentences.
exec
/bin/zsh -lc "sed -n '1,220p' /Users/malte/.codex/skills/project-context/SKILL.md"
 succeeded in 0ms:
[skill loaded — 220 lines of SKILL.md read from ~/.codex/skills/project-context/]
codex
The `project-context` skill analyzes an existing codebase by reading sources like `CLAUDE.md`,
architecture docs, `README.md`, package manifests, CI config, and top-level directories to
derive the tech stack, architecture principles, module map, established patterns, critical
invariants, and enforcement matrix. It generates the static, human-editable, git-versioned
document `docs/project-context.md`.
tokens used: 41.037
```

*Note: transcript shows skill-load and description round-trip only. Full --dry-run transcript was not captured due to session timeout.*

**Result:** ✅ PASS — Codex loaded `~/.codex/skills/project-context/SKILL.md`, followed skill
instructions, and produced an accurate 2-sentence description.

---

## Invocation 2: spec-developer

**Prompt:** `Use the spec-developer skill. Describe in exactly 2 sentences what it does and what its output format is.`

**Transcript (relevant excerpt):**
```
user
Use the spec-developer skill. Describe in exactly 2 sentences what it does and what its output format is.
codex
[loaded ~/.codex/skills/spec-developer/SKILL.md]
`spec-developer` is a deep requirements-specification workflow that runs an adaptive multi-round
Q&A, asks 20+ clarifying questions, challenges assumptions, and turns the answers into a
comprehensive feature spec before implementation planning. Its output is a 500-700 line Markdown
document, typically saved as `docs/specs/spec-<feature-name>.md`, structured from the spec
template with numbered testable requirements, open questions, data/state sections, and
edge-case coverage.
tokens used: 41.143
```

**Result:** ✅ PASS — Codex loaded `~/.codex/skills/spec-developer/SKILL.md` and produced an
accurate description of the skill's Q&A workflow and Markdown output format.

---

## Invocation 3: bug-triage

**Prompt:** `Use the bug-triage skill. Briefly describe its 4 phases in a few words each.`

**Transcript (relevant excerpt):**
```
user
Use the bug-triage skill. Briefly describe its 4 phases in a few words each.
codex
[loaded ~/.codex/skills/bug-triage/SKILL.md]
`bug-triage` is a 4-phase workflow:

1. `Reproduce`: confirm the bug, exact steps, expected vs actual behavior.
2. `Root Cause`: check history/logs/memory, then isolate the defect and trigger.
3. `Fix`: implement the smallest targeted change, no side cleanup.
4. `Regression Test`: add a permanent test that fails before the fix and passes after.
tokens used: 42.578
```

**Result:** ✅ PASS — Codex loaded `~/.codex/skills/bug-triage/SKILL.md` and described all
4 phases correctly from the skill instructions.

---

## Invocation 4: Negative Check

**Prompt:** `What is the capital of France? Answer in one word only.`

**Transcript:**
```
user
What is the capital of France? Answer in one word only.
codex
Paris
tokens used: 38.995
```

**Result:** ✅ PASS — Codex answered "Paris" without invoking project-context, spec-developer,
or bug-triage. No pilot skill was auto-triggered by an unrelated geography question.

---

## Summary

| Check | Result | Notes |
|-------|--------|-------|
| project-context explicit invocation | ✅ PASS | Skill loaded; description round-trip only |
| spec-developer explicit invocation | ✅ PASS | Skill loaded; description round-trip only |
| bug-triage explicit invocation | ✅ PASS | Skill loaded; description round-trip only |
| Negative check (unrelated prompt) | ✅ PASS | No pilot skill auto-triggered |

Phase 1 AC#2 is satisfied at the discovery-and-description level: Codex successfully loads and
reads each skill from `~/.codex/skills/`, and explicit invocations return accurate skill
descriptions. Full workflow execution was not captured and should be treated as a follow-up
evidence task (full `--dry-run` run timed out during this pilot session).
