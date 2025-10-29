---
name: branch-synchronizer
description: This skill should be used to synchronize branches with main via intelligent rebase. Handles conflict detection, auto-stash uncommitted changes, and supports project-agnostic workflows. Use when branches need updating before PRs, testing, or resuming work.
allowed_tools: Bash(./.claude/skills/branch-synchronizer/scripts/sync-branch.zsh *), Bash(jq:*)
---

# Branch Synchronizer Skill

Intelligent branch synchronization with conflict-aware rebasing.

## Overview

Provides safe, intelligent branch synchronization and rebasing operations. Handles fetching remote changes, rebasing onto main, and managing conflicts with context-aware strategies.

**Project-agnostic** - works with any git repository. Uses ticket patterns from `jira-analyzer.json` for intelligent branch discovery.

## When to Use This Skill

Use when:
- Updating feature branches before creating pull requests
- Rebasing with automatic conflict handling
- Finding and syncing ticket-based branches (PROJ-*, PROJ-*, PROJ-*)
- Preventing merge conflicts by staying current with main
- Resuming work on stale branches

## When Claude Code Should Invoke This Skill

Invoke proactively when user:
- Mentions branch is "behind", "out of date", or "needs updating"
- Asks to "update", "sync", "rebase", or "catch up" branch
- Runs tests in feature branch (sync first)
- Creates pull requests (sync first)
- Resumes work on stale tickets
- Asks if branch is current

**Example phrases:** "update my branch", "sync with main", "is my branch current?", "catch up with main", "rebase onto main"

**Proactive suggestions:** Before operations that benefit from synced branches, suggest syncing:
- "Branch may be behind main - sync first?"
- "This branch is 3 days old - sync with main first?"

## Quick Start

```zsh
# Sync current branch
./.claude/skills/branch-synchronizer/scripts/sync-branch.zsh

# Sync specific worktree
./.claude/skills/branch-synchronizer/scripts/sync-branch.zsh --path /path/to/worktree

# Find and sync by ticket number
./.claude/skills/branch-synchronizer/scripts/sync-branch.zsh --pattern PROJ-123
```

**Configuration:** Uses ticket prefixes from `.jira-analyzer.json` (project root) or `~/.jira-analyzer.json` (global). Only `prefixes` array needed - no authentication required.

**Advanced examples:** See [usage-guide.md](./references/usage-guide.md) for custom base branches, agent mode, and workflows.

## Features

### Smart Synchronization
- Fetch latest from remote branches and main
- Auto-stash uncommitted changes before rebase
- Rebase feature branch onto latest main
- Detect and handle conflicts based on execution mode
- Auto-restore stashed changes after successful rebase

### Conflict Handling
Adapts based on execution context:
- **Agent Mode:** Auto-abort, restore original state, return exit code 1
- **Interactive Mode:** Guide through resolution, provide helpful commands, support continuation

### Branch Discovery
- Find branches by ticket pattern (PROJ-123, PROJ-456)
- Detect if branch already merged to main
- Handle multiple matching branches (selects most recent)

### Safety Features
- Never auto-push (requires manual review)
- Preserve uncommitted changes with auto-stash
- Validate branch existence before operations

## Claude Code Integration

Invoke automatically when synchronization needed. The skill handles:
- Finding branches by ticket pattern
- Syncing current or specified branches
- Adapting conflict handling to execution context (agent vs interactive)

**Example invocation:**
```bash
# By pattern
./.claude/skills/branch-synchronizer/scripts/sync-branch.zsh --pattern PROJ-456

# By path
./.claude/skills/branch-synchronizer/scripts/sync-branch.zsh --path /path/to/worktree
```

**Conflict handling:** Agent mode auto-aborts on conflicts (exit code 1). Interactive mode guides user through resolution. See [integration-guide.md](./references/integration-guide.md) for detailed scenarios.

## Script Reference

Main options for `sync-branch.zsh`:
- `--path PATH` - Repository or worktree path
- `--branch BRANCH` - Specific branch to sync
- `--pattern PATTERN` - Find branch by ticket pattern
- `--base-branch BRANCH` - Base branch (default: main)
- `--status` - Show sync status as JSON (no sync)

**Exit codes:** 0 = success, 1 = conflicts/errors

Complete API documentation: [api-reference.md](./references/api-reference.md)

## Integration

Integrates with other skills (git-worktree-tools, jira-context-fetcher), CI/CD pipelines, git hooks, and IDEs.

Comprehensive integration patterns: [integration-guide.md](./references/integration-guide.md)

## Reference Documentation

Load reference documents as needed:

| User Need | Document | Example Questions |
|-----------|----------|-------------------|
| Usage examples | [usage-guide.md](./references/usage-guide.md) | "How do I sync?", "Show examples" |
| Troubleshooting | [troubleshooting.md](./references/troubleshooting.md) | "Got an error", "Sync failed" |
| Integration | [integration-guide.md](./references/integration-guide.md) | "Use in CI?", "Add to git hooks?" |
| API details | [api-reference.md](./references/api-reference.md) | "Parameters?", "JSON output?" |

## See Also

**Reference Documentation:**
- [usage-guide.md](./references/usage-guide.md) - Comprehensive usage examples and workflows
- [api-reference.md](./references/api-reference.md) - Complete script API and JSON output format
- [integration-guide.md](./references/integration-guide.md) - Integration patterns for CI/CD, hooks, and IDEs
- [troubleshooting.md](./references/troubleshooting.md) - Common issues and solutions

**Related Skills:**
- [git-worktree-tools](../git-worktree-tools/) - Git worktree lifecycle management
- [git-operations](../git-operations/) - Safe git operations
- [jira-context-fetcher](../jira-context-fetcher/) - JIRA ticket context gathering
