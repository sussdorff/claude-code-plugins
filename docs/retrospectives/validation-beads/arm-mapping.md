# Arm Mapping — A/B Validation (CCP-2vo.8)

## WARNING: This file must NOT be passed to the rubric scorer agent.

The rubric scorer receives only the diff, bead title, and acceptance criteria.
It must NOT see this file, arm labels, or any metadata indicating which arm
a given run belongs to.

## Mapping Table

| Canonical | Slug 1 → Arm | Bead ID 1 | Slug 2 → Arm | Bead ID 2 |
|-----------|--------------|-----------|--------------|-----------|
| 01-metrics-rollup-null-bug       | xjmt → full-2pane (control)   | CCP-2vo.8.1  | kpnv → full-1pane (treatment) | CCP-2vo.8.2  |
| 02-codex-exec-timeout-bug        | bqwr → full-2pane (control)   | CCP-2vo.8.3  | fhzd → full-1pane (treatment) | CCP-2vo.8.4  |
| 03-wave-token-refactor           | cysn → full-2pane (control)   | CCP-2vo.8.5  | gltu → full-1pane (treatment) | CCP-2vo.8.6  |
| 04-bead-lint-dedup-task          | dpek → full-2pane (control)   | CCP-2vo.8.7  | hwqf → full-1pane (treatment) | CCP-2vo.8.8  |
| 05-metrics-endpoint-feature      | ergx → full-2pane (control)   | CCP-2vo.8.9  | ivcm → full-1pane (treatment) | CCP-2vo.8.10 |
| 06-wave-report-ui-feature        | fzlb → full-2pane (control)   | CCP-2vo.8.11 | jpas → full-1pane (treatment) | CCP-2vo.8.12 |

## Slug Generation Note

Slugs were chosen as opaque 4-character lowercase alphanumeric strings that carry
no semantic content. The first slug in each row is always the control arm
(full-2pane), the second is always the treatment arm (full-1pane).

## Blinding Protocol

1. When dispatching, the dispatcher sees both bead IDs from the table above
   and dispatches them with the correct `--mode` flag (see DISPATCH.md).
2. After both runs complete, the scorer agent is given only:
   - The bead title and description (from the canonical `.md` file)
   - The git diff produced by each run
   - The quality rubric
   The scorer agent does NOT receive arm labels or this file.
3. The scorer returns a `quality_score` per slug.
4. The analyst then joins scores back to arms using this table.
