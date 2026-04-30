---
name: hook-creator
model: sonnet
description: >-
  Create and manage Claude Code hooks across all 8 hook types. Use when adding
  automated behaviors, troubleshooting hooks, or learning best practices.
  Triggers on create hook, hooks, PreToolUse, PostToolUse, security hook.
  Enforces the three-tier exit code convention (0=info/pass, 1=hook-error, 2=block)
  — see malte/standards/dev-tools/hook-exit-codes.md for the full standard.
disableModelInvocation: true
requires_standards: [english-only]
---

# Hook Creator

## Overview

Create and manage Claude Code hooks -- shell commands that execute automatically at specific lifecycle events. Hooks provide deterministic control over security validation, code quality enforcement, and workflow automation.

## When to Use

- Create new hooks (security, quality, automation)
- Install or configure hooks in settings.json
- Troubleshoot hook behavior
- Understand hook types and capabilities

## Mode Routing

| Request Type | Action |
|-------------|--------|
| Simple formatting/notification | Inline command in settings.json |
| Security validation | Python script from `assets/templates/pre_tool_use_template.py` |
| Complex post-processing | Python script from `assets/templates/post_tool_use_template.py` |
| Session initialization | Python script from `assets/templates/session_start_template.py` |
| Quality gates | Python script from `assets/templates/stop_template.py` |
| Troubleshooting | Consult `references/troubleshooting.md` |

## The 9 Hook Types

| Hook Type | Can Block? | Purpose |
|-----------|------------|---------|
| PreToolUse | Yes (exit 2) | Security validation |
| Stop | Yes (exit 2) | Quality gates |
| UserPromptSubmit | Yes (exit 2) | Prompt validation |
| SubagentStop | Yes (exit 2) | Subagent validation |
| PostToolUse | No | Auto-formatting, linting |
| SessionStart | No | Context loading, additionalContext injection |
| Notification | No | Alerts |
| PreCompact | No | Transcript backup |
| InstructionsLoaded | No | **Observability only** — fires when a CLAUDE.md is loaded |

### InstructionsLoaded Limitations

`InstructionsLoaded` is **async/observability-only**. It cannot block, cannot modify instruction content, and **cannot inject `additionalContext`**. Use it for audit logging and diagnostics only.

Available fields: `file_path`, `memory_type` ("User"/"Project"/"Local"/"Managed"), `load_reason` ("session_start"/"nested_traversal"/"path_glob_match"/"include"), plus optional `globs`, `trigger_file_path`, `parent_file_path`.

For standards injection into model context, use `SessionStart` (which supports `additionalContext`).

Full documentation of each type, available data, and environment variables: `references/hook_types.md`

## Quick Start

### Simple Hook (inline command)

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

More inline examples (Black, gofmt, notifications): `assets/templates/simple_hooks.md`

### Advanced Hook (Python script)

1. Copy template: `cp assets/templates/pre_tool_use_template.py .claude/hooks/pre_tool_use.py`
2. Make executable: `chmod +x .claude/hooks/pre_tool_use.py`
3. Customize validation logic
4. Install: `uv run scripts/hook_manager.py install PreToolUse --command "uv run .claude/hooks/pre_tool_use.py"`
5. Test: `echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | uv run .claude/hooks/pre_tool_use.py`

## Hook Configuration

### Settings locations

- **User scope**: `~/.claude/settings.json` (all projects)
- **Project scope**: `<project>/.claude/settings.json` (project-specific)

### Matcher patterns

- `""` or `"*"` -- Match all tools
- `"Edit|Write"` -- Match Edit OR Write
- `"Edit:*.ts"` -- Match Edit on TypeScript files only
- `".*"` -- Regex match any tool

### Exit codes

Three-tier standard (see `malte/standards/dev-tools/hook-exit-codes.md` for full reference):

| Code | Name | Effect | Where output goes |
|------|------|--------|-------------------|
| `0` | info/pass | Non-blocking; operation proceeds | stdout → user transcript |
| `1` | hook-error | Non-blocking; treated as *hook error* by runtime (not intentional warn) | stdout/stderr → user |
| `2` | block | **Blocking; non-bypassable** | stderr → Claude as context |

WHY exit 2 specifically: Other non-zero codes are treated as unintended hook failures,
not deliberate blocks. Exit 2 is the only code the runtime interprets as an intentional denial.

WHY not exit 1 to warn: Exit 1 is logged by the runtime as a hook *error*, not a semantic
warning. For non-blocking informational signals, use exit 0 and write to stdout/stderr.

**Hook type capabilities** — which hooks CAN block:
- **Blocking** (can use exit 2): `PreToolUse`, `Stop`, `UserPromptSubmit`, `SubagentStop`
- **Non-blocking** (SHOULD only use exit 0): `PostToolUse`, `SessionStart`, `Notification`, `PreCompact`, `InstructionsLoaded`

For non-blocking hooks (especially observability-only hooks like `InstructionsLoaded`),
always exit 0 on errors — fail-open avoids false error signals in the runtime log.

### JSON response (advanced)

Hooks can output JSON for richer control:

```json
{"continue": false, "decision": "deny", "additionalContext": "Message for Claude"}
```

## Hook Manager

Install, remove, and list hooks via the manager script:

```bash
uv run scripts/hook_manager.py install PreToolUse --command "uv run .claude/hooks/pre_tool_use.py"
uv run scripts/hook_manager.py install PostToolUse --matcher "Edit:*.py" --command "black \"$file_path\""
uv run scripts/hook_manager.py list
uv run scripts/hook_manager.py remove PreToolUse --command "uv run .claude/hooks/pre_tool_use.py"
uv run scripts/hook_manager.py install Notification --command "osascript -e '...'" --scope user
```

## Security Essentials

Core principles: Least Privilege, Defense in Depth, Fail Secure (exit 2 in blocking security hooks; exit 0 fail-open in non-blocking hooks — see § Exit codes), Comprehensive Logging.

WHY fail secure: A broken blocking security hook that silently passes defeats its purpose. Always exit 2 on unexpected errors in PreToolUse/Stop hooks. Non-blocking hooks (PostToolUse, SessionStart, etc.) should exit 0 even on errors — exit 2 from a non-blocking hook is a confusing no-op.

Implement layered validation in PreToolUse hooks:
1. **Command patterns** -- Block destructive operations (`rm -rf /`, `chmod 777`, `sudo rm`)
2. **File paths** -- Protect sensitive files (`.env`, `credentials.json`, `~/.ssh/`)
3. **System paths** -- Block access to `/etc/`, `/bin/`, `/sys/`

Full patterns, detection functions, and testing: `references/security_patterns.md`

## Testing Hooks

Run the bundled test helper: `scripts/test_hooks.sh [hook_path]`

The script exercises built-in test mode, manual stdin injection, automated pytest, and quick diagnostics. See [scripts/test_hooks.sh](scripts/test_hooks.sh) for the full sequence.

## Best Practices

1. Start simple -- inline commands first, scripts when logic grows
2. Use provided templates from `assets/templates/`
3. Test hooks before deploying (manual + `--test` flag)
4. Fail secure -- `exit 2` on errors in blocking hooks (PreToolUse, Stop); `exit 0` fail-open in non-blocking hooks (PostToolUse, SessionStart, etc.) — see § Exit codes
5. Keep hooks fast (< 1 second). WHY: Hooks run synchronously; slow hooks degrade the interactive experience.
6. Use UV for dependency isolation. WHY: Avoids conflicts with project dependencies.
7. Log decisions for audit trails
8. Commit hook scripts to git for team sharing

## Do NOT

- Do NOT create hooks that modify tool input -- hooks can only allow/block/add context
  WHY: Hooks are not middleware. Modifying input silently breaks the user's mental model of what Claude is doing.
- Do NOT use `exit 1` to block operations -- use `exit 2`
  WHY: Exit 1 is treated as a hook error, not an intentional block. Claude will report it as a failure, not a denial. The same applies to trying to use exit 1 as a semantic "warn" — it is logged as an error. Use exit 0 with informational stdout for non-blocking warnings.
- Do NOT use `exit 2` in non-blocking hook types (PostToolUse, SessionStart, Notification, PreCompact, InstructionsLoaded)
  WHY: Non-blocking hooks cannot block operations regardless of exit code. Exit 2 from these hooks is a confusing no-op. Always use exit 0 for non-blocking hooks, even on errors (fail-open).
- Do NOT skip testing hooks before installation
  WHY: An untested blocking hook can lock out all tool use, requiring manual settings.json editing to recover.
- Do NOT put slow operations (network calls, large file scans) in PreToolUse hooks
  WHY: PreToolUse runs before every tool call. A 2-second hook on every edit destroys productivity.
- Do NOT hardcode absolute paths in hook scripts meant for team sharing
  WHY: Breaks on other machines. Use relative paths from project root or `$HOME`.

## Resources

### Reference docs (load on demand)
- `references/hook_types.md` -- All 8 hook types: use cases, data, environment variables, blocking
- `references/security_patterns.md` -- Dangerous patterns, file validation, path normalization
- `references/hook_examples.md` -- 10+ complete working implementations
- `references/troubleshooting.md` -- Common issues, debugging, performance optimization

### Templates
- `assets/templates/pre_tool_use_template.py` -- Security validation
- `assets/templates/post_tool_use_template.py` -- Auto-formatting/linting
- `assets/templates/session_start_template.py` -- Context initialization
- `assets/templates/stop_template.py` -- Completion validation
- `assets/templates/simple_hooks.md` -- Inline hook examples (no scripts)
- `assets/test_hooks.py` -- Automated pytest framework

### External docs
- https://docs.claude.com/en/docs/claude-code/hooks
- https://docs.claude.com/en/docs/claude-code/hooks-guide
