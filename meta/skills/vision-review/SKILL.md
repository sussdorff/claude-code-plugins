---
name: vision-review
model: sonnet
trinity_role: enforcer-reactive
description: >-
  Vision health check: review each principle Y/N with evidence, compute a health score,
  generate draft ADRs for contested principles. Triggers on: vision review, review vision,
  vision health, vision health check, re-evaluate vision.
---

# Vision Review

Evaluate each principle in a project's `vision.md` against current reality. Produces a Vision Health Score, generates draft ADRs for contested principles, and surfaces a re-author recommendation when the score drops below 80%.

## Overview

Vision Review is a cadence-triggered enforcer-reactive skill. It does not modify `vision.md` directly — it creates auditable draft ADRs in `docs/adr/drafts/` and a review report in `docs/`. The skill drives an interactive per-principle dialog with the user, invokes `/council` (or degrades gracefully), and delegates all file I/O to `scripts/vision_review.py`.

**Trinity role**: Enforcer-Reactive — checks existing vision against current reality after the fact.

## When to Use

- "vision review" / "review vision"
- "vision health" / "vision health check"
- "re-evaluate vision" / "vision health score"
- Quarterly or after major architecture changes
- After `/vision-author` to validate alignment

Do NOT use for: editing vision.md directly (use `/vision-author --refresh`), creating new visions (use `/vision-author`), or non-vision document reviews.

## Workflow

### Step 1: Load Vision

Parse the project's vision file (default: `docs/vision.md`):

```bash
python3 scripts/vision_review.py docs/vision.md --output-dir docs/ --adr-dir docs/adr/drafts/ --max-principles 5
```

If the path differs, ask the user before proceeding. Exit with a clear error if the file does not exist or fails to parse.

### Step 2: Per-Principle Y/N Dialog

For each principle in `vision.principles`, conduct an interactive dialog:

```
[P1] All architectural boundaries are enforced at commit time.

Is this principle still accurate? [Y/n]:
Evidence (why it holds or why it is contested):
```

- Accept `Y` (or blank) as confirmed. Accept `N` as contested.
- Require at least one sentence of evidence for any `N` answer.
- Record each result as a `PrincipleResult` (principle_id, confirmed, evidence).

### Step 3: Council Integration

For each contested principle (confirmed = N), invoke `/council` for a second opinion
via [scripts/council_review.py](scripts/council_review.py). The script invokes the
`business:council` subagent with `principle_id`, `principle_text`, and `evidence`.

**Degraded mode**: If the council Agent raises an exception or is unavailable, fall back to a single-perspective Haiku critique:

```
⚠️ WARNING: Council (CCP-bw6) was unavailable. Using degraded mode (single-perspective Haiku critique).
council_mode: degraded
```

Surface this warning explicitly to the user in the output.

Set `council_mode`:
- `"full"` — council responded successfully
- `"degraded"` — council unavailable, Haiku fallback used
- `"skipped"` — no principles were contested

### Step 4: Generate Output

After collecting all per-principle results, invoke the script functions to produce output files:

**Draft ADRs** (one per contested principle):

Call [scripts/generate_adr.py](scripts/generate_adr.py), which wraps
`vision_review.generate_draft_adr` with `principle`, `evidence`, `council_finding`
(None if council skipped), `run_date`, and `adr_dir`.

Draft ADR filenames: `vision-mutation-<rule_id>-<YYYYMMDD-HHMMSS>.md`
The `supersedes` field uses the authored rule_id (e.g. `P1`), NOT a positional index.

**Review report**:

Call [scripts/generate_report.py](scripts/generate_report.py), which wraps
`vision_review.compute_health_score` and `vision_review.generate_review_report`
with `vision_path`, `results`, `confirmed_ids`, `total_count`, `council_mode`, and `report_dir`.

### Step 5: Present Results

Report the Vision Health Score and next steps:

```
Vision Health Score: 66.67% (2 of 3 principles confirmed)

Draft ADRs generated:
  - docs/adr/drafts/vision-mutation-P2-20260422-120000.md

Review report: docs/vision-review-20260422-120000.md
council_mode: full
```

If `health_score < 80`:

```
⚠️ Health score is below 80%. Consider invoking `/vision-author --refresh` for a full re-author session.
```

## Smoke Test / Mock Mode

For automated testing, pass `--mock-council` and `--yes` flags to skip interaction:

```bash
python3 scripts/vision_review.py tests/fixtures/vision/valid.md \
  --mock-council tests/fixtures/vision-review/mock_council.json \
  --yes \
  --output-dir /tmp/ \
  --adr-dir /tmp/adr-drafts/
```

Exit code 0 = success. Exit code 1 = parse error or hard failure.

## Triggers

This skill is **on-demand only** for the MVP. Invoke it manually or via a project health schedule. Cron-based and signal-based auto-triggers are architectural references for future implementation only — they are NOT active in this version.

## Limitations

- Requires a valid v1 `vision.md` (produced by `/vision-author`). Rejects files with wrong `template_version`.
- Maximum 5 principles by default (override with `--max-principles N`).
- Does NOT modify `vision.md` — creates draft ADRs only.
- Council integration requires the `business:council` subagent (CCP-bw6). Degrades gracefully if unavailable.
- Cron/signal-based triggers are NOT implemented in MVP (on-demand only).
