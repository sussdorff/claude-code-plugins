#!/usr/bin/env bash
DB="${CLAUDE_EVENTS_DB:-$HOME/.claude/events.db}"
TAIL=20
PROJECT="${PROJECT:-$(git remote get-url origin 2>/dev/null | sed 's|.*[:/]||; s|\.git$||')}"
# Sanitize PROJECT once to avoid repeating the tr-pipeline inline in SQL.
# IMPORTANT: Never interpolate user-supplied values directly into SQL strings.
# Or better: use Python for queries to avoid shell injection entirely.
PROJECT_SAFE=$(echo "$PROJECT" | tr -d "'" | tr -d '"')

# No filters — last N events for current project
sqlite3 "$DB" "
  SELECT
    substr(timestamp, 1, 19) || 'Z' as ts,
    event_type,
    coalesce(agent, '-') as agent,
    coalesce(tool, '-') as tool,
    coalesce(outcome, '-') as outcome
  FROM events
  WHERE project = '$PROJECT_SAFE'
  ORDER BY timestamp DESC
  LIMIT $TAIL
" | column -t -s '|'

# With --type filter
sqlite3 "$DB" "
  SELECT substr(timestamp,1,19)||'Z', event_type, session_id
  FROM events
  WHERE project = '$PROJECT_SAFE'  AND event_type = 'session_start'
  ORDER BY timestamp DESC LIMIT $TAIL
"

# With --tool filter
sqlite3 "$DB" "
  SELECT substr(timestamp,1,19)||'Z', event_type, tool, outcome
  FROM events
  WHERE project = '$PROJECT_SAFE'  AND tool = 'Read'
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
