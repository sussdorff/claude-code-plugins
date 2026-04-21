---
harness: claude
skill: entropy-scan
---

# Entropy Scan — Claude Harness Adapter

This file supplements `SKILL.md` with Claude-specific paths.
A Codex user does NOT need to read this file.

## Script Invocation (Claude)

In Claude Code projects, the entropy-scan script lives at:

```bash
bash malte/skills/entropy-scan/scripts/entropy-scan.sh
# optional: scan a specific directory
bash malte/skills/entropy-scan/scripts/entropy-scan.sh --dir /path/to/project
```

## Test Suite (Claude)

```bash
bash malte/skills/entropy-scan/tests/test_entropy_scan.sh
```

## Integration with project-health (Claude)

In Claude Code, the harness check in `/project-health` calls:

```bash
if [ -f malte/skills/entropy-scan/scripts/entropy-scan.sh ]; then
  bash malte/skills/entropy-scan/scripts/entropy-scan.sh 2>&1
fi
```
