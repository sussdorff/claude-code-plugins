---
name: vision-author
description: >
  Guided PO-grade 7-question dialogue producing a structured, present-tense-enforced vision.md
  with locked sections and 4-column boundary table. Use when starting a new project or formalizing
  a vision. Triggers on "vision author", "author vision", "create vision", "vision document".
model: opus
disable-model-invocation: true
---

# Vision Author

Produces a structured `docs/vision.md` file through a guided 7-question dialogue. Every answer
is validated for present tense, non-blank content, and section-assignment rules before being
saved. The output is a v1-template vision.md consumed by architecture-scout, review-agent,
and the implementation orchestration workflow in Phase 2.

---

## Arguments

| Flag | Effect |
|------|---------|
| (none) | Full 7-question dialogue producing a new vision.md |
| `--refresh` | Re-author mode: load existing vision.md as defaults, walk through Q&A |

---

## Phase 0: Tense-Gate Probe

Before anything else, verify the tense-gate linter is available.

```bash
python3 <skill-dir>/scripts/probe-tense-gate.py
```

Where `<skill-dir>` is the directory where the /vision-author skill is installed (e.g. `~/.claude/skills/vision-author`).

If the probe fails (exit 2), stop immediately. Do NOT proceed to Phase 1.

---

## --refresh Mode: Pre-Scan Gate

If `--refresh` was passed:

1. Locate `docs/vision.md`. If not found, inform the user and fall through to normal Q&A.
2. Run conformance check:

```bash
python3 <skill-dir>/scripts/check-conformance.py docs/vision.md
```

Parse result: if the script exits 0, proceed. If it exits non-zero, print its output and abort.

3. If the check-conformance.py script exits non-zero:
   - Print: "CONFORMANCE FAILURE: Cannot load existing vision.md as defaults."
   - Print the output from the script (missing sections / errors)
   - Print: "Options: (a) Fix the vision.md manually, then retry --refresh. (b) Run /vision-author (no --refresh) to re-author from scratch."
   - Exit with code 1. Do NOT proceed with --refresh dialogue.

4. If conformant: load current values using `parse_vision(Path("docs/vision.md"))` and use
   them as defaults for each question (shown in brackets as the default answer).

---

## Phase 1–7: Guided Q&A Dialogue

Work through each question in order. For every question:

1. Present the question with framing and (in --refresh mode) the current default in brackets
2. Accept user answer
3. Validate the answer (tense gate, STUB/TBD check, length/count constraints)
4. On validation failure: show the specific error message and re-prompt (do not advance)
5. On success: confirm "✓ Section saved" and continue to the next question

Save all answers to `docs/vision.md.draft` as each question completes (incremental write).

### STUB/TBD Detection Rule

Before tense-gate validation, check for placeholder markers. If the answer (stripped) matches
any of:
- Empty string / whitespace only
- Starts with or equals: "TBD", "STUB", "TODO", "placeholder", "N/A", "?"
- Contains: "to be determined", "to be decided", "to be locked"

Then: reject with message:
```
REJECTED: Placeholder answer detected ("<value>").
Vision sections must contain real, decided content — not deferred text.
If you don't have an answer yet, create a bead first:
  bd create --title="[VISION-BLOCK] <question> — undecided" --type=task
Then return and complete this question when you have the answer.
```

### Tense Gate Validation Rule

After STUB detection, run tense gate on every answer:

```bash
python3 <skill-dir>/scripts/validate-tense.py << 'TENSE_GATE_EOF'
<answer_text>
TENSE_GATE_EOF
```

Exit 0 = no violations (proceed). Exit 1 = violations listed on stdout (reject the answer, show violations, re-prompt).

If violations > 0, reject:
```
REJECTED: Future-tense language detected.
Violations:
  line N: [tag] explanation
    Found: 'offending text'

Rewrite the answer in present tense. Vision sections describe what IS true now,
not what will be true in the future.
```

---

## Q1: Vision Statement

**Question to ask:**
```
## Q1: Vision Statement

What is this product's core identity — what does it DO and WHO does it serve?

Rules:
  - One sentence only
  - 30 words maximum
  - Present tense (no "will", "should", "plan to")
  - No STUB/TBD placeholders

Example: "We build tools that make developers faster by removing workflow friction."

Your vision statement:
```

**Validation:**
1. STUB/TBD check
2. Tense gate
3. Word count: count `answer.split()`. If > 30: reject with "Vision statement is N words — must be ≤30 words. Condense to one tight sentence."
4. Sentence count: if more than one sentence (contains `.` followed by a capital letter after stripping): warn and ask to condense.

**On success:** Save to draft, print "✓ Section saved: Vision Statement (N words)"

---

## Q2: Target Group

**Question to ask:**
```
## Q2: Target Group

Who specifically uses this product? Be concrete — name the role, context, and scale.

Rules:
  - 1–2 sentences
  - Specific enough to be actionable (not just "developers")
  - Present tense

Example: "Software developers working in mid-size teams on long-lived codebases."

Your target group:
```

**Validation:** STUB/TBD check, then tense gate.

**On success:** Save to draft, print "✓ Section saved: Target Group"

---

## Q3: Core Need (JTBD)

**Question to ask:**
```
## Q3: Core Need

What job does your target group need to get done? What pain does this product remove?
Use Jobs-to-be-Done framing: "Teams need to..." / "Developers need to..."

Rules:
  - Present tense (what they need NOW)
  - No product solution language (that goes in Q4/Positioning)
  - No STUB/TBD

Example: "Teams need to maintain architectural quality across many contributors without constant manual review."

Your core need:
```

**Validation:** STUB/TBD check, then tense gate.

**On success:** Save to draft, print "✓ Section saved: Core Need"

---

## Q4: Positioning

**Question to ask:**
```
## Q4: Positioning

How does this product win against alternatives? Use the "For X who Y, our Z provides W
that no other V offers" pattern.

Rules:
  - Names the alternative or status quo being displaced
  - Articulates unique differentiated value
  - Present tense
  - No STUB/TBD

Example: "For developer teams that struggle with architectural drift, our tool suite
provides automated boundary enforcement that no other plugin ecosystem offers with zero config."

Your positioning statement:
```

**Validation:** STUB/TBD check, then tense gate.

**On success:** Save to draft, print "✓ Section saved: Positioning"

---

## Q5: Value Principles

**Question to ask:**
```
## Q5: Value Principles

What are the 3–5 behavioral invariants of this product? Each is a positive, present-tense
statement of how the system works — not aspirations, not negations.

Format each principle as:
  - **P1**: [principle text]
  - **P2**: [principle text]
  ...up to **P5**

Then for each principle, I'll ask for a "scope" (which part of the system this governs).

Rules:
  - Exactly 3–5 principles (no more, no fewer)
  - Present tense only — no "will", "should", "plan to"
  - Positive assertions (what IS true), not negations
  - IDs P1..P5 must be slug-stable (don't renumber existing principles on --refresh)
  - No STUB/TBD

Example:
  - **P1**: All architectural boundaries are enforced at commit time, not review time.
  - **P2**: Every rule is expressed once and consumed by all tooling.
  - **P3**: Developers see violations in context, not in a separate CI dashboard.

Your value principles (list all at once, then we'll collect scopes):
```

**Collection and Validation:**

1. Parse lines matching `- **P{N}**: text` or `* **P{N}**: text`
2. Count check:
   - < 3: reject — "Need at least 3 principles. Add more or reconsider your scope constraints."
   - > 5: reject and offer extras-as-beads:
     ```
     Too many principles ({count} entered, max 5). Extra principles belong in NOT in Vision
     as deferred capabilities, or can be tracked as beads.
     
     Options:
       (a) Choose 3–5 to keep in the vision; I'll create beads for the rest.
       (b) Re-enter a condensed list of 3–5 principles.
     
     Which extras would you like to convert to beads? (or enter 'b' to re-enter all)
     ```
3. For each accepted principle: run tense gate individually
4. Overlap check: compute token overlap between each pair of principles.
   If any pair has >60% token overlap:
   ```
   WARNING: Principles P{a} and P{b} share >60% token overlap.
   P{a}: "..."
   P{b}: "..."
   Consider merging them into one principle or making them more distinct.
   Continue anyway? (y/n)
   ```

5. For each principle, ask for its scope:
   ```
   Scope for P{N} ("{principle text}"):
   (Which part of the system or workflow does this principle govern?)
   > 
   ```

6. Generate boundary table from principles + scopes.

**On success:** Save principles + boundary table to draft, print "✓ Section saved: Value Principles (N principles, boundary table generated)"

---

## Q6: Business Goal

**Question to ask:**
```
## Q6: Business Goal

What is the single most important measurable outcome metric for this product?

Rules:
  - One metric with a time horizon
  - Quantified: "Reduce X by Y% within Z timeframe"
  - No roadmap dates ("by Q3", "by 2027") — use relative time ("within 6 months")
  - Present or imperative tense — no "will reduce"
  - No STUB/TBD

Example: "Reduce architectural drift incidents by 80% within the first quarter of adoption."

Your business goal:
```

**Validation:** STUB/TBD check, then tense gate.

**On success:** Save to draft, print "✓ Section saved: Business Goal"

---

## Q7: NOT in Vision

**Question to ask:**
```
## Q7: NOT in Vision

What does this product explicitly NOT do in its current vision? These are conscious scope
constraints — things you're deliberately deferring or excluding.

Rules:
  - At least 2 items
  - Each item is a noun phrase or short statement (not a long explanation)
  - These should be bead-eligible (trackable as future work)
  - No STUB/TBD

Format:
  - [Deferred capability or excluded scope]
  - [Another deferred item]

Example:
  - Auto-fixing violations without developer confirmation
  - Supporting non-git version control systems
  - Replacing human code review entirely

Your NOT-in-Vision items:
```

**Collection and Validation:**

1. Parse bullet items (`- ` or `* ` lines)
2. Count check: < 2 items → reject — "List at least 2 explicitly deferred items."
3. STUB/TBD check on each item
4. Tense gate on the full NOT-in-Vision block
5. **Q5 cross-check**: For each Q7 item, check if it contains keywords that appear to negate a Q5 principle.
   If potential negation detected:
   ```
   WARNING: Q7 item may negate Q5 principle P{N}:
     P{N}: "{principle}"
     Q7:   "{item}"
   
   This could create a contradiction in your vision document.
   Options:
     (a) Rephrase the Q7 item to avoid the conflict
     (b) Rephrase P{N} in Q5 to clarify scope
     (c) Accept as-is (add a tense-gate-ignore comment in the ADR)
   ```

6. For each accepted Q7 item, offer bead creation:
   ```
   Create a tracking bead for "{item}"?
   This runs: bd create --title="[ROADMAP] {item}" --type=task
   (y/n, or 'all' to create for all items)
   ```

**On success:** Save to draft, print "✓ Section saved: NOT in Vision (N items)"

---

## Phase 8: Atomic Write + Genesis ADR

After all 7 questions succeed:

### Step 1: Render and validate the complete vision.md

Save all collected answers to `/tmp/vision-answers-<session>.json` with the structure:
```json
{
  "vision_statement": "...",
  "target_group": "...",
  "core_need": "...",
  "positioning": "...",
  "principles": [["P1", "text"], ["P2", "text"]],
  "principle_scopes": {"P1": "scope1", "P2": "scope2"},
  "business_goal": "...",
  "not_in_vision": ["item1", "item2"]
}
```

Then render:
```bash
python3 <skill-dir>/scripts/render-vision-cli.py /tmp/vision-answers-<session>.json > /tmp/vision-content-<session>.md
```

Run tense gate on the rendered content as a final check:
```bash
cat /tmp/vision-content-<session>.md | python3 <skill-dir>/scripts/validate-tense.py
```

### Step 2: Atomic write

```bash
cat /tmp/vision-content-<session>.md | python3 <skill-dir>/scripts/write-vision-atomic.py
```

Print: "docs/vision.md written (atomic rename from draft)"

### Step 3: Genesis ADR creation

Create `docs/adr/0000-vision-initial.md` using `render_genesis_adr` from `scripts/vision_renderer.py`:

```bash
python3 <skill-dir>/scripts/write-genesis-adr.py
```

This uses the git repo directory name as the project name.

Print: "docs/adr/0000-vision-initial.md created (genesis ADR)"

---

## Completion Summary

After Phase 8 completes, print:

```
╔══════════════════════════════════════════════════════════╗
║  /vision-author complete                                  ║
╠══════════════════════════════════════════════════════════╣
║  docs/vision.md          — created (v1 template)          ║
║  docs/adr/0000-vision-initial.md — genesis ADR            ║
╠══════════════════════════════════════════════════════════╣
║  Next steps:                                              ║
║  1. Run tense-gate: python3 scripts/tense-gate.py docs/vision.md
║  2. Review: /vision-review docs/vision.md                ║
║  3. Commit: git add docs/ && git commit -m "docs: add vision.md"
╚══════════════════════════════════════════════════════════╝
```

---

## --refresh Mode: Mutation ADR

In --refresh mode, instead of creating `0000-vision-initial.md`, create a mutation ADR:

```
docs/adr/NNNN-vision-mutation-{date}.md
```

Where NNNN is the next sequential ADR number. Frontmatter:

```markdown
# ADR-NNNN: Vision Mutation — {date}

**Status:** accepted
**Date:** {date}
**Generated by:** /vision-author --refresh
**Template version:** 1
**Supersedes:** 0000-vision-initial.md

## Context

This is a vision mutation. The following sections were changed from their previous values:
[list the changed sections and their old vs new values]

## Decision

The vision has been updated as reflected in `docs/vision.md`.

## Consequences

[Same as genesis ADR consequences]
```

---

## Do NOT

- Do NOT skip the tense-gate probe (Phase 0) — missing tense-gate is a hard stop
- Do NOT advance past a question with a validation failure — always re-prompt
- Do NOT write to `docs/vision.md` directly during the dialogue — use `docs/vision.md.draft`
- Do NOT skip the genesis ADR (Phase 8, Step 3)
- Do NOT create the ADR before the atomic write of vision.md (order matters)
- Do NOT allow fewer than 2 items in NOT in Vision (Q7)
- Do NOT number principles by position — use authored P-IDs from the user's input

## Resources

- `references/vision-template.md` — locked v1 template with section-assignment rules
- `references/smoke-test-checklist.md` — manual smoke test checklist
- `scripts/vision_renderer.py` — renders VisionAnswers -> vision.md text
- `scripts/vision_conformance.py` — v1 conformance scanner (for --refresh mode)
- `scripts/vision_parser.py` — parses existing vision.md into structured data
- `scripts/tense-gate.py` — lints prescriptive-present documents for future-tense markers
