---
name: skill-auditor
model: sonnet
description: Audit and score Claude Code skills fleet-wide; improve weak skills surgically. Triggers on audit skills, skill health check, fleet quality, improve skill, fix skill, rewrite skill.
---

# Skill Auditor

Scan and score all Claude Code skills against the quality standard. Produces fleet-wide quality reports with grades, token costs, and actionable findings.

## When to Use

- "Audit all skills" / "skill health check" / "fleet quality report"
- "How good are my skills?" / "score all skills"
- "Which skills need work?" / "find low-quality skills"
- "What's my total system prompt cost?"
- "improve skill X" / "fix weak skill" / "rewrite {skill-name}"

## Workflow

### 1. Discover Skills

Run `scripts/scan-skills.sh` to find all skills and measure their size.

### 2. Load Quality Standards

```
quality_standard="~/.claude/standards/skills/quality.md"
tier_standard="~/.claude/standards/skills/token-budget-tiers.md"
```

Read both standards first. If unavailable, use the embedded dimensions below as fallback.

### 2a. Determine Skill Tier

Before scoring, assign a tier based on the skill's **intended complexity** (not just current size):

| Tier | SKILL.md budget | Total budget (incl. refs) | Characteristics |
|------|-----------------|---------------------------|-----------------|
| **Light** | < 1,000 tokens | = SKILL.md | Single-purpose, one action, fixed output |
| **Medium** | < 3,000 tokens | < 5,000 tokens | Multi-step workflow, some branching |
| **Heavy** | < 2,000 tokens | < 8,000 tokens | Multi-phase, large reference library |

Measure tokens: `wc -w SKILL.md | awk '{print int($1*1.33)}'`

> If the skill's intended tier is ambiguous, default to Medium and flag for human review.

### 3. Evaluate Each Skill

Score against five dimensions:

| Dimension | Weight | Key Criteria |
|-----------|--------|-------------|
| Description Quality | 28 pts | Trigger phrases, format, efficiency (150-250 chars optimal) |
| Content Structure | 25 pts | Section order, word count, "When to Use" section |
| Progressive Disclosure | 20 pts | SKILL.md < 500 lines, references/ split, clear pointers |
| Writing Style | 15 pts | Imperative form, concrete language, no filler |
| Token Efficiency | 12 pts | Within tier budget (light < 1000, medium SKILL.md < 3000 / total < 5000, heavy SKILL.md < 2000 / total < 8000) |

**Token Efficiency scoring:**
- Full 12 pts: within tier budget
- Partial 6 pts: exceeds tier budget by up to 50%
- Zero 0 pts: exceeds tier budget by more than 50%

**Tier violations** are reported as blocking findings (separate from score):
```
TIER VIOLATION: {skill-name} is {tier}-tier but uses {N} tokens (budget: {limit})
```

### 4. Assign Grades

| Grade | Score | Meaning |
|-------|-------|---------|
| **A** | 90-100 | Production-ready, exemplary |
| **B** | 75-89 | Good, minor improvements possible |
| **C** | 60-74 | Functional, notable issues |
| **D** | 40-59 | Needs significant rework |
| **F** | 0-39 | Fundamentally broken |

### 5. Output Fleet Report

```
## Skill Fleet Audit

| Skill | Grade | Tier | Lines | Tokens | Refs | Issues |
|-------|-------|------|-------|--------|------|--------|
| {name} | {grade} | {light/medium/heavy} | {n} | {n} | {y/n} | {top issue} |

### Tier Violations
- {skill-name}: TIER VIOLATION — {tier}-tier but uses {N} tokens (budget: {limit})

### Fleet Summary
- Total skills: {n}
- Average grade: {X}
- Critical issues: {list}

### Fleet System Prompt Cost
- Total description chars: {n}
- Estimated description tokens: {n} (~chars/4)
- Average description length: {n} chars
- Top bloated descriptions (>300 chars): {list with char counts}
```

After outputting the fleet report, if any skill scored C, D, or F, append:

```
Skills with grade C/D/F: {comma-separated list of skill names with their grade}

Which skill(s) would you like to improve? Reply with a skill name (or multiple, comma-separated), or 'none' to skip.
```

## Improve Mode

Use when the user explicitly requests improvement of a specific skill (Grade C/D/F), **or proactively after an audit reveals C/D/F grades**. Audit remains the default; improve is on-demand.

**Trigger phrases:** "improve skill X", "fix skill X", "rewrite {skill-name}", "it scored C/D/F — fix it"

**Proactive trigger:** After any audit (fleet or single-skill) where grade is C, D, or F — append the improve prompt (see Step 5 / Improve Step 1 below) and wait for user response. If the user names a skill, enter Improve Mode for that skill. If the user replies 'none', stop.

**Guard for A/B skills:** If the target skill scores A or B, report "No improvement needed — skill is already high-quality." If the user insists, identify the single weakest dimension and make the minimal change only.

### Step 1 — Audit the target skill

Run the full audit workflow (steps 1–4 above) on the single target skill. Record per-dimension scores.

If the grade is C, D, or F and the user has not already requested improvement, append:

```
{skill-name} scored {grade} ({score}/100).

Would you like to improve it? Reply 'yes' to proceed with surgical rewrite, or 'no' to stop.
```

If the user replies 'yes', continue to Step 2. If 'no', stop.

### Step 2 — Identify weak dimensions

Select the 1–2 lowest-scoring dimensions. These are the only sections to rewrite.

### Step 3 — Load standards

Read `~/.claude/standards/skills/quality.md` and `~/.claude/standards/skills/token-budget-tiers.md` before writing any changes.

### Step 4 — Surgical rewrite

Rewrite ONLY the sections that correspond to the weak dimensions:

| Weak dimension | Action |
|----------------|--------|
| Description Quality | Rewrite frontmatter description: add concrete trigger phrases, hit 150–250 chars |
| Content Structure | Reorder sections to match quality.md order; add missing "When to Use" or "Do NOT" |
| Writing Style | Convert passive/tutorial phrasing to imperative; remove filler ("you might want to") |
| Token Efficiency | Move infrequently-needed content to `references/`; trim redundant prose |
| Progressive Disclosure | Add `references/` file(s) for deep context; update SKILL.md with pointers |

Do not rewrite sections that scored well.

### Step 5 — Before/After Benchmark

1. Save original: `cp SKILL.md workspace/{skill-name}/{skill-name}-before.md`
2. Run 2–3 representative test scenarios using the skill (subagent runs) with the original SKILL.md; store outputs in `workspace/{skill-name}/before/run-N/outputs/`

   Example subagent prompt for each scenario:
   ```
   Load skill: ~/.claude/skills/{skill-name}/SKILL.md
   Task: {concrete task that exercises the skill's main function}
   Expected output: {what a good response looks like}
   ```
3. Apply the rewrite
4. Run the same scenarios with the improved SKILL.md; store outputs in `workspace/{skill-name}/after/run-N/outputs/`
5. Generate the HTML comparison report using the eval-viewer (see Resources):
   ```
   python <eval-viewer> workspace/{skill-name} --skill-name {skill-name}
   ```
6. Open the generated HTML report and review the side-by-side output diff

### Step 6 — Improvement summary

Report:
```
## Improve Report: {skill-name}

Before: Grade {X} ({score}/100) — weak: {dim1}, {dim2}
After:  Grade {X} ({score}/100) — {delta} point improvement
Token delta: {before} → {after} tokens ({+/- n})

Changes made:
- {dimension}: {what changed}
```

## Do NOT

- Review non-skill files (agents, commands have different standards)
- Skip dimensions — score all five even if some are perfect
- Assume quality standard content — always load from file
- Rewrite sections that scored well — improve only weak dimensions

## Resources

- `scripts/scan-skills.sh` — Discover all skills, measure tokens/lines
- `~/.claude/standards/skills/quality.md` — Authoritative quality standard
- `~/.claude/standards/skills/token-budget-tiers.md` — Token budget tier definitions and overage remediation
- `malte/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/eval-viewer/generate_review.py` — Before/after benchmark viewer: reads workspace dir with run subdirs, generates self-contained HTML comparison report
