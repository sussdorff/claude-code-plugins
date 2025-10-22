---
name: hook-creator
description: This skill should be used when creating, configuring, or managing Claude Code hooks. Use when users want to add automated behaviors, security validation, code quality checks, or workflow automation to their Claude Code setup. Also use when users ask about hook best practices, security patterns, or want to troubleshoot existing hooks.
---

# Hook Creator

## Overview

This skill provides comprehensive guidance and tools for creating Claude Code hooks. Hooks are shell commands that execute automatically at specific points in Claude Code's lifecycle, enabling deterministic control over behavior such as security validation, code quality enforcement, and workflow automation.

## When to Use This Skill

Use this skill when users request:

- Creating new hooks for security, quality, or automation
- Understanding hook types and use cases
- Installing or configuring hooks in settings.json
- Security best practices for hooks
- Troubleshooting hook behavior
- Examples of common hook patterns

## Core Concepts

### What Are Hooks?

Hooks are user-defined shell commands that execute at specific lifecycle events. They provide deterministic control by ensuring certain actions always occur, rather than relying on Claude to remember or decide.

### The 8 Hook Types

1. **SessionStart** - Initialize context at session start
2. **UserPromptSubmit** - Process prompts before Claude sees them
3. **PreToolUse** - Validate/block tool calls before execution (security)
4. **PostToolUse** - Auto-format, lint, or process after tool execution
5. **Notification** - Handle notifications (desktop alerts, TTS)
6. **Stop** - Validate completion criteria before allowing Claude to stop
7. **SubagentStop** - Process subagent task completion
8. **PreCompact** - Backup transcripts before compaction

### Hook Control Levels

| Hook Type | Can Block? | Common Purpose |
|-----------|------------|----------------|
| PreToolUse | Yes (exit 2) | Security validation |
| Stop | Yes (exit 2) | Quality gates |
| UserPromptSubmit | Yes (exit 2) | Prompt validation |
| PostToolUse | No | Auto-formatting, linting |
| SessionStart | No | Context loading |
| Notification | No | Alerts |
| SubagentStop | Yes (exit 2) | Validation |
| PreCompact | No | Backup |

## Quick Start

### Simple Hook Setup

For simple hooks that don't require custom logic, configure directly in settings.json.

**Example: Auto-format with Prettier**

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

For additional formatting examples (Black, gofmt, rustfmt, etc.), see `assets/templates/simple_hooks.md`.

### Advanced Hook Setup

For hooks requiring custom logic (security validation, complex workflows), use Python scripts with UV.

**1. Create the hook script**

Use the templates in `assets/templates/`:
- `pre_tool_use_template.py` - Security validation
- `post_tool_use_template.py` - Auto-formatting/linting
- `session_start_template.py` - Context loading
- `stop_template.py` - Completion validation

**2. Customize the template**

Copy a template to `.claude/hooks/` and modify the validation logic:

```bash
cp assets/templates/pre_tool_use_template.py .claude/hooks/pre_tool_use.py
chmod +x .claude/hooks/pre_tool_use.py
```

**3. Install the hook**

Use the hook manager script:

```bash
uv run scripts/hook_manager.py install PreToolUse \
  --command "uv run .claude/hooks/pre_tool_use.py"
```

Or manually edit settings.json:

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

## Common Use Cases

### 1. Security & Protection

Block dangerous operations and protect sensitive files.

**Use PreToolUse hook with security validation:**

```python
# .claude/hooks/pre_tool_use.py
def is_dangerous_rm(command):
    patterns = [r'rm\s+(-[rf]{2}|-r.*-f|-f.*-r)']
    dangerous_paths = ['/', '~', '*']
    # Check patterns and paths
    return is_match

def is_sensitive_file(file_path):
    sensitive = [r'\.env$', r'credentials\.json$']
    return any(re.search(p, file_path) for p in sensitive)
```

Reference `references/security_patterns.md` for comprehensive security patterns.

### 2. Code Quality Automation

Automatically format and lint code after edits. See `references/hook_examples.md` and `assets/templates/simple_hooks.md` for complete examples including:
- Prettier (JavaScript/TypeScript)
- Black (Python)
- gofmt (Go)
- ESLint, Pylint
- TypeScript type checking

### 3. Development Context

Load git status and project context on session start.

**Session initialization:**

```python
# .claude/hooks/session_start.py
def get_git_info():
    return {
        "branch": git("branch --show-current"),
        "status": git("status --short"),
        "commits": git("log --oneline -5")
    }

# Print context for Claude
print(format_context(get_git_info()))
```

Reference `assets/templates/session_start_template.py`.

### 4. Quality Gates

Ensure tests pass before allowing completion.

**Stop hook validation:**

```python
# .claude/hooks/stop.py
def run_tests():
    result = subprocess.run(["npm", "test"], timeout=60)
    return result.returncode == 0

if not run_tests():
    print("Tests failing - please fix before completing", file=sys.stderr)
    sys.exit(2)  # Block completion
```

Reference `assets/templates/stop_template.py`.

### 5. Desktop Notifications

Get notified when Claude needs input. See `assets/templates/simple_hooks.md` for platform-specific examples (macOS, Linux, Windows).

### 6. Transcript Backup

Automatically backup conversations before compaction.

```bash
mkdir -p .claude/hooks/backups
# Hook copies $transcript_path to backups/ with timestamp
```

## Security Best Practices

### Critical Security Principles

1. **Principle of Least Privilege**: Only grant necessary access
2. **Defense in Depth**: Multiple validation layers
3. **Fail Secure**: Block by default on errors
4. **Comprehensive Logging**: Audit trail for compliance

### Dangerous Patterns to Block

Reference `references/security_patterns.md` for detailed patterns:

**Destructive Operations:**
- `rm -rf /`, `rm -rf ~`, `rm -rf *`
- `chmod 777` (world-writable permissions)
- `sudo rm`, `sudo chmod` (privilege escalation)

**Sensitive Files:**
- `.env` (environment variables with secrets)
- `credentials.json`, `secrets.yaml`
- `~/.aws/credentials`, `~/.ssh/id_rsa`

**System Paths:**
- `/etc/`, `/bin/`, `/sys/`, `/proc/`

### Implementation Pattern

```python
def validate_tool_use(tool_name, tool_input):
    # Layer 1: Command pattern matching
    if tool_name == "Bash":
        if is_dangerous_pattern(tool_input["command"]):
            return False, "Blocked dangerous command"

    # Layer 2: File path validation
    if tool_name in ["Read", "Edit", "Write"]:
        if is_sensitive_file(tool_input["file_path"]):
            return False, "Blocked sensitive file access"

    # Layer 3: System path protection
    if is_system_path(tool_input.get("file_path", "")):
        return False, "Blocked system directory access"

    return True, None
```

## Hook Configuration

### Settings File Locations

- **User scope**: `~/.claude/settings.json` (applies to all projects)
- **Project scope**: `<project>/.claude/settings.json` (project-specific)

### Configuration Structure

```json
{
  "hooks": {
    "HookType": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          {
            "type": "command",
            "command": "shell command"
          }
        ]
      }
    ]
  }
}
```

### Matcher Patterns

- `""` or `"*"` - Match all tools
- `"Edit|Write"` - Match Edit OR Write
- `"Edit:*.ts"` - Match Edit on TypeScript files only
- `".*"` - Regex match any tool (PreToolUse/PostToolUse)

### Exit Codes

- `0` - Success, allow operation (stdout shown)
- `2` - Block operation (stderr shown to Claude)
- Other - Non-blocking error (shown to user)

### JSON Response (Advanced)

For complex control flow:

```json
{
  "continue": false,
  "decision": "deny",
  "additionalContext": "Message for Claude"
}
```

## Tools & Scripts

### Hook Manager

Install, remove, and list hooks using the hook manager:

```bash
# Install a hook
uv run scripts/hook_manager.py install PreToolUse \
  --command "uv run .claude/hooks/pre_tool_use.py"

# Install with matcher
uv run scripts/hook_manager.py install PostToolUse \
  --matcher "Edit:*.py" \
  --command "black \"$file_path\""

# List all hooks
uv run scripts/hook_manager.py list

# Remove a hook
uv run scripts/hook_manager.py remove PreToolUse \
  --command "uv run .claude/hooks/pre_tool_use.py"

# User scope (applies to all projects)
uv run scripts/hook_manager.py install Notification \
  --command "osascript -e 'display notification...'" \
  --scope user
```

## Workflow Guide

### Creating a New Security Hook

**Step 1: Choose the hook template**

```bash
cp assets/templates/pre_tool_use_template.py .claude/hooks/pre_tool_use.py
chmod +x .claude/hooks/pre_tool_use.py
```

**Step 2: Customize validation logic**

Edit `.claude/hooks/pre_tool_use.py` to add your security rules. Reference `references/security_patterns.md` for dangerous pattern detection.

**Step 3: Test the hook**

```bash
# Option 1: Use built-in test mode
uv run .claude/hooks/pre_tool_use.py --test

# Option 2: Use automated test script
./assets/test_hooks.sh pre_tool_use

# Option 3: Manual testing
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | \
  uv run .claude/hooks/pre_tool_use.py
# Should exit with code 2

echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | \
  uv run .claude/hooks/pre_tool_use.py
# Should exit with code 0
```

**Step 4: Install the hook**

```bash
uv run scripts/hook_manager.py install PreToolUse \
  --command "uv run .claude/hooks/pre_tool_use.py"
```

**Step 5: Verify installation**

```bash
uv run scripts/hook_manager.py list
```

### Creating an Auto-Format Hook

**Step 1: Determine if you need a script**

For simple formatting, use inline commands:

```bash
uv run scripts/hook_manager.py install PostToolUse \
  --matcher "Edit|Write" \
  --command "npx prettier --write \"\$file_path\" 2>/dev/null || true"
```

For multiple formatters or complex logic, use the template:

```bash
cp assets/templates/post_tool_use_template.py .claude/hooks/post_tool_use.py
```

**Step 2: Customize formatter logic**

Edit the `format_file()` function to support your file types.

**Step 3: Install and test**

```bash
uv run scripts/hook_manager.py install PostToolUse \
  --matcher "Edit|Write" \
  --command "uv run .claude/hooks/post_tool_use.py"
```

## Reference Materials

### Comprehensive Documentation

**Hook Types Reference** - `references/hook_types.md`
- Complete documentation of all 8 hook types
- Use cases and examples for each
- Available data and environment variables
- Blocking capabilities and exit codes
- **Search tips:**
  - `## [0-9]\. (SessionStart|PreToolUse|PostToolUse)` - Find specific hook type documentation
  - `Blocking capability` - Understand which hooks can block operations
  - `Common use cases` - See when to use each hook type

**Security Patterns** - `references/security_patterns.md`
- Dangerous command patterns to block
- File validation best practices
- Path normalization and traversal prevention
- Security testing and validation
- **Search tips:**
  - `### Category [0-9]:` - Find specific threat categories
  - `is_dangerous_.*\(` - Locate validation function examples
  - `def normalize_path` - Find path validation utilities
  - `Security Checklist` - Review pre-deployment requirements

**Hook Examples** - `references/hook_examples.md`
- 10+ complete working hook implementations
- Security validation examples
- Auto-formatting and linting
- Session initialization
- Quality gates and testing
- Multi-hook configurations
- **Search tips:**
  - `## Example [0-9]+:` - Jump to specific examples
  - `"PostToolUse"` - Find formatting/linting examples
  - `"PreToolUse"` - Find security validation examples
  - `"Stop"` - Find quality gate examples

**Simple Hooks** - `assets/templates/simple_hooks.md`
- Inline hook examples (no scripts needed)
- Quick reference for common patterns
- Copy-paste configurations
- **Search tips:**
  - `## [A-Z][a-z]+ (Formatting|Notifications|Testing)` - Find examples by category
  - `prettier|black|gofmt` - Find formatter configurations
  - `exit 2` - Find blocking hook examples

**Troubleshooting** - `references/troubleshooting.md`
- Solutions to common hook issues
- Debugging techniques and tools
- Performance optimization tips
- Error message explanations
- **Search tips:**
  - `## Hook Not Running` - Fix hooks that don't execute
  - `## Hook Blocking Incorrectly` - Debug validation logic
  - `## Performance Issues` - Optimize slow hooks
  - `## Common Error Messages` - Understand error messages

### Templates

**Python Script Templates** - `assets/templates/`
- `pre_tool_use_template.py` - Security validation
- `post_tool_use_template.py` - Auto-formatting/linting
- `session_start_template.py` - Context initialization
- `stop_template.py` - Completion validation

All templates include:
- UV script headers for dependency isolation
- Comprehensive documentation
- Error handling
- Logging infrastructure
- Modular, reusable functions
- Built-in test mode (run with `--test` flag)

**Testing Tools** - `assets/test_hooks.sh`
- Automated testing script for hook validation
- Tests security patterns, exit codes, and integration
- Run individual tests or full test suite
- Usage: `./assets/test_hooks.sh` or `./assets/test_hooks.sh pre_tool_use`

## Troubleshooting

For comprehensive troubleshooting guidance, see `references/troubleshooting.md`.

**Quick diagnostics:**

```bash
# Validate settings.json
cat .claude/settings.json | jq .

# Make script executable
chmod +x .claude/hooks/your_hook.py

# Test hook manually
echo '{"tool_name":"Test","tool_input":{}}' | uv run .claude/hooks/your_hook.py
echo $?  # Check exit code (0 = allow, 2 = block)

# Check logs
tail -f .claude/hooks/logs/pre_tool_use.jsonl

# Test with built-in test mode
uv run .claude/hooks/your_hook.py --test
```

See `references/troubleshooting.md` for solutions to:
- Hook not running
- Hook blocking incorrectly
- Performance issues
- Import errors
- Settings not taking effect
- And more...

## Best Practices Summary

1. **Start simple** - Begin with inline commands, graduate to scripts when needed
2. **Use templates** - Leverage provided templates for common patterns
3. **Test thoroughly** - Test hooks manually before deploying
4. **Fail secure** - Block by default on errors (exit 2)
5. **Log everything** - Maintain audit trails for security and debugging
6. **Use UV** - Isolate hook dependencies from project dependencies
7. **Keep hooks fast** - Optimize for quick execution (< 1 second)
8. **Document security rules** - Explain why patterns are blocked
9. **Review regularly** - Update hooks as threats evolve
10. **Version control** - Commit hook scripts to git for team sharing

## Additional Resources

- **Claude Code Hooks Documentation**: https://docs.claude.com/en/docs/claude-code/hooks
- **Hook Guide**: https://docs.claude.com/en/docs/claude-code/hooks-guide
- **Community Examples**: https://github.com/disler/claude-code-hooks-mastery
