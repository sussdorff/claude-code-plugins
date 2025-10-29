# Scripts Directory

This directory is reserved for future helper scripts related to ZSH best practices.

## Code Review

The zsh-best-practices skill provides **intelligent code review** through the Claude Code agent, not through separate linting tools.

When you ask the agent to review ZSH scripts, it automatically checks for:
- Global variable leakage
- Arithmetic expression bugs with NO_UNSET
- Incorrect array operations
- Unquoted expansions
- Common Bash-to-ZSH migration issues

See [10-code-review-checklist.md](../references/10-code-review-checklist.md) for the complete checklist.

## Why No Linter?

We intentionally don't provide a separate linter because:

1. **Context matters** - The agent understands when a pattern is intentional
2. **Better explanations** - Not just "error on line 42", but WHY and HOW to fix
3. **Flexible** - Adapts to your codebase's conventions
4. **No maintenance burden** - No tool to install, update, or configure

Simply ask the agent to "review this ZSH script" and get intelligent, context-aware feedback.
