# Claude Code Hook Examples

Complete working examples for the most common hook use cases.

## Quick Reference

| Use Case | Hook Type | Config style |
|----------|-----------|--------------|
| Auto-format code | PostToolUse | Inline command |
| Block dangerous commands | PreToolUse | Python script |
| Load git context | SessionStart | Python script |
| Desktop notifications | Notification | Inline command |
| Ensure tests pass | Stop | Python script |
| Backup transcripts | PreCompact | Python script |
| Type checking | PostToolUse | Inline command |
| Log prompts | UserPromptSubmit | Python script |

---

## Example 1: Auto-Format Code (Inline)

```json
{
  "hooks": {
    "PostToolUse": [
      {"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "npx prettier --write \"$file_path\" 2>/dev/null || true"}]},
      {"matcher": "Edit:*.py|Write:*.py", "hooks": [{"type": "command", "command": "black \"$file_path\" 2>/dev/null || true"}]},
      {"matcher": "Edit:*.go|Write:*.go", "hooks": [{"type": "command", "command": "gofmt -w \"$file_path\""}]}
    ]
  }
}
```

## Example 2: TypeScript Type Checking (Inline)

```json
{
  "hooks": {
    "PostToolUse": [
      {"matcher": "Edit:*.ts|Edit:*.tsx|Write:*.ts|Write:*.tsx", "hooks": [{"type": "command", "command": "npx tsc --noEmit --pretty || true"}]}
    ]
  }
}
```

## Example 3: Desktop Notifications (Inline)

macOS: `osascript -e 'display notification "Claude needs input" with title "Claude Code" sound name "Glass"'`  
Linux: `notify-send 'Claude Code' 'Claude needs your input' -u normal`  
Windows: `powershell -Command "New-BurntToastNotification -Text 'Claude Code', 'Claude needs your input'"`

```json
{
  "hooks": {
    "Notification": [
      {"matcher": "", "hooks": [{"type": "command", "command": "osascript -e 'display notification \"Claude needs input\" with title \"Claude Code\"'"}]}
    ]
  }
}
```

## Example 4: Security - Block Dangerous Commands (Script)

Use the template from `assets/templates/pre_tool_use_template.py`. The core detection:

```python
def is_dangerous_rm(command):
    patterns = [r'rm\s+(-[rf]{2}|-r.*-f|-f.*-r)', r'rm\s+--recursive.*--force']
    dangerous_paths = ['/', '~', '~/', '*', '.*', '/*', '..', '$HOME']
    normalized = command.lower().strip()
    for pattern in patterns:
        if re.search(pattern, normalized):
            for path in dangerous_paths:
                if path in command:
                    return True
    return False

def is_sensitive_file(file_path):
    whitelist = [r'\.env\.(sample|example|template)$']
    sensitive = [r'\.env$', r'credentials\.json$', r'secrets\.ya?ml$', r'\.aws/credentials$', r'\.ssh/id_.*$']
    filename = os.path.basename(file_path)
    if any(re.search(p, filename) for p in whitelist): return False
    return any(re.search(p, file_path) for p in sensitive)
```

Install:
```bash
cp assets/templates/pre_tool_use_template.py .claude/hooks/pre_tool_use.py
chmod +x .claude/hooks/pre_tool_use.py
uv run scripts/hook_manager.py install PreToolUse --command "uv run .claude/hooks/pre_tool_use.py"
```

## Example 5: Load Git Context at Session Start (Script)

```python
#!/usr/bin/env -S uv run --quiet --script
import subprocess, sys, json

def run(cmd): 
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    return r.stdout.strip()

def main():
    branch = run(["git", "branch", "--show-current"])
    status = run(["git", "status", "--short"])
    commits = run(["git", "log", "--oneline", "-5"])
    parts = []
    if branch: parts.append(f"Branch: {branch}")
    if status: parts.append(f"Status:\n{status}")
    if commits: parts.append(f"Recent commits:\n{commits}")
    if parts: print("\n".join(parts))
    sys.exit(0)

if __name__ == "__main__":
    main()
```

## Example 6: Ensure Tests Pass Before Stop (Script)

```python
#!/usr/bin/env -S uv run --quiet --script
import subprocess, sys

def main():
    r = subprocess.run(["npm", "test"], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        print(f"Cannot complete: Tests failing.\n{r.stderr}", file=sys.stderr)
        sys.exit(2)
    print("All tests passed ✓")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

## Example 7: Backup Transcripts (Script)

```python
#!/usr/bin/env -S uv run --quiet --script
import json, sys, os, shutil
from datetime import datetime

def main():
    data = json.loads(sys.stdin.read())
    transcript_path = data.get("transcript_path", "")
    if not transcript_path or not os.path.exists(transcript_path): sys.exit(0)
    backup_dir = ".claude/hooks/backups"
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = os.path.join(backup_dir, f"transcript_{data.get('session_id','x')}_{ts}.jsonl")
    shutil.copy2(transcript_path, backup)
    print(f"Backed up to: {backup}")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

## Example 8: Multi-Hook Production Setup

```json
{
  "hooks": {
    "SessionStart": [{"matcher": "", "hooks": [{"type": "command", "command": "uv run .claude/hooks/session_start.py"}]}],
    "PreToolUse": [{"matcher": ".*", "hooks": [{"type": "command", "command": "uv run .claude/hooks/pre_tool_use.py"}]}],
    "PostToolUse": [
      {"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "npx prettier --write \"$file_path\" 2>/dev/null || true"}]},
      {"matcher": "Edit:*.ts|Edit:*.tsx|Write:*.ts|Write:*.tsx", "hooks": [{"type": "command", "command": "npx tsc --noEmit || true"}]}
    ],
    "Notification": [{"matcher": "", "hooks": [{"type": "command", "command": "osascript -e 'display notification \"Claude needs input\" with title \"Claude Code\"'"}]}],
    "PreCompact": [{"matcher": "", "hooks": [{"type": "command", "command": "uv run .claude/hooks/pre_compact.py"}]}]
  }
}
```

## Testing

```bash
# Manual test
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | uv run .claude/hooks/pre_tool_use.py
echo $?  # 2 = blocked

echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | uv run .claude/hooks/pre_tool_use.py
echo $?  # 0 = allowed
```
