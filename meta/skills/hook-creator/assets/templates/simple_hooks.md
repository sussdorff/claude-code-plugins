# Simple Hook Examples (No Script Required)

These hooks can be configured directly in settings.json without creating separate Python scripts.

## Desktop Notifications

### macOS
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

### Linux (notify-send)
```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'Claude Code' 'Claude needs your input' -u normal -i dialog-information"
          }
        ]
      }
    ]
  }
}
```

### Windows (PowerShell toast notification)
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

## Code Formatting

### Prettier (JavaScript/TypeScript)
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

### Black (Python)
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit:*.py|Write:*.py",
        "hooks": [
          {
            "type": "command",
            "command": "black \"$file_path\" 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

### gofmt (Go)
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit:*.go|Write:*.go",
        "hooks": [
          {
            "type": "command",
            "command": "gofmt -w \"$file_path\""
          }
        ]
      }
    ]
  }
}
```

### rustfmt (Rust)
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit:*.rs|Write:*.rs",
        "hooks": [
          {
            "type": "command",
            "command": "rustfmt \"$file_path\""
          }
        ]
      }
    ]
  }
}
```

## Linting

### ESLint (JavaScript/TypeScript)
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit:*.js|Edit:*.jsx|Edit:*.ts|Edit:*.tsx",
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

### Pylint (Python)
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

## Type Checking

### TypeScript
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

### Python (mypy)
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit:*.py|Write:*.py",
        "hooks": [
          {
            "type": "command",
            "command": "mypy \"$file_path\" || true"
          }
        ]
      }
    ]
  }
}
```

## Git Operations

### Auto-stage modified files
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "git add \"$file_path\" 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

### Show git status on session start
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "echo '=== Git Status ===' && git status --short && echo '' && echo '=== Recent Commits ===' && git log --oneline -5"
          }
        ]
      }
    ]
  }
}
```

## Testing

### Run tests on stop
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "npm test || exit 2"
          }
        ]
      }
    ]
  }
}
```

### Run specific tests after file changes
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit:*.test.js|Write:*.test.js",
        "hooks": [
          {
            "type": "command",
            "command": "npm test -- \"$file_path\" || true"
          }
        ]
      }
    ]
  }
}
```

## Logging & Auditing

### Log all bash commands
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"[$(date)] Bash command executed\" >> .claude/hooks/logs/bash_commands.log"
          }
        ]
      }
    ]
  }
}
```

### Backup transcript before compaction
```json
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "mkdir -p .claude/backups && cp $transcript_path .claude/backups/transcript_$(date +%Y%m%d_%H%M%S).jsonl"
          }
        ]
      }
    ]
  }
}
```

## Build Operations

### Run build after TypeScript changes
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit:*.ts|Edit:*.tsx",
        "hooks": [
          {
            "type": "command",
            "command": "npm run build || true"
          }
        ]
      }
    ]
  }
}
```

### Ensure build passes before completion
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "npm run build || (echo 'Build failed - please fix errors before completing' >&2 && exit 2)"
          }
        ]
      }
    ]
  }
}
```

## File Permissions

### Make shell scripts executable
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write:*.sh",
        "hooks": [
          {
            "type": "command",
            "command": "chmod +x \"$file_path\""
          }
        ]
      }
    ]
  }
}
```

## Documentation

### Generate docs after code changes
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit:src/*.js|Write:src/*.js",
        "hooks": [
          {
            "type": "command",
            "command": "npm run docs:generate || true"
          }
        ]
      }
    ]
  }
}
```

## Tips

1. **Use `|| true`** at the end of commands to make them non-blocking:
   - Without: `npm test` (blocks on failure)
   - With: `npm test || true` (continues even on failure)

2. **Redirect errors** to suppress noise:
   - `2>/dev/null` suppresses stderr
   - `>/dev/null 2>&1` suppresses all output

3. **Use exit code 2** to block operations:
   - In PreToolUse: Blocks the tool from running
   - In Stop: Forces Claude to continue working
   - In UserPromptSubmit: Blocks the prompt

4. **Chain commands** with `&&`:
   - `command1 && command2` (command2 only runs if command1 succeeds)

5. **Use environment variables**:
   - `$file_path` - Available in Edit/Write PostToolUse hooks
   - `$transcript_path` - Available in PreCompact hooks
   - `$CLAUDE_PROJECT_DIR` - Always available

6. **Matcher patterns**:
   - `""` or `"*"` - Matches all
   - `"Edit|Write"` - Matches Edit OR Write
   - `"Edit:*.ts"` - Matches Edit on TypeScript files
   - `".*"` - Regex to match any tool name
