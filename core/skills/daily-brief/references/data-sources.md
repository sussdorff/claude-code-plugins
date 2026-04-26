# daily-brief: Data Sources Reference

Canonical map of which source is authoritative for which field, dedup rules,
fallback behavior, and which output sections are deterministic vs synthesized.

## Source Authority Map

| Field | Source | Authority | Notes |
|-------|--------|-----------|-------|
| `closed_beads` | beads (`bd`) | **Authoritative** | Deterministic — beads closed in the date window |
| `open_beads` | beads (`bd`) | **Authoritative** | Deterministic snapshot at query time |
| `ready_beads` | beads (`bd`) | **Authoritative** | Deterministic snapshot: unblocked, not yet started |
| `blocked_beads` | beads (`bd`) | **Authoritative** | Deterministic snapshot: blocked beads |
| `decision_requests` | beads (`bd human`) | **Authoritative** | Beads flagged for human decision |
| `commits` | git log | **Authoritative** | Standalone commits not linked to a closed bead |
| `sessions` | open-brain (type=session_summary, debrief) | **Authoritative** | Session summaries and debrief entries |
| `learnings` | open-brain (type=learning) | **Authoritative** | Learning entries in memory |
| `decisions` | open-brain (type=decision) | **Authoritative** | Decision entries in memory |
| `followups` | open-brain | **Authoritative** | Lines with `Decide:`, `Need input:`, `Follow-up:` prefixes |
| `rework_signals` | git (revert commits) + beads (supersede events) | **Authoritative** | Revert commits + bead supersede events |
| `capabilities` | capability-extractor.py (derives from closed_beads + sessions) | Synthesized | Empty list |
| `warnings` | — | Diagnostic | Source unavailability notices (partial data indicator) |

## Dedup Rules

### Bead–Commit Deduplication

Commits that are associated with a closed bead appear under that bead in the
`closed_beads` list (as `bead.commits[]`). They are **not** duplicated in the
`commits` field. A commit appears in `commits` only if it is **not** linked to
any closed bead in the date window.

Rule: `commits` = git log for date − commits attributed to any `closed_beads`.

### Open-Brain Memory Deduplication

`sessions`, `learnings`, and `decisions` are separate open-brain query targets.
Entries can appear in multiple buckets if they carry multiple type tags. No
cross-bucket dedup is applied — the renderer may encounter the same memory ID
in multiple fields. This is intentional: a session_summary may also be tagged
as a learning.

### Rework Signal Sources

`rework_signals` aggregates two sub-sources:
1. `git` — revert commits in the date window (matched by `Revert "..."` subject pattern)
2. `beads` — supersede events (bead A superseded by bead B)

Both are included without dedup because they represent different kinds of
rework: git reverts are code rollbacks, supersede events are scope replacements.

## Fallback Behavior

Each source is queried independently. Failures are non-blocking — they produce
a `warnings` entry and the brief is rendered with partial data.

| Source | Fallback behavior on failure |
|--------|------------------------------|
| beads (`bd`) | `closed_beads`, `open_beads`, `ready_beads`, `blocked_beads` = `[]`; warning emitted |
| beads (`bd human`) | `decision_requests` = `[]`; warning emitted |
| git | `commits` = `[]`, `rework_signals` (git) = `[]`; warning emitted |
| open-brain | `sessions`, `learnings`, `decisions`, `followups` = `[]`; warning emitted |

A brief with all sources degraded still renders — the Executive Summary
will note "N sources were not fully available" and the content sections
will use empty-day fallback text where applicable.

### Source Availability Warnings Format

Warnings appear in the `warnings` field as plain strings. Common formats:

```
warning/beads: no beads database found under /path/.beads/*.db — beads data skipped
warning/beads: bd human list --json returned non-list JSON: NoneType
warning/open-brain: ob_client not provided — open-brain data unavailable
warning/open-brain: search failed: Client error '401 Unauthorized' for url '...'
warning/git: git log failed — commits data skipped
```

Warnings propagate to the `## Belege` (Evidence) section as bullet entries,
giving the reader visibility into which data was missing.

## Deterministic vs Synthesized Sections

### Deterministic Sections

These sections are rendered directly from raw source data, without any LLM
synthesis or paraphrasing. The content is a factual enumeration.

| Output section | Primary source | Secondary source |
|----------------|---------------|-----------------|
| `## Was sich verändert hat` | `closed_beads` | `commits`, capability signals |
| `## Offene Fäden` | `open_beads`, `blocked_beads` | — |
| `## Entscheidungsbedarf` | `decision_requests`, `decisions` (status=pending), `followups` (Decide:/Need input: prefix) | — |
| `## Drift- und Rework-Signale` | `rework_signals` (revert_commit, supersede_event, reopen_event) | — |
| `## Nächste sinnvolle Schritte` | `ready_beads` (≤2 items) | `followups` (Follow-up: prefix only, ≤1 item) |
| `## Belege` | all sources | warnings, decision_requests |

Deterministic sections are reproducible: running the same query twice for the
same project+date produces identical output (assuming source data is stable).

**Explicit-source contract (v1.1):** `## Entscheidungsbedarf` renders **only** items with an
explicit source signal. It never infers decisions from prose in sessions, commits, or closed beads.
If no explicit signal exists, it renders the empty-state string `Keine offenen Entscheidungen erfasst.`

**Semantic boundary (v1.1):** `## Offene Fäden` and `## Drift- und Rework-Signale` are
semantically distinct. Open Loops lists beads currently in-flight (open/blocked — not yet finished).
Drift & Rework lists work that **regressed** (finished work reversed, scope replaced, or work
reopened after being closed). These sections read from disjoint source fields and must not overlap.

### Synthesized Sections

These sections combine facts from multiple fields using template-driven prose
generation. They are **not** LLM-generated — the prose is assembled from
fixed templates populated with actual counts and IDs from source data.

| Output section | Template inputs | Synthesized element |
|----------------|----------------|---------------------|
| `## Executive Summary` | bead counts, commit counts, session counts, capability signals, warnings | Prose sentence assembly |
| `## Warum es zählt` | `closed_beads` (FEAT type), `capabilities`, `learnings` | Prose sentence assembly |

Synthesized sections may be omitted: `## Warum es zählt` is skipped entirely
if there are no closed feature beads, no capability signals, and no learnings.
This prevents fabricating significance from empty data.

## Range Mode Aggregation

For `--since=Nd` or `--range=START..END`, the brief is a **compressed rollup**:

- **Executive Summary**: one summary spanning the entire date range (aggregated counts)
- **Was sich verändert hat**: grouped by day (`### YYYY-MM-DD` sub-headings)
- **Offene Fäden**: snapshot at the end of the range (not per-day)
- **Entscheidungsbedarf**: snapshot at the end of the range — `decision_requests` is always taken from last day (point-in-time bd human list, not accumulated)
- **Drift- und Rework-Signale**: union of all rework_signals across the range (each revert/supersede/reopen event is time-stamped)
- **Nächste sinnvolle Schritte**: snapshot at the end of the range (not per-day)
- **Belege**: union of all evidence across the range

Per-day briefs are still written to disk (`<project>/.claude/daily-briefs/YYYY-MM-DD.md`)
even in range mode. The rollup output to stdout is separate from the on-disk files.
