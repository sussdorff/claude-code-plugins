# Claude Code Hook Examples

This document contains complete, working examples of hooks for various use cases. All examples are based on proven patterns from the Claude Code community.

## Quick Reference

| Use Case | Hook Type | Complexity | Security Impact |
|----------|-----------|------------|-----------------|
| Auto-format code | PostToolUse | Simple | Low |
| Block dangerous commands | PreToolUse | Medium | High |
| Load git context | SessionStart | Medium | Low |
| Desktop notifications | Notification | Simple | Low |
| Ensure tests pass | Stop | Medium | Medium |
| Backup transcripts | PreCompact | Simple | Low |
| Type checking | PostToolUse | Simple | Low |

## Example 1: Auto-Format Code After Edits

**Use case**: Automatically format code files after Claude edits or writes them.

**Hook type**: PostToolUse

**Configuration**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write \"$file_path\" 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

**How it works**:
- Triggers after any Edit or Write tool use
- Runs Prettier on the modified file
- Suppresses errors (2>/dev/null) to avoid blocking on non-JS files
- Always succeeds (|| true) so non-formattable files don't cause issues

**Variations**:

Python (Black):
```json
{
  "matcher": "Edit:*.py|Write:*.py",
  "hooks": [
    {
      "type": "command",
      "command": "black \"$file_path\" 2>/dev/null || true"
    }
  ]
}
```

Go (gofmt):
```json
{
  "matcher": "Edit:*.go|Write:*.go",
  "hooks": [
    {
      "type": "command",
      "command": "gofmt -w \"$file_path\""
    }
  ]
}
```

## Example 2: TypeScript Type Checking

**Use case**: Run type checking after TypeScript file modifications.

**Hook type**: PostToolUse

**Configuration**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit:*.ts|Edit:*.tsx|Write:*.ts|Write:*.tsx",
        "hooks": [
          {
            "type": "command",
            "command": "npx tsc --noEmit --pretty || true"
          }
        ]
      }
    ]
  }
}
```

**How it works**:
- Triggers only for TypeScript files
- Runs type checking without emitting files
- Shows pretty-printed errors to Claude
- Non-blocking (|| true) so Claude can continue even with type errors

## Example 3: Security - Block Dangerous Commands

**Use case**: Prevent dangerous rm commands and protect sensitive files.

**Hook type**: PreToolUse

**Implementation** (`hooks/pre_tool_use.py`):
```python
#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = []
# ///

import json
import re
import sys
import os

def is_dangerous_rm(command):
    """Detect dangerous rm commands with recursive and force flags"""
    if not command:
        return False

    normalized = command.lower().strip()

    # Patterns for rm with recursive + force
    rm_patterns = [
        r'rm\s+(-[rf]{2}|-r.*-f|-f.*-r)',
        r'rm\s+--recursive.*--force',
        r'rm\s+--force.*--recursive',
    ]

    # Dangerous target paths
    dangerous_paths = [
        '/', '~', '~/', '*', '.*', '/*', '~/.*',
        '..', '../..', '$HOME'
    ]

    # Check if command matches dangerous pattern
    for pattern in rm_patterns:
        if re.search(pattern, normalized):
            # Check if targeting dangerous paths
            for path in dangerous_paths:
                if path in command:
                    return True

    return False

def is_sensitive_file(file_path):
    """Check if file contains sensitive information"""
    if not file_path:
        return False

    filename = os.path.basename(file_path)

    # Allow sample/example files
    whitelist = [
        r'\.env\.sample$',
        r'\.env\.example$',
        r'\.env\.template$',
    ]

    for pattern in whitelist:
        if re.search(pattern, filename):
            return False

    # Block actual sensitive files
    sensitive = [
        r'\.env$',
        r'credentials\.json$',
        r'secrets\.ya?ml$',
        r'\.aws/credentials$',
        r'\.ssh/id_.*$',
    ]

    return any(re.search(pattern, file_path) for pattern in sensitive)

def main():
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # Create logs directory if needed
        os.makedirs(".claude/hooks/logs", exist_ok=True)

        # Log all attempts
        with open(".claude/hooks/logs/pre_tool_use.json", "a") as log:
            log.write(json.dumps(input_data) + "\n")

        # Check Bash commands for dangerous operations
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            if is_dangerous_rm(command):
                msg = f"BLOCKED: Dangerous rm command detected: {command}"
                print(msg, file=sys.stderr)
                sys.exit(2)  # Block with exit code 2

        # Check file operations for sensitive files
        if tool_name in ["Read", "Edit", "Write"]:
            file_path = tool_input.get("file_path", "")
            if is_sensitive_file(file_path):
                msg = f"BLOCKED: Access to sensitive file denied: {file_path}"
                print(msg, file=sys.stderr)
                sys.exit(2)  # Block with exit code 2

        # Allow operation
        sys.exit(0)

    except json.JSONDecodeError:
        # Invalid JSON input - allow but log
        print("Warning: Invalid JSON input to hook", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        # Unexpected error - allow but log
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
```

**Configuration**:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/pre_tool_use.py"
          }
        ]
      }
    ]
  }
}
```

**What it blocks**:
- `rm -rf /`
- `rm -rf ~`
- `rm -rf *`
- Access to `.env` files
- Access to `credentials.json`
- Access to SSH private keys

**What it allows**:
- `.env.sample`, `.env.example`
- Normal rm commands without recursive + force
- Regular file operations

## Example 4: Session Initialization - Load Git Context

**Use case**: Automatically load git status and recent commits at session start.

**Hook type**: SessionStart

**Implementation** (`hooks/session_start.py`):
```python
#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = []
# ///

import subprocess
import sys
import json

def get_git_status():
    """Get current git status"""
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except:
        return ""

def get_recent_commits():
    """Get last 5 commits"""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except:
        return ""

def get_current_branch():
    """Get current git branch"""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except:
        return ""

def main():
    try:
        branch = get_current_branch()
        status = get_git_status()
        commits = get_recent_commits()

        # Build context message
        context = []

        if branch:
            context.append(f"Current branch: {branch}")

        if status:
            context.append(f"\nGit status:\n{status}")

        if commits:
            context.append(f"\nRecent commits:\n{commits}")

        if context:
            # Print context that will be shown to Claude
            print("\n".join(context))

        sys.exit(0)

    except Exception as e:
        print(f"Error loading git context: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block session start on error

if __name__ == "__main__":
    main()
```

**Configuration**:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/session_start.py"
          }
        ]
      }
    ]
  }
}
```

## Example 5: Desktop Notifications

**Use case**: Get desktop notifications when Claude needs input.

**Hook type**: Notification

**macOS**:
```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude needs your input\" with title \"Claude Code\" sound name \"Glass\"'"
          }
        ]
      }
    ]
  }
}
```

**Linux (notify-send)**:
```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'Claude Code' 'Claude needs your input' -u normal"
          }
        ]
      }
    ]
  }
}
```

**Windows (PowerShell)**:
```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "powershell -Command \"New-BurntToastNotification -Text 'Claude Code', 'Claude needs your input'\""
          }
        ]
      }
    ]
  }
}
```

## Example 6: Ensure Tests Pass Before Completion

**Use case**: Prevent Claude from stopping until all tests pass.

**Hook type**: Stop

**Implementation** (`hooks/stop.py`):
```python
#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = []
# ///

import subprocess
import sys

def run_tests():
    """Run test suite and return exit code"""
    try:
        result = subprocess.run(
            ["npm", "test"],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Tests timed out after 60 seconds"
    except Exception as e:
        return 1, "", str(e)

def main():
    exit_code, stdout, stderr = run_tests()

    if exit_code != 0:
        # Tests failed - block stopping
        msg = "Cannot complete: Tests are failing. Please fix the failing tests before completing."
        if stderr:
            msg += f"\n\nError output:\n{stderr}"
        print(msg, file=sys.stderr)
        sys.exit(2)  # Block with exit code 2

    # Tests passed - allow completion
    print("All tests passed ✓")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

**Configuration**:
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/stop.py"
          }
        ]
      }
    ]
  }
}
```

## Example 7: Backup Transcripts Before Compaction

**Use case**: Save conversation transcripts before they get compacted.

**Hook type**: PreCompact

**Implementation** (`hooks/pre_compact.py`):
```python
#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = []
# ///

import json
import sys
import os
import shutil
from datetime import datetime

def main():
    try:
        # Read input
        input_data = json.loads(sys.stdin.read())
        transcript_path = input_data.get("transcript_path", "")

        if not transcript_path or not os.path.exists(transcript_path):
            sys.exit(0)

        # Create backup directory
        backup_dir = ".claude/hooks/backups"
        os.makedirs(backup_dir, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = input_data.get("session_id", "unknown")
        backup_name = f"transcript_{session_id}_{timestamp}.jsonl"
        backup_path = os.path.join(backup_dir, backup_name)

        # Copy transcript
        shutil.copy2(transcript_path, backup_path)

        print(f"Transcript backed up to: {backup_path}")
        sys.exit(0)

    except Exception as e:
        print(f"Backup error: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block compaction on error

if __name__ == "__main__":
    main()
```

**Configuration**:
```json
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/pre_compact.py"
          }
        ]
      }
    ]
  }
}
```

## Example 8: Run Linters After Edits

**Use case**: Automatically lint code and provide feedback to Claude.

**Hook type**: PostToolUse

**ESLint (JavaScript/TypeScript)**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit:*.js|Edit:*.jsx|Edit:*.ts|Edit:*.tsx|Write:*.js|Write:*.jsx|Write:*.ts|Write:*.tsx",
        "hooks": [
          {
            "type": "command",
            "command": "npx eslint \"$file_path\" --format=compact || true"
          }
        ]
      }
    ]
  }
}
```

**Pylint (Python)**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit:*.py|Write:*.py",
        "hooks": [
          {
            "type": "command",
            "command": "pylint \"$file_path\" --output-format=text || true"
          }
        ]
      }
    ]
  }
}
```

## Example 9: Log User Prompts for Compliance

**Use case**: Log all user prompts for auditing and compliance.

**Hook type**: UserPromptSubmit

**Implementation** (`hooks/user_prompt_submit.py`):
```python
#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = []
# ///

import json
import sys
import os
from datetime import datetime

def main():
    try:
        # Read input
        input_data = json.loads(sys.stdin.read())

        # Extract prompt and metadata
        user_prompt = input_data.get("user_prompt", "")
        session_id = input_data.get("session_id", "")

        # Create logs directory
        log_dir = ".claude/hooks/logs"
        os.makedirs(log_dir, exist_ok=True)

        # Create log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "prompt": user_prompt,
            "prompt_length": len(user_prompt)
        }

        # Append to log file
        log_file = os.path.join(log_dir, "prompts.jsonl")
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Allow prompt to proceed
        sys.exit(0)

    except Exception as e:
        # Don't block on logging errors
        print(f"Logging error: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
```

**Configuration**:
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/user_prompt_submit.py"
          }
        ]
      }
    ]
  }
}
```

## Example 10: Multi-Hook Configuration

**Use case**: Complete production setup with multiple hooks.

**Full configuration**:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/session_start.py"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/user_prompt_submit.py"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/pre_tool_use.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write \"$file_path\" 2>/dev/null || true"
          }
        ]
      },
      {
        "matcher": "Edit:*.ts|Edit:*.tsx|Write:*.ts|Write:*.tsx",
        "hooks": [
          {
            "type": "command",
            "command": "npx tsc --noEmit || true"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude needs input\" with title \"Claude Code\"'"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/pre_compact.py"
          }
        ]
      }
    ]
  }
}
```

## Testing Your Hooks

### Manual Testing
```bash
# Test a hook manually
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | uv run .claude/hooks/pre_tool_use.py
echo $?  # Should output 2 (blocked)

echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | uv run .claude/hooks/pre_tool_use.py
echo $?  # Should output 0 (allowed)
```

### Automated Testing
Create `tests/test_hooks.sh`:
```bash
#!/bin/bash

test_dangerous_rm() {
    echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | \
        uv run .claude/hooks/pre_tool_use.py 2>/dev/null
    if [ $? -eq 2 ]; then
        echo "✓ Dangerous rm blocked"
        return 0
    else
        echo "✗ Dangerous rm NOT blocked"
        return 1
    fi
}

test_safe_command() {
    echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | \
        uv run .claude/hooks/pre_tool_use.py 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✓ Safe command allowed"
        return 0
    else
        echo "✗ Safe command blocked"
        return 1
    fi
}

# Run tests
test_dangerous_rm && test_safe_command
```

## Troubleshooting

### Hook Not Running
- Check JSON syntax in settings.json
- Verify matcher pattern
- Ensure script is executable: `chmod +x .claude/hooks/script.py`
- Check hook logs: `cat .claude/hooks/logs/*.json`

### Hook Blocking Incorrectly
- Review exit codes (0 = allow, 2 = block)
- Check stderr output
- Test hook manually with sample inputs
- Add debug logging to hook script

### Performance Issues
- Reduce hook execution time
- Use more specific matchers
- Cache expensive operations
- Consider running hooks asynchronously (if non-blocking)
