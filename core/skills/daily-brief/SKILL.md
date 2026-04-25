---
name: daily-brief
description: >
  Generate and manage daily project briefs. Loads project config from
  ~/.claude/daily-brief.yml and persists per-project briefs to
  <project>/.claude/daily-briefs/YYYY-MM-DD.md. Use for daily summaries
  of git activity, bead progress, and open-brain entries across tracked projects.
triggers:
  - daily brief
  - daily briefing
  - tagesbericht
  - was hatte ich gestern gemacht
  - daily-brief
  - brief generieren
  - /daily-brief
---

# daily-brief

Generate a daily brief for one or all tracked projects, covering git commits,
bead activity, and memory entries for a given date range.

## Quick Start

All CLI forms delegate to `scripts/orchestrate-brief.py`:

```bash
python3 scripts/orchestrate-brief.py
```

See the **Orchestration** section below for all supported CLI args.

## Config

Config lives at `~/.claude/daily-brief.yml`. Bootstrap it with:

```bash
python3 core/skills/daily-brief/scripts/config.py load
```

This creates the file with four default projects (claude-code-plugins, mira, polaris,
open-brain) if it does not already exist.

## Config Schema

```yaml
projects:
  - name: claude-code-plugins
    path: /Users/malte/code/claude-code-plugins
    slug: claude-code-plugins
    beads: true
    docs_dir: docs

defaults:
  since: yesterday          # yesterday | today | Nd | YYYY-MM-DD
  format: markdown
  detailed: false
  language: de              # de | en
  timezone: Europe/Berlin
```

## Storage Layout

Briefs are persisted flat under `<project>/.claude/daily-briefs/`:

```
<project>/.claude/daily-briefs/
  2026-04-24.md
  2026-04-23.md
  ...
```

## Orchestration (scripts/orchestrate-brief.py)

The `orchestrate-brief.py` script is the main entry point. It handles all CLI
args, backfill logic, and open-brain persistence.

**Orchestration flow:**
1. Parse CLI args
2. Load config, resolve project(s)
3. For each (project, date): check `brief_exists` → if missing, call `render-brief.py`
4. Persist each new brief to open-brain (idempotent via `session_ref`)
5. Emit aggregated markdown

**Backfill rule:** Re-running the same args is a no-op. Already-persisted briefs are
never re-queried. Force-regenerate is not supported in v1.

**Open-brain persistence:** Each new brief is saved as `type=daily_brief`,
`project=<slug>`, `session_ref=daily-brief-YYYY-MM-DD`. Non-blocking — failure
never aborts the brief output.

**CLI args:**

| Invocation | Behaviour |
|------------|-----------|
| `python3 scripts/orchestrate-brief.py` | All config projects, since=yesterday |
| `python3 scripts/orchestrate-brief.py <name>` | Single project, since=yesterday |
| `python3 scripts/orchestrate-brief.py --since=Nd` | Last N days (2d, 7d, etc.) |
| `python3 scripts/orchestrate-brief.py --date=YYYY-MM-DD` | Specific date |
| `python3 scripts/orchestrate-brief.py --range=YYYY-MM-DD..YYYY-MM-DD` | Date range |
| `python3 scripts/orchestrate-brief.py --detailed` | Raise word cap ~150→~300/project |

**Range rollup:** For `--since` or `--range`, emits ONE aggregated markdown per
project: single Executive Summary across the range, What Changed grouped by day,
Open Loops/Next Best Moves/Evidence aggregated.

## Python Helpers (scripts/config.py)

The `config.py` module provides:

| Function | Returns | Description |
|----------|---------|-------------|
| `load_config()` | envelope | Load (or bootstrap) config |
| `resolve_project(name_or_none)` | envelope | Resolve one or all projects |
| `brief_path(project, date)` | `Path` | Path for a brief file |
| `brief_exists(project, date)` | `bool` | Whether brief exists on disk |
| `briefs_dir(project)` | `Path` | Per-project briefs directory |

Multi-field functions emit
[`core/contracts/execution-result.schema.json`](../../contracts/execution-result.schema.json)
envelopes. Single atomic values (`Path`, `bool`) are returned bare.

## Data Collection (scripts/query-sources.py)

The `query-sources.py` script aggregates raw data from three sources for a given
project and date:

```bash
python3 scripts/query-sources.py --project claude-code-plugins --date 2026-04-23
```

Output is a single JSON blob conforming to `core/contracts/execution-result.schema.json`
with these `data` fields:

| Field | Source | Description |
|-------|--------|-------------|
| `sessions` | open-brain | session_summary + debrief entries |
| `closed_beads` | beads (bd) | Beads closed in the date window, commits merged in |
| `open_beads` | beads (bd) | Current open bead snapshot |
| `ready_beads` | beads (bd) | Unblocked/ready bead snapshot |
| `blocked_beads` | beads (bd) | Currently blocked beads |
| `commits` | git | Standalone commits not linked to a bead |
| `learnings` | open-brain | type=learning entries |
| `decisions` | open-brain | type=decision entries |
| `decision_requests` | beads (bd) | Beads flagged for human decision |
| `followups` | open-brain | Lines with Decide: / Need input: / Follow-up: prefixes |
| `rework_signals` | git + beads | Revert commits + supersede events |
| `warnings` | — | Source unavailability notices (partial data) |

Status is `ok` when all sources are available, `warning` when any source is degraded.

**CLI options:**
- `--project NAME` — project name from daily-brief.yml
- `--date YYYY-MM-DD` — date to query (Europe/Berlin midnight-to-midnight)
- `--config PATH` — optional config file path override

## Capability Extraction (scripts/capability-extractor.py)

The `capability-extractor.py` script parses closed bead titles/descriptions and session
summaries for capability signals, producing short present-tense capability sentences
grounded in source data.

**Capability signals detected:**
- Bead titles/descriptions containing: `now`, `new gate`, `now verified`, `now possible`,
  `unblocks`, `[FEAT]`, `[QG]` (case-insensitive)
- Both `feature` AND `task` beads qualify
- Session summary lines starting with `New:`, `Fixed:`, or `Internal:`
- For polaris: files created on target date in `docs/` and `docs/adr/`

**CLI options:**
- `--stdin` — read query-sources.py JSON envelope from stdin
- `--project NAME --date YYYY-MM-DD` — run query-sources internally
- `--scan-docs` — enable polaris docs/ scanning
- `--config PATH` — optional config file override

**Output:** execution-result envelope with `data.capabilities[]` list of sentences.

**Usage:**

```bash
python3 scripts/capability-extractor.py --project claude-code-plugins --date 2026-04-23
```

## Rendering (scripts/render-brief.py)

The `render-brief.py` script renders a v1.0 Chief-of-Staff markdown report in Voice B
(journalistic narrator, past tense, third-person observational, German).

**v1.0 sections rendered:**

| Section | German heading | Content type |
|---------|---------------|--------------|
| Executive Summary | `## Executive Summary` | Synthesized prose (German, ~150 words) |
| What Changed | `## Was sich verändert hat` | Deterministic from closed_beads + commits |
| Why It Matters | `## Warum es zählt` | Synthesized prose, only from cited facts |
| Open Loops | `## Offene Fäden` | Deterministic from open_beads + blocked_beads |
| Next Best Moves | `## Nächste sinnvolle Schritte` | Max 3 items: ≤2 from ready_beads, ≤1 from followups |
| Evidence | `## Belege` | Bullet list: beads/commits/sessions/decisions/warnings |

**Voice B rules:** German, past tense, third-person observational. No first-person pronouns.
Prose paragraphs, not bullet lists (except Evidence). Empty day: `Ruhiger Tag — keine Aktivität verzeichnet.`

**CLI options:**
- `--project NAME` — project name from daily-brief.yml (required)
- `--date YYYY-MM-DD` — single day mode
- `--since YYYY-MM-DD [--until YYYY-MM-DD]` — range mode
- `--range START END` — explicit date range
- `--detailed` — raises word cap to ~300 words/project; full per-day sections in range
- `--no-persist` — skip writing brief to `<project>/.claude/daily-briefs/YYYY-MM-DD.md`
- `--config PATH` — optional config file override

**Single day:**

```bash
python3 scripts/render-brief.py --project claude-code-plugins --date 2026-04-23
```

## Config CLI Usage

```bash
python3 core/skills/daily-brief/scripts/config.py load
python3 core/skills/daily-brief/scripts/config.py resolve mira
python3 core/skills/daily-brief/scripts/config.py brief-exists mira 2026-04-24
```

## Reference Docs

- [`references/data-sources.md`](references/data-sources.md) — canonical field→source map, dedup rules, fallback behavior, deterministic vs synthesized sections
- [`references/config-schema.md`](references/config-schema.md) — full YAML config schema with annotated fields and examples

## Sample Output

- [`docs/examples/daily-brief-sample.md`](../../../../docs/examples/daily-brief-sample.md) — live sample from `--since=7d` on claude-code-plugins, with v1.0 Product Contract review
