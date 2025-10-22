# Claude Code Hook Types Reference

This document provides comprehensive documentation of all 8 Claude Code hook types, their purposes, use cases, and when to use each one.

## Hook Event Lifecycle

```
SessionStart
    ↓
UserPromptSubmit → PreToolUse → [Tool Execution] → PostToolUse → Stop
    ↓                                                                ↓
Notification                                                   SubagentStop
    ↓
PreCompact → [Compaction]
```

## 1. SessionStart

**When it runs**: At the beginning of a Claude Code session, before any user interaction.

**Purpose**: Initialize session context, load environment-specific information, set up workspace state.

**Blocking capability**: Cannot block (informational only).

**Common use cases**:
- Load git status and recent commits
- Fetch recent GitHub/GitLab issues
- Set up development environment variables
- Load project-specific context files
- Initialize logging or monitoring

**Special features**:
- Has access to `CLAUDE_ENV_FILE` environment variable
- Can persist environment variables for subsequent bash commands
- Runs only once per session

**Example**:
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

## 2. UserPromptSubmit

**When it runs**: When a user submits a prompt, before Claude processes it.

**Purpose**: Validate, log, or transform user prompts before processing.

**Blocking capability**: Can block with exit code 2.

**Common use cases**:
- Log all user prompts for compliance/auditing
- Validate prompt content against policies
- Inject additional context into prompts
- Track prompt history
- Name or categorize agent tasks

**Available data**:
- User's submitted prompt text
- Session ID
- Transcript path

**Example**:
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/user_prompt_submit.py --log-only"
          }
        ]
      }
    ]
  }
}
```

## 3. PreToolUse

**When it runs**: After Claude creates tool parameters but before processing the tool call.

**Purpose**: Validate and potentially block tool executions based on security rules or business logic.

**Blocking capability**: Can block with exit code 2 or JSON response `"decision": "deny"`.

**Common use cases**:
- Block dangerous commands (rm -rf, chmod 777, sudo operations)
- Protect sensitive files (.env, credentials, private keys)
- Validate file paths before access
- Enforce security policies
- Prevent modifications to critical infrastructure

**Available data**:
- Tool name
- Tool parameters (file paths, commands, etc.)
- Session context

**JSON response format**:
```json
{
  "continue": false,
  "decision": "deny",
  "additionalContext": "Blocked: Attempt to access sensitive .env file"
}
```

**Security patterns**:
- Pattern matching for dangerous commands
- Path validation
- File access control
- Command sanitization

**Example**:
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

## 4. PostToolUse

**When it runs**: Immediately after a tool successfully completes execution.

**Purpose**: Process results, perform cleanup, trigger follow-up actions, or transform output.

**Blocking capability**: Cannot block (informational only).

**Common use cases**:
- Auto-format code after edits (prettier, black, gofmt)
- Run linters after file modifications
- Convert transcript formats
- Update metadata or indexes
- Trigger CI/CD workflows
- Log tool usage for auditing

**Available data**:
- Tool name
- Tool parameters
- Tool execution results

**Matcher patterns**:
```
Edit|Write          # Matches Edit OR Write tools
Edit:*.ts|Edit:*.tsx   # Matches TypeScript edits only
```

**Example - Auto-formatting**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write \"$file_path\""
          }
        ]
      }
    ]
  }
}
```

**Example - TypeScript type checking**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit:*.ts|Edit:*.tsx|Write:*.ts|Write:*.tsx",
        "hooks": [
          {
            "type": "command",
            "command": "npx tsc --noEmit"
          }
        ]
      }
    ]
  }
}
```

## 5. Notification

**When it runs**: When Claude Code sends a notification (e.g., waiting for user input).

**Purpose**: Handle notifications with custom alerts, logging, or integrations.

**Blocking capability**: Cannot block (informational only).

**Common use cases**:
- Desktop notifications (notify-send, osascript)
- Text-to-speech announcements
- Slack/Discord notifications
- Log notification events
- Trigger custom alert systems

**Example - macOS notification**:
```json
{
  "hooks": {
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
    ]
  }
}
```

## 6. Stop

**When it runs**: When Claude attempts to finish responding to the user.

**Purpose**: Validate task completion, enforce quality gates, or generate completion messages.

**Blocking capability**: Can block with exit code 2 to force Claude to continue.

**Common use cases**:
- Ensure tests pass before allowing completion
- Verify build succeeds
- Check that all TODOs are addressed
- Generate AI-powered completion summaries
- Validate deliverables meet requirements

**Advanced pattern**:
- Generate completion messages using LLM
- Force continuation if critical tasks incomplete
- Multi-LLM fallback (OpenAI → Anthropic → Ollama)

**Example - Ensure tests pass**:
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

## 7. SubagentStop

**When it runs**: When a subagent (Task tool) completes its work.

**Purpose**: Monitor subagent completion, log results, or trigger follow-up actions.

**Blocking capability**: Can block with exit code 2.

**Common use cases**:
- Log subagent task results
- Announce subagent completion with TTS
- Validate subagent output
- Trigger dependent workflows

**Example**:
```json
{
  "hooks": {
    "SubagentStop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/subagent_stop.py --notify"
          }
        ]
      }
    ]
  }
}
```

## 8. PreCompact

**When it runs**: Before Claude Code performs context compaction operations.

**Purpose**: Backup conversation state, log compaction events, or prepare for context reduction.

**Blocking capability**: Cannot block (informational only).

**Common use cases**:
- Backup transcripts before compaction
- Log compaction events for analysis
- Archive conversation state
- Generate summaries before compaction

**Example - Backup transcript**:
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

## Hook Execution Behavior

### Exit Codes
- `0`: Success; stdout shown in transcript mode
- `2`: Blocking error; stderr feeds back to Claude
- Other codes: Non-blocking errors displayed to users

### JSON Response Control
Hooks can return JSON to control execution:

```json
{
  "continue": false,           // Stop execution
  "decision": "deny",          // "allow", "deny", or "ask"
  "additionalContext": "..."   // Context injection for Claude
}
```

### Parallelization
All matching hooks for an event execute simultaneously.

### Timeout
Default 60-second timeout per command (configurable).

### Environment Variables
- `CLAUDE_PROJECT_DIR`: Current project directory
- `CLAUDE_ENV_FILE`: Path to environment file (SessionStart only)
- `CLAUDE_CODE_REMOTE`: Remote execution indicator
- Tool-specific variables (e.g., `file_path` for Edit/Write)

## Best Practices

1. **Choose the right hook**: Use PreToolUse for blocking/security, PostToolUse for automation
2. **Keep hooks fast**: Slow hooks degrade user experience
3. **Use matchers wisely**: Limit hooks to relevant tools/files to reduce overhead
4. **Test thoroughly**: Test hooks before deploying to production
5. **Handle errors gracefully**: Use try-catch and meaningful error messages
6. **Log for auditing**: Maintain audit trails for compliance
7. **Use UV for isolation**: Keep hook dependencies separate from project dependencies
