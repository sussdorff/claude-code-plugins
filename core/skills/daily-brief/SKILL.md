---
name: daily-brief
description: >
  Generate and manage daily project briefs. Loads project config from
  ~/.claude/daily-brief.yml and persists per-project briefs to
  <project>/.claude/daily-briefs/YYYY-MM-DD.md. Use for daily summaries
  of git activity, bead progress, and open-brain entries across tracked projects.
---

# daily-brief

Generate a daily brief for one or all tracked projects, covering git commits,
bead activity, and memory entries for a given date range.

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

## CLI Usage

```bash
# Load (or bootstrap) config
python3 core/skills/daily-brief/scripts/config.py load

# Resolve a project
python3 core/skills/daily-brief/scripts/config.py resolve mira

# Get brief path
python3 core/skills/daily-brief/scripts/config.py brief-path mira 2026-04-24

# Check brief existence
python3 core/skills/daily-brief/scripts/config.py brief-exists mira 2026-04-24

# Get briefs directory
python3 core/skills/daily-brief/scripts/config.py briefs-dir mira
```
