#!/usr/bin/env bash
sqlite3 "$HOME/.claude/events.db" "
  SELECT
    project,
    substr(timestamp,1,19)||'Z' as ts,
    event_type,
    coalesce(tool,'-') as tool,
    coalesce(outcome,'-') as outcome
  FROM events
  WHERE date(timestamp) = date('now')
  ORDER BY timestamp DESC LIMIT 50
"
