#!/usr/bin/env bash
# Test a Claude Code hook script in multiple ways.
# Usage: ./scripts/test_hooks.sh [hook_path]
# Default hook_path: .claude/hooks/your_hook.py

HOOK=${1:-.claude/hooks/your_hook.py}

# Built-in test mode
uv run "$HOOK" --test

# Manual test
echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | uv run "$HOOK"
echo $?  # 0 = allow, 2 = block

# Automated pytest
python3 -m pytest assets/test_hooks.py -v -k pre_tool_use

# Quick diagnostics
cat .claude/settings.json | jq .
# Quick diagnostics (last 20 log lines)
tail -20 .claude/hooks/logs/pre_tool_use.jsonl 2>/dev/null || echo "No log file found yet"
