# Vision Template v1 — Locked Sections and Section-Assignment Rules

This is the authoritative reference template for vision.md files produced by `/vision-author`.
The section layout is **locked**: consumers (architecture-scout, review-agent, bead-orchestrator Phase 2)
parse this format by position and name. Do not add, remove, or rename sections without an ADR.

---

## Template v1 Frontmatter

Every generated vision.md MUST begin with this exact frontmatter block:

```yaml
---
document_type: prescriptive-present
template_version: 1
generator: vision-author
---
```

| Field | Value | Purpose |
|-------|-------|---------|
| `document_type` | `prescriptive-present` | Activates tense-gate pre-commit hook |
| `template_version` | `1` | Parser version signal (vision_parser.py) |
| `generator` | `vision-author` | Provenance tracking |

---

## Section-Assignment Rules

These rules determine which answer belongs in which section. The rules are normative —
violations are detected by `/vision-author --refresh` and flagged as conformance errors.

### Q1 → `## Vision Statement`

**Rule: One sentence, ≤30 words, present-tense, no conditional language.**

- Captures WHAT the product IS and WHO it serves in the simplest possible terms
- Must be present tense: "We build X" not "We will build X"
- Must NOT contain: competitive framing, technical details, roadmap language
- Must NOT overlap with: Positioning (Q4) or Business Goal (Q6)

**Belongs here**: Core identity claim — the product's reason for existence.

**Does NOT belong here**: Market differentiation, success metrics, feature lists.

---

### Q2 → `## Target Group`

**Rule: One or two sentences defining the specific audience segment.**

- States WHO uses this product in concrete, observable terms
- Must NOT be so broad it's meaningless ("developers" alone is insufficient)
- Must NOT overlap with: Vision Statement, Core Need, or Positioning

**Belongs here**: The specific human role, context, and scale (e.g. "mid-size teams").

**Does NOT belong here**: Their pain points (that's Q3/Core Need), market size claims.

---

### Q3 → `## Core Need (JTBD)`

**Rule: The job-to-be-done — what the target group is trying to accomplish.**

- Uses Jobs-to-be-Done framing: "Teams need to..." / "Developers need to..."
- Present tense: what they need NOW, not what they will need
- Must NOT overlap with: Vision Statement (that's your solution), Positioning (competitive framing)

**Belongs here**: The functional and emotional need the product resolves.

**Does NOT belong here**: How your product solves it, competitor comparisons.

---

### Q4 → `## Positioning`

**Rule: Competitive framing using the "For X who Y, our Z provides W" pattern.**

- Explicitly names the alternative or status quo being displaced
- Articulates the unique differentiated value
- Must NOT overlap with: Vision Statement (identity), Value Principles (invariants), Business Goal (metrics)

**Belongs here**: Why this product wins in the market against alternatives.

**Does NOT belong here**: Present-tense invariants (those go in Q5), success metrics (Q6).

---

### Q5 → `## Value Principles`

**Rule: 3–5 invariants, each a positive present-tense statement of how the product behaves.**

Principles are the MOST constrained section:

1. **Count**: Exactly 3–5. Fewer means the product isn't differentiated enough; more means you haven't prioritized.
2. **Form**: Each principle starts with `- **P{N}**:` and uses a slug-stable ID (P1, P2, ...).
3. **Tense**: Present tense ONLY. "Boundaries are enforced" not "Boundaries will be enforced".
4. **Tone**: Positive assertions of what IS true. NOT negations, NOT aspirations.
5. **Scope**: Each principle maps to exactly one row in the 4-column boundary table.

**OVERLAP PREVENTION (critical)**:
- **NOT Positioning** (Q4): Principles state how the system works, not why it beats competitors.
- **NOT NOT-in-Vision** (Q7): Principles are positive invariants; deferred items go in Q7.
- **NOT Business Goal** (Q6): Principles are behavioral truths; goals are metrics.

**Overlap warning trigger**: >60% token overlap between any two principles triggers a warning.
Resolve by merging, splitting, or moving one to another section.

**Boundary table** (required, immediately after principle list):

| rule_id | rule | scope | source-section |
|---------|------|-------|----------------|
| P1 | [principle text verbatim or paraphrased] | [system scope] | Value Principles |

- `rule_id` MUST match a principle's P-prefix ID (slug-stable, not position-assigned)
- `scope` describes which system boundary the principle governs
- `source-section` is ALWAYS "Value Principles" (literal string)

---

### Q6 → `## Business Goal`

**Rule: One measurable outcome metric with a time horizon.**

- Must be quantified: "Reduce X by Y% within Z months"
- Present tense framing: "The product reduces..." or imperative "Reduce X by Y..."
- Must NOT contain roadmap language ("by Q3", "by 2027") — those trigger tense-gate
- Must NOT overlap with: Principles (behavioral truths), Positioning (market claim)

**Belongs here**: The single most important success metric.

**Does NOT belong here**: Multiple metrics (pick one), roadmap milestones, feature lists.

---

### Q7 → `## NOT in Vision`

**Rule: 2+ explicitly deferred items — things the product actively refuses to do in this version.**

- Each item starts with `- ` and is written as a noun phrase or brief statement
- Items represent conscious scope constraints, not just things that haven't been built yet
- Each item should be bead-eligible: "bd create --title='[ROADMAP] <item>'"
- Must NOT overlap with: Principles (positive invariants), Vision Statement (identity)

**CRITICAL OVERLAP CHECK with Q5**: If a Q7 item appears to negate a Q5 principle,
the `/vision-author` skill will flag this for reconciliation. Example conflict:
- P1: "All boundaries are enforced automatically"
- Q7: "Manual override bypass for emergency fixes" ← negates P1, needs reconciliation

**Belongs here**: Deferred features, excluded use cases, explicitly out-of-scope capabilities.

**Does NOT belong here**: Things that haven't been decided (use beads for those), vague disclaimers.

---

## Complete Template Structure

```markdown
---
document_type: prescriptive-present
template_version: 1
generator: vision-author
---

## Vision Statement

[One sentence, ≤30 words, present tense]

## Target Group

[Specific audience segment, 1-2 sentences]

## Core Need (JTBD)

[Job-to-be-done, present tense]

## Positioning

[Competitive framing: "For X who Y, our Z provides W that no other V offers"]

## Value Principles

- **P1**: [Invariant principle 1 — positive, present tense]
- **P2**: [Invariant principle 2 — positive, present tense]
- **P3**: [Invariant principle 3 — positive, present tense]

| rule_id | rule | scope | source-section |
|---------|------|-------|----------------|
| P1 | [rule text] | [scope] | Value Principles |
| P2 | [rule text] | [scope] | Value Principles |
| P3 | [rule text] | [scope] | Value Principles |

## Business Goal

[Measurable outcome: "Reduce X by Y% within Z timeframe"]

## NOT in Vision

- [Deferred item 1]
- [Deferred item 2]
```

---

## Mutation Protocol (--refresh)

When modifying an existing vision.md:

1. **Conformance gate**: `/vision-author --refresh` runs `check_conformance()` before loading defaults.
   - Missing sections → cannot refresh, must re-author
   - Bad boundary table → cannot refresh, must re-author

2. **Stability rule**: `rule_id` values (P1, P2, ...) are slug-stable. Do not renumber existing
   principles during a refresh — consumers may reference P-IDs in beads and ADRs.

3. **ADR required**: Every mutation produces a new `docs/adr/*-vision-mutation-*.md` with
   `supersedes: 0000-vision-initial.md` in the frontmatter.

4. **Tense gate**: All sections re-validated after mutation. Any future-tense language in any
   section causes the mutation to abort with a list of violations.
