# Review Checklist

Detailed scoring criteria for each review dimension. Use during Review and Refactor modes.

## Description Quality (25 points)

| Criterion | Points | Pass Condition |
|-----------|--------|---------------|
| Specific trigger phrases | 5 | Description contains 3+ phrases users would say |
| Standard format | 5 | Matches: `[Function]. Use when [triggers]. [Details].` |
| Length 150-300 chars | 3 | Character count within range |
| Third person voice | 3 | No "you should", uses "Use when" / imperative |
| Negative triggers | 3 | Includes "Do NOT use for..." or equivalent |
| Action-oriented verbs | 3 | Starts with verb or uses active constructs |
| Named after job | 3 | Name reflects function, not team or org |

**Common failures:**
- Description too vague ("helps with tasks")
- Missing trigger phrases (auto-delegation fails)
- No negative triggers (gets invoked incorrectly)

## Content Structure (25 points)

| Criterion | Points | Pass Condition |
|-----------|--------|---------------|
| Section order | 5 | Title -> Overview -> When to Use -> Main -> Resources -> Limitations |
| Word count 1000-3000 | 5 | SKILL.md body within range |
| "When to Use" section | 5 | Explicit section with trigger scenarios |
| Logical flow | 5 | No redundancy, clear progression |
| Output format defined | 5 | Templates or examples for expected output |

**Common failures:**
- Missing "When to Use" section
- Resources buried mid-document instead of at end
- No output format specification

## Progressive Disclosure (20 points)

| Criterion | Points | Pass Condition |
|-----------|--------|---------------|
| SKILL.md under 500 lines | 5 | Line count check |
| Heavy content in references/ | 5 | Detailed examples, checklists moved out |
| Clear pointers to references | 5 | SKILL.md links to reference files explicitly |
| Scripts for automation | 5 | Repetitive tasks automated in scripts/ |

**Common failures:**
- Monolithic SKILL.md with 800+ lines
- References exist but SKILL.md doesn't point to them
- Manual steps that could be scripted

## Writing Style (15 points)

| Criterion | Points | Pass Condition |
|-----------|--------|---------------|
| Imperative/infinitive form | 5 | "Read the file", not "You should read the file" |
| Concrete and specific | 5 | "One-sentence answers", not "be concise" |
| No filler or meta-commentary | 5 | No "This section explains...", no padding |

**Common failures:**
- Second person throughout ("you should", "you can")
- Vague directives ("be thorough", "use best practices")
- Meta-commentary ("In this section we will discuss...")

## Token Efficiency (15 points)

| Criterion | Points | Pass Condition |
|-----------|--------|---------------|
| SKILL.md under 3000 tokens | 5 | Estimated: words * 1.3 |
| References under 2000 tokens each | 5 | Per-file check |
| Total skill under 10000 tokens | 5 | Sum of all files |

**Estimation method:**
```
tokens ~= word_count * 1.3
```

**Common failures:**
- SKILL.md over budget due to inline examples
- Single reference file contains all detail (split needed)
- Redundant content across files inflates total

---

# Output Templates

Format templates for each skill-forge mode. Use the matching template when producing output.

## Review Output

```
## Skill Review: {skill-name}

**Grade: {X}** ({score}/100)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Description Quality | {n}/25 | {finding} |
| Content Structure | {n}/25 | {finding} |
| Progressive Disclosure | {n}/20 | {finding} |
| Writing Style | {n}/15 | {finding} |
| Token Efficiency | {n}/15 | {finding} |

### Top 3 Issues
1. {issue + recommendation}
2. {issue + recommendation}
3. {issue + recommendation}
```

## Refactor Output

Review output above, plus:

```
### Suggested Rewrites

#### {Section/Element}
**Before:**
{current text}

**After:**
{improved text}

**Why:** {rationale}
```

Reference `refactoring-patterns.md` for common improvement patterns.

## Audit Output

```
## Skill Fleet Audit

| Skill | Grade | Lines | Tokens | Refs | Issues |
|-------|-------|-------|--------|------|--------|
| {name} | {grade} | {n} | {n} | {y/n} | {top issue} |

### Fleet Summary
- Total skills: {n}
- Average grade: {X}
- Critical issues: {list}
```

## Optimize Output

```
## Trigger Optimization: {skill-name}

**Current description:** {text}
**Issues:** {list}
**Suggested description:** {improved text}

**Trigger test phrases:**
- "{phrase}" -> should match: {yes/no}
```
