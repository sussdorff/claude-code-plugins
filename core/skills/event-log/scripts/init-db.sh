#!/usr/bin/env bash
DB="<agent-state-dir>/events.db"

if [[ ! -f "$DB" ]]; then
  echo "No event log found at $DB."
  echo "Events are recorded when hooks are active and CLAUDE_EVENTS_DB is set (or defaults to the harness events DB)."
  exit 0
fi

# Derive current project name from git remote or cwd basename
PROJECT=$(git remote get-url origin 2>/dev/null | sed 's|.*[:/]||; s|\.git$||')
if [[ -z "$PROJECT" ]]; then
  PROJECT=$(basename "$PWD")
fi
