---
harness: claude
skill: project-health
---

# Project Health — Claude Harness Adapter

This file supplements `SKILL.md` with Claude-specific paths and conventions.
A Codex user does NOT need to read this file.

## Conventions File Check (Claude)

The "project conventions file" referred to in §4 is `CLAUDE.md` in the project root.

Check: file exists, contains an Overview/project description, and contains a Commands section with at least one command.

## Harness Check (Claude)

The harness skills directory to detect is `malte/skills/` or `.claude/agents/`. If either exists, this is a harness repository.

The entropy-scan script path is:

```bash
if [[ -d malte/skills ]] || [[ -d .claude/agents ]]; then
  if [ -f malte/skills/entropy-scan/scripts/entropy-scan.sh ]; then
    entropy_output=$(bash malte/skills/entropy-scan/scripts/entropy-scan.sh 2>&1)
    entropy_exit=$?
    if [[ $entropy_exit -eq 2 ]]; then
      violation_count="error"
    else
      violation_count=$(echo "$entropy_output" | grep -c "VIOLATION \[" 2>/dev/null || echo 0)
    fi
  else
    violation_count=0
  fi
fi
```
