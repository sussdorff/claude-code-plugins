---
name: event-log
description: Query the structured event log for any project. Shows tool use history, session starts, permission decisions, and errors from the centralized harness events database. Use when investigating session activity, debugging tool usage patterns, reviewing what happened in a session, or querying across projects.
requires_standards: [english-only]
---

# Event Log Query

Query the centralized event log in the active harness state directory.

## Usage

```
event-log                        # Show last 20 events for current project
event-log --tail=N               # Show last N events (default 20)
event-log --type=<event_type>    # Filter by event_type (session_start, tool_use, permission_decision, error)
event-log --tool=<tool_name>     # Filter by tool name (Read, Write, Bash, etc.)
event-log --session=<session_id> # Filter by session ID
event-log --bead=<bead_id>       # Filter by bead ID (e.g. claude-qxs3)
event-log --project=<name>       # Filter by project name (cross-project queries)
```

## Process

### Step 1: Determine DB path and current project

See [`scripts/init-db.sh`](scripts/init-db.sh) for the DB existence check and project name derivation logic.

### Step 2: Parse arguments

Parse the user's arguments to determine filters:
- `--tail=N` → result limit (default 20)
- `--type=<value>` → filter `event_type = '<value>'`
- `--tool=<value>` → filter `tool = '<value>'`
- `--session=<value>` → filter `session_id = '<value>'`
- `--bead=<value>` → filter `json_extract(metadata, '$.bead_id') = '<value>'`
- `--project=<value>` → filter `project = '<value>'` (overrides current project)

### Step 3: Build and run sqlite3 query

> **SQL injection note**: All user-supplied filter values — from `--project`,
> `--type`, `--tool`, `--session`, and `--bead` arguments — must be sanitized
> before interpolation into SQL strings. Use the following pattern for every
> shell variable that originates from user input:
>
> ```bash
> VALUE_SAFE=$(echo "$VALUE" | tr -d "'" | tr -d '"')
> ```
>
> Then interpolate `$VALUE_SAFE` in the SQL string, not `$VALUE`. Do not apply
> this to literal example values in comments or hardcoded constants.

Use the `sqlite3` CLI to query the database. See [`scripts/query-events.sh`](scripts/query-events.sh) for complete query templates for each filter combination (no filter, `--type`, `--tool`, `--session`, `--bead`, cross-project).

### Step 4: Format output

Display the results in a human-readable table:

```
Event Log: <agent-state-dir>/events.db | project=my-project (last 20 events)

TIMESTAMP            TYPE                 AGENT      TOOL             OUTCOME
2026-04-05T14:23:01Z session_start        main       -                -
2026-04-05T14:23:02Z tool_use             main       Read             success
2026-04-05T14:23:04Z tool_use             main       Bash             success
2026-04-05T14:23:10Z permission_decision  main       Bash             deny
```

If no events match the filter, say: "No events found matching filter."
If DB doesn't exist, say: "No event log found in the harness events DB location. Events are recorded when hooks are active."

## Examples

### Last 5 events for current project
```
event-log --tail=5
```

### All Bash tool calls this session
```
event-log --tool=Bash
```

### Session start events only
```
event-log --type=session_start
```

### All permission decisions (security audit)
```
event-log --type=permission_decision
```

Query: See [`scripts/query-permission-decisions.sh`](scripts/query-permission-decisions.sh)

### Denied operations only

See [`scripts/query-denied-operations.sh`](scripts/query-denied-operations.sh)

### Specific session
```
event-log --session=abc12345
```

### All events for a specific bead
```
event-log --bead=claude-qxs3
```

### Cross-project: all events today
```
event-log --project=all
```

Query: See [`scripts/query-cross-project.sh`](scripts/query-cross-project.sh)

### Cross-project: specific project
```
event-log --project=my-repo
```

## Event Schema Reference

SQLite table `events` in the centralized harness events DB:

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Auto-increment primary key |
| `timestamp` | TEXT | ISO 8601 UTC |
| `session_id` | TEXT | Claude Code session ID |
| `project` | TEXT | Project name (git remote repo or cwd basename) |
| `event_type` | TEXT | `session_start`, `tool_use`, `permission_decision`, or `error` |
| `agent` | TEXT | `main`, `subagent`, or custom |
| `tool` | TEXT\|null | Tool name for `tool_use` and `permission_decision` events; null otherwise |
| `outcome` | TEXT\|null | `success`, `error`, `allow`, `deny`, or null |
| `tokens` | INTEGER\|null | Reserved for future token tracking |
| `duration_ms` | REAL\|null | Hook execution duration |
| `metadata` | JSON | Additional context (cwd, agent_id, tool_input, bead_id, worktree, cmux_surface_id, pane_name) |

### `permission_decision` metadata fields

The `metadata` JSON column contains these additional fields for permission events:

| Field | Type | Description |
|-------|------|-------------|
| `decision` | string | `allow` or `deny` (current); `ask` is reserved for future interactive-confirmation hooks |
| `rule` | string | Rule that triggered the decision (see below) |
| `reason` | string | Human-readable explanation of the decision |
| `operation` | string\|null | The command or operation that was evaluated |

Note: `outcome` column == `decision` value for permission events (alias for filtering compatibility).

**Rule names:**

| Rule | Decision | Description |
|------|----------|-------------|
| `block_dangerous_rm` | deny | Dangerous `rm -rf` command detected |
| `block_bd_init_existing_project` | deny | `bd init` / `dolt init` on existing project |
| `block_git_push_with_secrets` | deny | `git push` blocked by gitleaks secret scan |
| `pass_through_git_push_no_secrets` | allow | `git push` passed gitleaks scan |
| `pass_through` | allow | No rule matched, operation allowed |

## Implementation Notes

- The event log is centralized in one harness events DB — single DB for all projects
- Events are written without requiring a `.beads/` directory in the project
- WAL mode is enabled for concurrent write safety
- Override DB path for testing: `CLAUDE_EVENTS_DB=/tmp/test.db`
- The hook `malte/hooks/event-log.py` handles both `SessionStart` and `PostToolUse`
- The hook `default/hooks/pre_tool_use.py` handles `permission_decision` events
- Shared write module: `malte/hooks/events_db.py`
- Migration script: `scripts/migrate_events_to_sqlite.py`
