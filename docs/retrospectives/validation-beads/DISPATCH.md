# Dispatching Validation Runs

## Prerequisites

- CCP-2vo.5, CCP-2vo.6, CCP-2vo.7 must be closed (they are, per epic status)
- `--validation-mode` is implemented in bead-orchestrator (delivered in CCP-2vo.4)
- All 12 sibling beads are created in bd (done — see arm-mapping.md for IDs)
- You have `cld` available on PATH (`cld` is the pre-flight-checked launcher)

## Safety Contract

Each run MUST start from an identical main branch SHA. The validation-mode flag
in bead-orchestrator ensures no run mutates main (no merge/push/tag), so this
is guaranteed as long as no unrelated work is merged between pairs.

**Rule**: dispatch both siblings of a pair before merging any other work to main.

## Per-Pair Dispatch Procedure

For each canonical bead (01 through 06), repeat:

### Step 1 — Capture main SHA

```bash
git rev-parse HEAD
# Record this SHA in the retrospective table (docs/retrospectives/2026-XX-single-pane-validation.md)
# Both siblings must share this SHA.
```

### Step 2 — Dispatch control arm (full-2pane)

```bash
cld -b <bead_id_slug1> --mode=full-2pane --validation-mode=true
```

Example for canonical 01:
```bash
cld -b CCP-2vo.8.1 --mode=full-2pane --validation-mode=true
```

Wait for completion. When done:
- Record `run_id` from the bead notes: `bd show CCP-2vo.8.1` — look for `[VALIDATION] run_id=<uuid>`
- Verify main SHA unchanged: `git rev-parse HEAD` must equal the SHA from Step 1
- Record token count and wall-clock time: `sqlite3 ~/.claude/metrics.db "SELECT total_tokens, codex_total_tokens, wall_clock_s FROM bead_runs WHERE bead_id='CCP-2vo.8.1';"`

### Step 3 — Dispatch treatment arm (full-1pane)

```bash
cld -b <bead_id_slug2> --mode=full-1pane --validation-mode=true
```

Example for canonical 01:
```bash
cld -b CCP-2vo.8.2 --mode=full-1pane --validation-mode=true
```

Wait for completion. When done:
- Record `run_id` from bead notes
- Verify main SHA unchanged: must still equal the SHA from Step 1
- Record metrics

### Step 4 — Update retrospective table

Fill in one data row per run in `docs/retrospectives/2026-XX-single-pane-validation.md`.

---

## Bead ID — Canonical Mapping

| Canonical | Control bead (full-2pane) | Treatment bead (full-1pane) |
|-----------|--------------------------|------------------------------|
| 01-metrics-rollup-null-bug  | CCP-2vo.8.1  | CCP-2vo.8.2  |
| 02-codex-exec-timeout-bug   | CCP-2vo.8.3  | CCP-2vo.8.4  |
| 03-wave-token-refactor      | CCP-2vo.8.5  | CCP-2vo.8.6  |
| 04-bead-lint-dedup-task     | CCP-2vo.8.7  | CCP-2vo.8.8  |
| 05-metrics-endpoint-feature | CCP-2vo.8.9  | CCP-2vo.8.10 |
| 06-wave-report-ui-feature   | CCP-2vo.8.11 | CCP-2vo.8.12 |

---

## After All 12 Runs

### 1. Collect diffs

For each bead run, extract the diff from its worktree branch:

```bash
git diff main..worktree-bead-<id> -- . ':(exclude).beads'
```

### 2. Blind scoring

Spawn an Opus subagent for each run with:
- The canonical bead markdown (title, description, acceptance criteria, baseline sketch)
- The diff from the run
- The quality rubric (from the retrospective template)
- DO NOT include arm labels, mode flags, or this file

Collect `quality_score` (0–10) per run.

### 3. Join scores to arms

Use `arm-mapping.md` to map each slug back to its arm.

### 4. Compute pairwise deltas

For each canonical pair:
```
delta_tokens = control_tokens - treatment_tokens
delta_quality = treatment_quality - control_quality
verdict = KEEP if delta_tokens > 0 and delta_quality >= -0.5 else TUNE or REVERT
```

### 5. Write verdict

Update `docs/retrospectives/2026-XX-single-pane-validation.md` with final verdict.

---

## Exclusion Criteria

Exclude a run pair from analysis if:
- Main SHA diverged between the two siblings (external merge happened)
- Either run exited with an unhandled crash before Phase 5 (implementation)
- The diff is empty (bead was trivially no-op — indicates dispatch error)
- `quality_score` for both arms is ≤ 3 (both implementations were poor — canonical bead may be malformed)

Excluded pairs should be noted in the retrospective Exclusion section with reason.
Re-run with a fresh canonical bead if >2 pairs are excluded.
