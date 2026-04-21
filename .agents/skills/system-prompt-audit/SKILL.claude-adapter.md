---
harness: claude
skill: system-prompt-audit
---

# System Prompt Audit — Claude Harness Adapter

This file supplements `SKILL.md` with Claude-specific paths.
A Codex user does NOT need to read this file.

## Script Invocation (Claude)

```bash
bash malte/skills/system-prompt-audit/scripts/fetch-latest.sh
```

## Baseline Directory (Claude)

`malte/system-prompts/baseline/`

Baseline file path: `malte/system-prompts/baseline/anthropic-v{BASELINE_VERSION}.md`

## System Prompts Registry (Claude)

`malte/system-prompts/registry.yml`

Example files that may appear in the registry (not a fixed list — always load the actual registry):
- `malte/system-prompts/golden.md` — main prompt (mode: replace — overrides Anthropic entirely)
- `malte/system-prompts/agents/_core.md`

## Update Baseline (Claude)

```bash
# Copy new prompt to baseline dir
cp "$NEW_PROMPT_FILE" malte/system-prompts/baseline/anthropic-v{LATEST_VERSION}.md
# Remove old baseline
rm malte/system-prompts/baseline/anthropic-v{BASELINE_VERSION}.md
# Remove temp file
rm -f "$NEW_PROMPT_FILE"
```
