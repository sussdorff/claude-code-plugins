# Brand Review Checklist

Scoring criteria for evaluating brand profile quality. Use during Review mode.

## Completeness (25 points)

| Criterion | Points | Pass Condition |
|-----------|--------|----------------|
| Required frontmatter | 5 | `name`, `type`, `description`, `version` all present |
| Type-matching sections | 8 | Voice type has Voice Profile sections; visual has Visual Profile sections |
| At least 1 good example | 5 | `<example-good>` block present (voice/combined types) |
| Vocabulary lists | 4 | Prefer and Avoid subsections populated (voice/combined) |
| Description meaningful | 3 | Description explains purpose, not just "a brand profile" |

**Common failures:**
- Missing `<example-good>` block (most frequent)
- Type is `voice` but Visual Profile sections present (or vice versa)
- Empty Vocabulary subsections with placeholder text

## Specificity (25 points)

| Criterion | Points | Pass Condition |
|-----------|--------|----------------|
| Concrete tone rules | 5 | "Use active voice" not "be clear" |
| Vocabulary with rationale | 5 | Each preferred/avoided term explains WHY |
| Measurable constraints | 5 | Numbers where possible: "max 2 sentences per paragraph", "hex #3B82F6" |
| Do/don't pairs | 5 | Rules stated as "do X, not Y" with contrast |
| Examples match rules | 5 | Good example demonstrably follows the stated rules |

**Common failures:**
- Vague adjectives without actionable rules ("warm and friendly")
- Vocabulary lists without rationale (just word lists)
- Rules that cannot be verified ("use appropriate tone")

## Actionability (20 points)

| Criterion | Points | Pass Condition |
|-----------|--------|----------------|
| Skill-ready rules | 8 | A skill reading this profile can apply rules without interpretation |
| Clear do/don't format | 6 | Rules stated as instructions, not descriptions |
| Bad example included | 6 | `<example-bad>` block shows what to avoid |

**Common failures:**
- Descriptive rather than prescriptive ("the tone is warm" vs "use encouraging language, avoid neutral phrasing")
- No bad example -- leaves violation boundary undefined
- Rules require external context to apply

## Consistency (15 points)

| Criterion | Points | Pass Condition |
|-----------|--------|----------------|
| No contradictions | 5 | Tone section does not conflict with Writing Rules |
| Examples match profile | 5 | Good/bad examples align with stated rules |
| Parent/child alignment | 5 | If `inherits`: child overrides are intentional, not accidental duplicates |

**Common failures:**
- Tone says "direct and concise" but examples use long flowing sentences
- Child profile restates parent rules identically (wasted tokens)
- Vocabulary avoid-list terms appear in examples

## Token Efficiency (15 points)

| Criterion | Points | Pass Condition |
|-----------|--------|----------------|
| Under 2000 tokens | 5 | `word_count * 1.3 < 2000` |
| No redundancy | 5 | No repeated rules across sections |
| Inheritance used | 5 | Shared rules in parent, only overrides in child (if applicable) |

**Estimation method:**
```
tokens ~= word_count * 1.3
```

**Common failures:**
- Inline examples inflating token count (move verbose examples to separate reference)
- Restating inherited rules in child profile
- Description repeating what body sections already cover

---

## Grade Scale

| Grade | Score | Meaning |
|-------|-------|---------|
| A | 90-100 | Production-ready, no changes needed |
| B | 75-89 | Good, minor improvements possible |
| C | 60-74 | Usable but needs work on 1-2 dimensions |
| D | 40-59 | Significant gaps, rework required |
| F | 0-39 | Missing critical elements, start over |

## Review Output Template

```
## Brand Review: {brand-name}

**Grade: {X}** ({score}/100)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Completeness | {n}/25 | {finding} |
| Specificity | {n}/25 | {finding} |
| Actionability | {n}/20 | {finding} |
| Consistency | {n}/15 | {finding} |
| Token Efficiency | {n}/15 | {finding} |

### Top 3 Issues
1. {issue + recommendation}
2. {issue + recommendation}
3. {issue + recommendation}
```
