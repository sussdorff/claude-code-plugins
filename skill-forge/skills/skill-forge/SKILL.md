---
name: skill-forge
description: >
  Create, review, refactor, audit, and optimize Claude Code skills against quality standards.
  Use when creating new skills, reviewing quality, auditing fleet consistency, or optimizing
  triggers. Triggers on "create skill", "new skill", "review skill", "audit skills",
  "skill quality", "refactor skill", "check skill". Do NOT use for agents (use agent-creator).
---

# Skill Forge

Create, evaluate, improve, and maintain Claude Code skill quality. Applies the quality standard (`references/quality-standard.md`) to produce scored reports, concrete refactoring suggestions, fleet-wide audits, and new skills from scratch.

## When to Use

- "I need a new skill for X" / "create a skill" / "build a skill for Y"
- "Review this skill" / "check skill quality" / "how good is skill X?"
- "Refactor skill X" / "improve skill X" / "optimize triggers for X"
- "Audit all skills" / "skill health check" / "fleet quality report"

## Modes

Route based on user intent:

| Mode | Trigger Examples | Action |
|------|-----------------|--------|
| **Create** | "create skill X", "new skill for Y", "build a skill" | Scaffold and build a new skill from requirements |
| **Review** | "review skill X", "check skill quality" | Score skill against quality standard, produce report |
| **Refactor** | "refactor skill X", "improve skill X" | Review + generate before/after rewrite suggestions |
| **Audit** | "audit all skills", "skill health check" | Scan ALL skills, produce scored overview table |
| **Optimize** | "fix triggers for X", "improve description" | Focused on description and trigger quality only |

## Create Mode Workflow

Follow these steps when building a new skill. Reference files provide the detail:
- `references/skill-specification.md` -- format, frontmatter fields, token budgets
- `references/skill-creation-guide.md` -- workflow, best practices, pitfalls
- `references/claude-code-features.md` -- context:fork, agents, $ARGUMENTS, dynamic injection

### 1. Gather Requirements

Ask about purpose, trigger scenarios, scope boundaries, output format, and content type (reference knowledge vs task instructions). Do NOT start writing without understanding intent.

### 2. Scaffold

Run `scripts/init-skill.sh <skill-name>` to create the directory skeleton with template SKILL.md.

- **Default (global):** Creates in `~/.claude/skills/` — shared across all projects
- **`--local` flag:** Creates in `.claude/skills/` — project-specific, not shared

Override the global path with env var `SKILL_FORGE_GLOBAL_DIR` if your skills live elsewhere.

```bash
scripts/init-skill.sh my-tool          # global (default)
scripts/init-skill.sh --local my-tool   # project-specific
```

### 3. Write Frontmatter

Apply the description format from `references/skill-specification.md`:
- Verb phrase + trigger phrases + negative triggers
- Set invocation control based on content type
- Add `context: fork` if skill runs standalone tasks

### 4. Write Body

Follow section order: Title -> Overview -> When to Use -> Core workflow -> Do NOT -> Resources.

### 5. Extract to References

If SKILL.md exceeds 500 lines, extract detail into `references/` files. Keep SKILL.md as the routing layer.

### 6. Validate

Run skill-forge **Review** mode on the new skill. Target grade B+ or better. Check auto-invocation triggers and token budget.

### 7. Test Invocation

- Auto-invocation: ask Claude something matching the description
- Manual: run `/skill-name` with arguments
- Negative: ask something the skill should NOT match

## Review/Refactor/Audit Workflow

### 1. Load Context

```
required_standard="references/quality-standard.md"
```

Read the quality standard first. If unavailable, use the embedded review dimensions below as fallback.

For **Audit** mode, run `scripts/scan-skills.sh` to discover all skills before evaluating.

### 2. Evaluate

Apply the five review dimensions to the target skill(s). For each dimension, assign a score.

**Review Dimensions** (details in `references/review-checklist.md`):

| Dimension | Weight | Key Criteria |
|-----------|--------|-------------|
| Description Quality | 25 pts | Trigger phrases, format, length 150-300 chars |
| Content Structure | 25 pts | Section order, word count, "When to Use" section |
| Progressive Disclosure | 20 pts | SKILL.md < 500 lines, references/ split, clear pointers |
| Writing Style | 15 pts | Imperative form, concrete language, no filler |
| Token Efficiency | 15 pts | SKILL.md < 3000 tokens, total < 10000 tokens |

### 3. Score

Compute total and assign grade:

| Grade | Score | Meaning |
|-------|-------|---------|
| **A** | 90-100 | Production-ready, exemplary |
| **B** | 75-89 | Good, minor improvements possible |
| **C** | 60-74 | Functional, notable issues |
| **D** | 40-59 | Needs significant rework |
| **F** | 0-39 | Fundamentally broken |

### 4. Output

Use the output template matching the active mode from `references/review-checklist.md`. Each mode has a distinct format (scored table for Review, before/after for Refactor, fleet table for Audit, trigger test for Optimize).

## Prompt Techniques

Apply these when suggesting refactoring improvements. See `references/prompt-techniques.md` for details.

- **Goldilocks Principle**: ~500 token sweet spot, 7 core principles
- **Six-Layer Specification**: FORMAT, TONE, CONSTRAINTS, SUCCESS, EDGE CASES, REFERENCE
- **WHY Statements**: Narrow solution space by stating intent
- **Hierarchical Context**: REQUIRED vs OPTIONAL separation

## Do NOT

- Create skills without asking about purpose and trigger scenarios first
- Rewrite entire skills without user approval -- suggest changes, let user decide
- Score skills without reading them fully first
- Assume quality standard content -- always load from file. WHY: standard is maintained separately and may have been updated since last read
- Skip dimensions in review -- score all five even if some are perfect. WHY: partial reviews miss systemic issues like token budget violations hiding behind good descriptions
- Apply review criteria to non-skill files (commands, agents have different standards)

## Resources

- `references/review-checklist.md` -- Scoring criteria per dimension + output templates
- `references/refactoring-patterns.md` -- Common improvement patterns with before/after
- `references/prompt-techniques.md` -- Goldilocks, Six-Layer Stack, prompt craft techniques
- `references/skill-specification.md` -- Complete SKILL.md format and frontmatter reference
- `references/skill-creation-guide.md` -- Creation workflow, best practices, pitfalls
- `references/claude-code-features.md` -- Claude Code-specific features (context:fork, $ARGUMENTS, etc.)
- `references/quality-standard.md` -- Authoritative quality standard
- `scripts/scan-skills.sh` -- Discover all skills, measure tokens/lines
- `scripts/init-skill.sh` -- Scaffold a new skill directory with template
