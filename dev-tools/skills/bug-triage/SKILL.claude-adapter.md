---
harness: claude
skill: bug-triage
---

# Bug Triage — Claude Harness Adapter

This file supplements `SKILL.md` with Claude-specific tool invocations and paths.
A Codex user does NOT need to read this file.

## Phase 2 Claude Extensions

### Step 1: Query buglog.json (Claude/project-specific)

Load the project's bug history via `malte/hooks/buglog.py`:

```python
import sys
sys.path.insert(0, "malte/hooks")
from buglog import load_buglog, search_buglog

entries = load_buglog(cwd=".")
matches = search_buglog(entries, query="<error message or symptom>")
for m in matches:
    print(m["error_pattern"], "→", m["root_cause"], "→", m["fix"])
```

WHY: buglog.json contains past bug fixes for this project. Identical or similar bugs may have been fixed before — skip re-investigation.

### Step 2: Query events.db (Claude-specific event log)

```bash
sqlite3 ~/.claude/events.db "
  SELECT substr(timestamp,1,19)||'Z', json_extract(metadata,'$.error') as err, tool
  FROM events
  WHERE event_type = 'error'
    AND date(timestamp) >= date('now', '-7 days')
  ORDER BY timestamp DESC LIMIT 20
"
```

WHY: events.db shows what tools were used and when errors occurred. Correlate timestamps with the reported bug.

Use the `/event-log` skill to query this interactively.

### Step 3: Query open-brain (Claude MCP tool)

```
mcp__open-brain__search(query="<error message or symptom>")
```

WHY: open-brain stores cross-project memories and learnings. A similar bug may have been encountered in a different project or session.

If open-brain is unavailable (MCP server down or timeout), skip this step gracefully.

## References (Claude-specific)

- buglog hook: `malte/hooks/buglog.py` — `search_buglog()`, `load_buglog()`, `write_backlink()`
- Event log skill: `/event-log` — query `~/.claude/events.db`
- open-brain: `mcp__open-brain__search` — cross-project memory search
