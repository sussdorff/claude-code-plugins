# daily-brief: Config Schema Reference

Full YAML config schema for `~/.claude/daily-brief.yml` with field annotations,
types, defaults, and examples.

## Schema Overview

```yaml
projects:       # list[ProjectConfig]  required
  - name:       # str  required  — display name + lookup key
    path:       # str  required  — absolute path to project root
    slug:       # str  optional  — URL-safe short name; defaults to name
    beads:      # bool optional  — whether project uses beads (bd); default true
    docs_dir:   # str  optional  — docs subdirectory path; default "docs"

defaults:       # Defaults  optional
  since:        # str  optional  — default lookback; default "yesterday"
  format:       # str  optional  — output format; default "markdown"
  detailed:     # bool optional  — default detailed mode; default false
  language:     # str  optional  — output language; default "de"
  timezone:     # str  optional  — IANA timezone; default "Europe/Berlin"
```

## Field Reference

### `projects[]` (list, required)

A list of one or more project entries. Each entry describes a tracked project.

#### `projects[].name` (str, required)

Display name and lookup key. Used in CLI invocations (`python3 scripts/orchestrate-brief.py <name>`)
and in brief headings.

**Example:** `claude-code-plugins`

#### `projects[].path` (str, required)

Absolute filesystem path to the project root directory. Brief files are written
to `<path>/.claude/daily-briefs/YYYY-MM-DD.md`.

**Example:** `/Users/malte/code/claude-code-plugins`

#### `projects[].slug` (str, optional)

URL-safe short identifier used for open-brain memory `session_ref` and `project`
fields. If omitted, defaults to `name`.

**Example:** `claude-code-plugins` *(same as name in most cases)*

#### `projects[].beads` (bool, optional, default: `true`)

Whether the project uses beads (`bd`) for issue tracking. When `false`, all
bead-sourced fields (`closed_beads`, `open_beads`, `ready_beads`, `blocked_beads`,
`decision_requests`) are skipped without emitting a warning.

**Example:** `false` *(for polaris, which does not use beads)*

#### `projects[].docs_dir` (str, optional, default: `"docs"`)

Path to the docs subdirectory relative to `path`. Used by capability-extractor
when `--scan-docs` is enabled (polaris pattern: scan for new ADR files).

**Example:** `docs`

### `defaults` (object, optional)

Global defaults applied when the corresponding CLI flag is not specified.
All fields are optional.

#### `defaults.since` (str, optional, default: `"yesterday"`)

Default lookback period. Accepted values:
- `"yesterday"` — process yesterday only
- `"today"` — process today
- `"Nd"` — last N days (e.g. `"3d"`, `"7d"`)
- `"YYYY-MM-DD"` — specific date

**Note:** This field is currently informational — `orchestrate-brief.py` uses
yesterday as the default when no `--since`/`--date`/`--range` flag is given.

#### `defaults.format` (str, optional, default: `"markdown"`)

Output format. Currently only `"markdown"` is supported.

#### `defaults.detailed` (bool, optional, default: `false`)

When `true`, brief word cap is raised from ~150 to ~300 words per project
and per-day sections in range mode are expanded.

#### `defaults.language` (str, optional, default: `"de"`)

Output language code. Currently only German (`"de"`) is supported by the
v1.0 renderer (Voice B: journalistic narrator, past tense, third-person).

#### `defaults.timezone` (str, optional, default: `"Europe/Berlin"`)

IANA timezone string. Used for midnight-to-midnight date windowing in
`query-sources.py`. Commits and bead closures are attributed to a date
in this timezone.

## Complete Example

This is the live config for the 4 tracked projects:

```yaml
projects:
  - name: claude-code-plugins
    path: /Users/malte/code/claude-code-plugins
    slug: claude-code-plugins
    beads: true
    docs_dir: docs

  - name: mira
    path: /Users/malte/code/mira
    slug: mira
    beads: true
    docs_dir: docs

  - name: polaris
    path: /Users/malte/code/polaris
    slug: polaris
    beads: false        # polaris does not use beads
    docs_dir: docs

  - name: open-brain
    path: /Users/malte/code/open-brain
    slug: open-brain
    beads: true
    docs_dir: docs

defaults:
  since: yesterday
  format: markdown
  detailed: false
  language: de
  timezone: Europe/Berlin
```

## Minimal Single-Project Example

```yaml
projects:
  - name: my-project
    path: /Users/me/code/my-project

defaults:
  since: yesterday
```

All optional fields use their defaults: `slug=my-project`, `beads=true`,
`docs_dir=docs`, `format=markdown`, `detailed=false`, `language=de`,
`timezone=Europe/Berlin`.

## Storage Layout

Each project's briefs are stored flat under `<path>/.claude/daily-briefs/`:

```
<path>/.claude/daily-briefs/
  2026-04-24.md
  2026-04-23.md
  2026-04-22.md
  ...
```

Brief files are created by `render-brief.py` during first generation.
They are never overwritten — `brief_exists()` in `config.py` acts as
a backfill guard: if the file exists, generation is skipped.

## Bootstrapping

Run `python3 core/skills/daily-brief/scripts/config.py load` to create
`~/.claude/daily-brief.yml` with the default 4-project config if it does
not already exist.
