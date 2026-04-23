# Troubleshooting Claude Code Hooks

This document provides solutions to common issues when working with Claude Code hooks.

## Hook Not Running

### Check JSON Syntax

Invalid JSON syntax in settings.json will prevent hooks from loading.

```bash
# Validate settings.json
cat .claude/settings.json | jq .

# If you get errors, fix the JSON formatting
```

**Common JSON errors:**
- Missing commas between array elements
- Trailing commas before closing brackets
- Unescaped quotes in command strings
- Mismatched brackets or braces

### Verify Matcher Pattern

Hooks only run when the matcher pattern matches the tool being used.

**Debugging matchers:**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",  // Matches Edit OR Write tools
        "hooks": [...]
      }
    ]
  }
}
```

**Common matcher issues:**
- Case sensitivity: `edit` won't match `Edit`
- File patterns: `Edit:*.ts` only matches TypeScript files
- Empty matcher `""` matches all tools (use this for debugging)

**Test with a broad matcher:**

```json
{
  "matcher": "",  // Matches everything
  "hooks": [...]
}
```

If the hook runs with `""` but not your specific matcher, the pattern is the issue.

### Verify Script Permissions

Python scripts must be executable on Unix-like systems.

```bash
# Make script executable
chmod +x .claude/hooks/pre_tool_use.py

# Verify permissions
ls -la .claude/hooks/
# Should show: -rwxr-xr-x (executable)
```

### Check Hook Logs

Hooks may be running but failing silently. Check the logs:

```bash
# List all log files
ls -la .claude/hooks/logs/

# View PreToolUse logs
cat .claude/hooks/logs/pre_tool_use.jsonl

# View recent logs
tail -n 20 .claude/hooks/logs/pre_tool_use.jsonl

# Watch logs in real-time
tail -f .claude/hooks/logs/pre_tool_use.jsonl
```

### Verify Settings File Location

Hooks can be configured at user or project scope.

**User scope** (applies to all projects):
```bash
cat ~/.claude/settings.json
```

**Project scope** (applies to current project only):
```bash
cat .claude/settings.json
```

Ensure the hook is configured in the correct settings file.

### Check UV Installation

If using UV script headers, ensure UV is installed:

```bash
# Check UV is installed
uv --version

# If not installed
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Hook Blocking Incorrectly

### Understand Exit Codes

Exit codes determine hook behavior:

| Exit Code | Behavior | Use Case |
|-----------|----------|----------|
| 0 | Allow operation, stdout shown | Normal success |
| 2 | Block operation, stderr to Claude | Security block, quality gate |
| Other | Non-blocking error, shown to user | Hook error |

### Test Hooks Manually

Test hooks with sample inputs to verify behavior:

```bash
# Test PreToolUse hook
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | \
  uv run .claude/hooks/pre_tool_use.py
echo $?  # Check exit code (should be 2 for dangerous command)

# Test with safe command
echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | \
  uv run .claude/hooks/pre_tool_use.py
echo $?  # Check exit code (should be 0)
```

### Add Debug Logging

Add temporary debug logging to understand what the hook is seeing:

```python
import json

# In your hook script
def main():
    input_data = json.loads(sys.stdin.read())

    # Debug: Log everything the hook receives
    with open(".claude/hooks/logs/debug.log", "a") as f:
        f.write(f"Input: {json.dumps(input_data, indent=2)}\n")
        f.write(f"Tool: {input_data.get('tool_name')}\n")
        f.write(f"Params: {input_data.get('tool_input')}\n\n")

    # ... rest of hook logic
```

Then check the debug log:

```bash
tail -f .claude/hooks/logs/debug.log
```

### Check Validation Logic

Review the validation logic for bugs:

```python
# Common bug: String comparison issues
if command == "rm -rf /":  # ❌ Only matches exact string
    return False

if "rm -rf" in command:  # ✓ Better, but can be bypassed
    return False

import re
if re.search(r'rm\s+-[rf]{2}', command):  # ✓ Best
    return False
```

### Review Output Streams

Ensure output goes to the correct stream:

```python
# Blocking messages go to stderr
print("BLOCKED: Dangerous operation", file=sys.stderr)
sys.exit(2)

# Informational messages go to stdout
print("Hook executed successfully")
sys.exit(0)
```

## Hook Not Blocking When Expected

### Verify Hook Type

Only certain hook types can block operations:

| Hook Type | Can Block? | Exit Code 2 Effect |
|-----------|------------|-------------------|
| PreToolUse | ✓ Yes | Prevents tool execution |
| Stop | ✓ Yes | Forces Claude to continue |
| UserPromptSubmit | ✓ Yes | Rejects user prompt |
| SubagentStop | ✓ Yes | Prevents subagent completion |
| PostToolUse | ✗ No | Tool already executed |
| SessionStart | ✗ No | Session already started |
| Notification | ✗ No | Informational only |
| PreCompact | ✗ No | Informational only |

If you're using PostToolUse to block operations, switch to PreToolUse.

### Check Exit Code

Verify the hook is exiting with code 2:

```python
# ❌ Wrong: Exit 1 doesn't block
if is_dangerous:
    print("Error", file=sys.stderr)
    sys.exit(1)  # Non-blocking error

# ✓ Correct: Exit 2 blocks
if is_dangerous:
    print("BLOCKED", file=sys.stderr)
    sys.exit(2)  # Blocks operation
```

### Verify Error Handling

Ensure exceptions don't bypass blocking logic:

```python
# ❌ Wrong: Exception causes hook to allow
try:
    if is_dangerous(command):
        sys.exit(2)
except:
    pass  # Silently allows dangerous operation

# ✓ Correct: Fail secure
try:
    if is_dangerous(command):
        sys.exit(2)
except Exception as e:
    print(f"Validation error: {e}", file=sys.stderr)
    sys.exit(2)  # Block on error (fail secure)
```

## Performance Issues

### Symptoms

- Claude Code feels slow or laggy
- Long delays before tool execution
- Timeouts or errors

### Optimize Hook Execution

**Use specific matchers:**

```json
{
  "matcher": "Edit:*.py|Write:*.py",  // ✓ Only Python files
  "hooks": [...]
}
```

Instead of:

```json
{
  "matcher": "Edit|Write",  // ❌ Runs on ALL files
  "hooks": [...]
}
```

**Cache expensive operations:**

```python
import functools

@functools.lru_cache(maxsize=128)
def load_config():
    """Load config once and cache"""
    with open("config.json") as f:
        return json.load(f)
```

**Set shorter timeouts:**

```python
result = subprocess.run(
    command,
    timeout=5  # ✓ Fast timeout
)
```

Instead of:

```python
result = subprocess.run(
    command,
    timeout=60  # ❌ Too long for hook
)
```

### Profile Hook Execution

Add timing to identify slow operations:

```python
import time

def main():
    start = time.time()

    # ... hook logic ...

    duration = time.time() - start
    if duration > 1.0:
        print(f"Warning: Hook took {duration:.2f}s", file=sys.stderr)
```

### Run Non-Critical Operations Asynchronously

For PostToolUse hooks, consider background execution:

```python
import subprocess

# Run formatter in background (don't wait for result)
subprocess.Popen(
    ["black", file_path],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
```

## Settings Not Taking Effect

### Restart Claude Code

Settings changes require restarting Claude Code:

```bash
# Exit and restart claude command
```

### Check File Location

Ensure settings.json is in the correct location:

```bash
# Project-specific hooks
ls -la .claude/settings.json

# User-level hooks
ls -la ~/.claude/settings.json
```

### Validate Settings Format

Use the hook manager to verify installation:

```bash
# List all configured hooks
uv run scripts/hook_manager.py list

# Should show your installed hooks
```

## Import Errors in Hook Scripts

### UV Script Dependencies

If the hook script imports packages, add them to the UV header:

```python
#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "requests",
#   "pyyaml>=6.0",
# ]
# ///

import requests  # Now available
import yaml      # Now available
```

### Path Issues

Ensure imports work from the hook's execution context:

```python
import sys
import os

# Add project root to path if needed
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Now can import project modules
from my_project import utils
```

## JSON Parsing Errors

### Invalid JSON Input

Hooks receive JSON on stdin. Handle parsing errors gracefully:

```python
try:
    input_data = json.loads(sys.stdin.read())
except json.JSONDecodeError as e:
    # Don't block on JSON errors (could be hook misconfiguration)
    print(f"Warning: Invalid JSON input: {e}", file=sys.stderr)
    sys.exit(0)  # Allow operation
```

### Missing Fields

Check for required fields safely:

```python
# ❌ Wrong: Crashes on missing field
command = input_data["tool_input"]["command"]

# ✓ Correct: Safe access with defaults
tool_input = input_data.get("tool_input", {})
command = tool_input.get("command", "")
```

## Hooks Running Multiple Times

### Check for Duplicate Configurations

List all hooks to find duplicates:

```bash
uv run scripts/hook_manager.py list
```

Remove duplicates from both user and project settings files.

### Multiple Matcher Entries

Ensure only one matcher entry for your pattern:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {"type": "command", "command": "prettier ..."}
        ]
      },
      // ❌ Duplicate matcher!
      {
        "matcher": "Edit|Write",
        "hooks": [
          {"type": "command", "command": "prettier ..."}
        ]
      }
    ]
  }
}
```

## Getting Help

### Enable Verbose Logging

Increase logging verbosity in your hooks:

```python
import logging

logging.basicConfig(
    filename=".claude/hooks/logs/verbose.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
logger.debug("Hook started")
logger.debug(f"Input: {input_data}")
```

### Test with Template Scripts

Use the provided templates' `--test` mode:

```bash
# Test PreToolUse template
uv run .claude/hooks/pre_tool_use.py --test

# Test PostToolUse template
uv run .claude/hooks/post_tool_use.py --test

# Test SessionStart template
uv run .claude/hooks/session_start.py --test

# Test Stop template
uv run .claude/hooks/stop.py --test
```

### Community Resources

- **Official Documentation**: https://docs.claude.com/en/docs/claude-code/hooks
- **Hook Guide**: https://docs.claude.com/en/docs/claude-code/hooks-guide
- **Community Examples**: https://github.com/disler/claude-code-hooks-mastery
- **GitHub Issues**: Report bugs at https://github.com/anthropics/claude-code/issues

## Common Error Messages

### "Hook timed out"

**Cause:** Hook execution exceeded timeout limit (default 60s).

**Solution:**
- Optimize hook to run faster (< 1 second ideal)
- Reduce operations performed
- Use specific matchers to reduce invocations

### "Permission denied"

**Cause:** Script not executable or file permissions issue.

**Solution:**
```bash
chmod +x .claude/hooks/your_hook.py
```

### "Command not found"

**Cause:** Hook tries to execute a command that doesn't exist.

**Solution:**
- Install missing command (e.g., `npm install -g prettier`)
- Check PATH environment variable
- Use full path to command in hook

### "No such file or directory"

**Cause:** Hook references file that doesn't exist.

**Solution:**
- Verify file paths are absolute or relative to project root
- Create necessary directories: `mkdir -p .claude/hooks/logs`
- Check for typos in file paths

## Debugging Checklist

When troubleshooting hooks, work through this checklist:

- [ ] Validate settings.json syntax with `jq`
- [ ] Check hook is in correct settings file (user vs project)
- [ ] Verify script has executable permissions
- [ ] Test hook manually with sample input
- [ ] Check hook logs for errors
- [ ] Verify matcher pattern matches tool name
- [ ] Confirm exit code is correct (0 or 2)
- [ ] Add debug logging to understand hook behavior
- [ ] Test with `--test` flag if available
- [ ] Restart Claude Code after settings changes
- [ ] Check UV is installed if using UV scripts
- [ ] Review error messages in stderr
