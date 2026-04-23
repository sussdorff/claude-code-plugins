# Vision Author Smoke Test Checklist

Manual verification steps for the `/vision-author` skill. Run this checklist after any change
to the skill, renderer, or conformance scanner.

## Pre-conditions

- [ ] `scripts/tense-gate.py` exists at the project root
- [ ] `scripts/vision_renderer.py` exists and imports cleanly: `python3 scripts/vision_renderer.py`
- [ ] `scripts/vision_conformance.py` exists and imports cleanly: `python3 scripts/vision_conformance.py`
- [ ] All unit tests pass: `uv run pytest tests/test_vision_author.py -v`

---

## Scenario 1: Happy Path — Full 7-Question Dialogue

Invoke the skill in a fresh Claude session:

```
/vision-author
```

- [ ] **Phase 0 probe**: Skill reports tense-gate found (or exits with exit-2 if missing)
- [ ] **Q1 (Vision Statement)**: Asked for a ≤30-word present-tense sentence
  - Enter: "We build tools that make developers faster by removing workflow friction."
  - [ ] Skill confirms "✓ Section saved" and advances to Q2
- [ ] **Q2 (Target Group)**: Asked for the specific audience segment
  - Enter: "Software developers working in mid-size teams on long-lived codebases."
  - [ ] Skill confirms "✓ Section saved" and advances to Q3
- [ ] **Q3 (Core Need)**: Asked for the JTBD
  - Enter: "Teams need to maintain architectural quality across many contributors without constant manual review."
  - [ ] Skill confirms "✓ Section saved" and advances to Q4
- [ ] **Q4 (Positioning)**: Asked for competitive framing
  - Enter: "For developer teams that struggle with architectural drift, our tool suite provides automated boundary enforcement that no other plugin ecosystem offers with zero config."
  - [ ] Skill confirms "✓ Section saved" and advances to Q5
- [ ] **Q5 (Value Principles)**: Asked for 3-5 principles in `**P1**: text` format
  - Enter three principles (P1, P2, P3) with scopes
  - [ ] Skill validates count (3 accepted), runs tense gate on each
  - [ ] Skill generates boundary table preview
  - [ ] Skill confirms "✓ Section saved" and advances to Q6
- [ ] **Q6 (Business Goal)**: Asked for measurable outcome
  - Enter: "Reduce architectural drift incidents by 80% within the first quarter of adoption."
  - [ ] Skill confirms "✓ Section saved" and advances to Q7
- [ ] **Q7 (NOT in Vision)**: Asked for 2+ deferred items
  - Enter two items
  - [ ] Skill offers to create beads for each item via `bd create`
  - [ ] Skill confirms "✓ Section saved"

**After Q7 completion**:
- [ ] `docs/vision.md` is created (atomic rename from `docs/vision.md.draft`)
- [ ] `docs/vision.md` passes tense-gate: `python3 scripts/tense-gate.py docs/vision.md` exits 0
- [ ] `docs/vision.md` is parseable: `python3 scripts/vision_parser.py docs/vision.md` exits 0
- [ ] `docs/adr/0000-vision-initial.md` is created with correct frontmatter

---

## Scenario 2: Validation Gates — STUB/TBD Rejection

- [ ] At Q1, enter: "TBD"
  - [ ] Skill rejects with STUB error, re-prompts Q1
  - [ ] Does NOT advance to Q2

- [ ] At Q1, enter: "STUB - placeholder for later"
  - [ ] Skill rejects with STUB error, re-prompts Q1

- [ ] At Q1, enter a blank line / empty input
  - [ ] Skill rejects, re-prompts Q1

---

## Scenario 3: Tense Gate — Future Tense Rejection

- [ ] At Q3 (Core Need), enter: "Teams will need architectural quality tooling."
  - [ ] Skill runs tense gate, detects "will need"
  - [ ] Skill shows violation with actionable hint (rewrite in present tense)
  - [ ] Skill re-prompts Q3

- [ ] At Q5, enter a principle: "The system will enforce boundaries at commit time."
  - [ ] Skill detects "will enforce" as future tense
  - [ ] Skill rejects principle, re-prompts for corrected version

---

## Scenario 4: Q5 Count Clamping

- [ ] Enter only 2 principles for Q5:
  - [ ] Skill rejects (<3 minimum), explains the constraint, re-prompts

- [ ] Enter 6 principles for Q5:
  - [ ] Skill rejects (>5 maximum)
  - [ ] Skill offers the "extras as beads" path: create beads for extras, accept 3-5
  - [ ] If user accepts, creates beads for the excess principles

---

## Scenario 5: --refresh Mode

Run on the vision.md created in Scenario 1:

```
/vision-author --refresh
```

- [ ] **Conformance gate**: Skill runs `check_conformance(docs/vision.md)`
  - [ ] All 7 sections found → proceeds to load defaults
  - [ ] If conformance fails → skill exits with actionable error listing missing sections

- [ ] **Defaults loaded**: Each question pre-filled with current vision.md content
  - [ ] Q1 shows current vision statement as default
  - [ ] User can accept default by pressing Enter or enter new text

- [ ] **After refresh**: New `docs/vision.md` written (via draft → atomic rename)
- [ ] **Mutation ADR**: `docs/adr/NNNN-vision-mutation-DESCRIPTION.md` created (not 0000)

---

## Scenario 6: Q7 Cross-Check Against Q5

Enter a Q7 item that appears to negate a Q5 principle:

- Q5 principle: "P1: All boundaries are enforced automatically at commit time."
- Q7 item: "Manual bypass of all boundary enforcement for emergency deployments"

- [ ] Skill detects potential negation of P1
- [ ] Skill warns: "Q7 item appears to negate P1. Reconcile or move to bead."
- [ ] Skill asks user to confirm or rephrase

---

## Scenario 7: Tense Gate Probe (Phase 0)

Test the probe with tense-gate missing:

```bash
# Temporarily rename tense-gate.py
mv scripts/tense-gate.py scripts/tense-gate.py.bak

# Invoke skill
/vision-author

# Restore
mv scripts/tense-gate.py.bak scripts/tense-gate.py
```

- [ ] Skill detects missing tense-gate at Phase 0
- [ ] Skill exits with exit code 2 (not 1)
- [ ] Error message includes actionable installation hint: "Install via: /tense-gate (CCP-2q2)"
- [ ] Skill does NOT proceed to Q1

---

## Expected Final State

After Scenario 1 completes successfully:

```
docs/
  vision.md          — v1 template, all 7 sections, tense-gate clean
  adr/
    0000-vision-initial.md  — Genesis ADR
```

No `docs/vision.md.draft` file remains (cleaned up by atomic rename).
