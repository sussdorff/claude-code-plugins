#!/usr/bin/env bash
DB="<agent-state-dir>/events.db"
TAIL=20

# No filters — last N events for current project
# IMPORTANT: $PROJECT must be properly shell-escaped. Never interpolate
# user-supplied values directly into SQL strings. Safe pattern:
#   PROJECT_SAFE=$(echo "$PROJECT" | tr -d "'" | tr -d '"')
# Or better: use Python for queries to avoid shell injection entirely.
sqlite3 "$DB" "
  SELECT
    substr(timestamp, 1, 19) || 'Z' as ts,
    event_type,
    coalesce(agent, '-') as agent,
    coalesce(tool, '-') as tool,
    coalesce(outcome, '-') as outcome
  FROM events
  WHERE project = '$(echo "$PROJECT" | tr -d "'" | tr -d '"')'
  ORDER BY timestamp DESC
  LIMIT $TAIL
" | column -t -s '|'

# With --type filter
# Use PROJECT_SAFE=$(echo "$PROJECT" | tr -d "'" | tr -d '"') before interpolating.
sqlite3 "$DB" "
  SELECT substr(timestamp,1,19)||'Z', event_type, session_id
  FROM events
  WHERE project = '$(echo "$PROJECT" | tr -d "'" | tr -d '"')'  AND event_type = 'session_start'
  ORDER BY timestamp DESC LIMIT $TAIL
"

# With --tool filter
sqlite3 "$DB" "
  SELECT substr(timestamp,1,19)||'Z', event_type, tool, outcome
  FROM events
  WHERE project = '$(echo "$PROJECT" | tr -d "'" | tr -d '"')'  AND tool = 'Read'
  ORDER BY timestamp DESC LIMIT $TAIL
"

# With --session filter
sqlite3 "$DB" "
  SELECT substr(timestamp,1,19)||'Z', event_type, tool, outcome
  FROM events
  WHERE session_id = 'SESS_ID'
  ORDER BY timestamp DESC LIMIT $TAIL
"

# With --bead filter
sqlite3 "$DB" "
  SELECT substr(timestamp,1,19)||'Z', event_type, tool, outcome
  FROM events
  WHERE json_extract(metadata, '$.bead_id') = 'claude-qxs3'
  ORDER BY timestamp DESC LIMIT $TAIL
"

# Cross-project: --project filter (all events today)
sqlite3 "$DB" "
  SELECT project, substr(timestamp,1,19)||'Z', event_type, tool, outcome
  FROM events
  WHERE project = 'my-project'
  ORDER BY timestamp DESC LIMIT $TAIL
"

# All events today across all projects (no --project flag)
sqlite3 "$DB" "
  SELECT project, substr(timestamp,1,19)||'Z', event_type, tool, outcome
  FROM events
  WHERE date(timestamp) = date('now')
  ORDER BY timestamp DESC LIMIT $TAIL
"
