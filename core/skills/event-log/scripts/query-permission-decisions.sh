#!/usr/bin/env bash
sqlite3 "$HOME/.claude/events.db" "
  SELECT
    substr(timestamp,1,19)||'Z' as ts,
    json_extract(metadata,'$.decision') as decision,
    json_extract(metadata,'$.rule') as rule,
    tool,
    json_extract(metadata,'$.reason') as reason
  FROM events
  WHERE event_type = 'permission_decision'
  ORDER BY timestamp DESC LIMIT 20
"
