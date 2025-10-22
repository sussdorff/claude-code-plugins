---
name: git-worktree-tools
description: Manages git worktree lifecycle - create, validate, remove, sync configuration files. Use when creating isolated workspaces for tickets or features without affecting main repository. Project-aware configuration syncing keeps worktrees in sync with main repo.
allowed_tools: Bash(./.claude/skills/git-worktree-tools/scripts/*.zsh *), Bash(jq:*)
---

# Git Worktree Tools

Provides git worktree lifecycle management with project-aware configuration syncing. Create isolated workspaces for tickets or features while keeping project configurations synchronized with the main repository.

## Overview

Git worktrees allow you to have multiple working trees from a single repository. This skill provides tools to:
- Create worktrees with automatic branch handling
- Validate worktree state
- Remove and clean up worktrees
- Sync project configurations (`.claude/`, `CLAUDE.local.md`, `.env`)
- Extract ticket numbers from branch names

**Key Design**: All operations run from outside the worktree directory (black box approach) to avoid permission issues and maintain clear separation between main repository and worktrees.

## When to Use This Skill

Use this skill when:
- Creating isolated workspaces for ticket development
- Working on multiple tickets/features simultaneously
- Keeping worktree configurations in sync with main repository
- Validating existing worktree state before resuming work
- Cleaning up completed or abandoned worktrees
- Extracting ticket information from branch names

**Integration**: Designed to be called by ticket-manager agents or other workflow automation, but can be used standalone.

## Quick Start

```bash
# Create a worktree
.claude/skills/git-worktree-tools/scripts/create-worktree.zsh --name=PROJ-123

# Validate and sync
.claude/skills/git-worktree-tools/scripts/validate-worktree.zsh --name=PROJ-123
.claude/skills/git-worktree-tools/scripts/sync-configs.zsh --name=PROJ-123

# Remove when done
.claude/skills/git-worktree-tools/scripts/remove-worktree.zsh --name=PROJ-123
```

Worktrees are created in `${PROJECT_ROOT}.worktrees/${NAME}/` as sibling directories to the main repository.

## Common Workflow Example

```bash
# 1. Create worktree for new ticket
CREATE_RESULT=$(.claude/skills/git-worktree-tools/scripts/create-worktree.zsh --name=PROJ-123)
WORKTREE_PATH=$(echo "$CREATE_RESULT" | jq -r '.path')
echo "Created worktree at: $WORKTREE_PATH"

# 2. Later: Resume work (validate and sync)
if .claude/skills/git-worktree-tools/scripts/validate-worktree.zsh --name=PROJ-123 --quiet; then
    echo "Worktree exists, syncing configurations..."
    .claude/skills/git-worktree-tools/scripts/sync-configs.zsh --name=PROJ-123
else
    echo "Worktree invalid or missing, recreating..."
    .claude/skills/git-worktree-tools/scripts/create-worktree.zsh --name=PROJ-123
fi

# 3. Clean up when done
.claude/skills/git-worktree-tools/scripts/remove-worktree.zsh --name=PROJ-123
```

For comprehensive workflows, integration patterns, and detailed examples, see [Usage Guide](references/usage-guide.md).

## Scripts

### create-worktree.zsh

Create a new git worktree and sync project configurations.

```bash
create-worktree.zsh --name=NAME [--branch=BRANCH] [--base-branch=BASE] [--skip-sync]
```

Creates worktree directory at `${PROJECT}.worktrees/${NAME}/`, handles branch creation/checkout, and syncs configurations (`.claude/`, `CLAUDE.local.md`, `.env`). Returns JSON with worktree info including extracted ticket number.

See [Usage Guide - create-worktree.zsh](references/usage-guide.md#create-worktreezsh-examples) for detailed parameters, examples, and behavior.

### validate-worktree.zsh

Check if a worktree exists and is valid.

```bash
validate-worktree.zsh --name=NAME [--quiet]
```

Returns JSON with status (`VALID`, `INVALID`, or `NOT_FOUND`). Exit code 0 if valid, 1 otherwise. Use `--quiet` for scripting.

See [Usage Guide - validate-worktree.zsh](references/usage-guide.md#validate-worktreezsh-examples) for detailed parameters and status values.

### remove-worktree.zsh

Remove a git worktree and clean up its directory.

```bash
remove-worktree.zsh --name=NAME [--force]
```

Removes worktree using `git worktree remove`, with fallback to directory removal. Checks for uncommitted changes unless `--force` is specified. Handles both valid and invalid worktrees.

See [Usage Guide - remove-worktree.zsh](references/usage-guide.md#remove-worktreezsh-examples) for detailed parameters and examples.

### sync-configs.zsh

Sync project configurations from main repository to worktree.

```bash
sync-configs.zsh --name=NAME [--worktree-path=PATH]
```

Syncs `.claude/` (using rsync), `CLAUDE.local.md`, and `.env` from main repository to worktree. Returns JSON with synced file details.

See [Usage Guide - sync-configs.zsh](references/usage-guide.md#sync-configszsh-examples) for detailed parameters and sync strategy.

## Library Functions

**When to use library functions:** Load these functions when building custom scripts, complex integrations, or when the provided scripts don't cover a specific use case. For standard worktree workflows (create, validate, sync, remove), use the provided scripts directly without loading library code into context.

### worktree-functions.zsh

Core worktree operations:

```zsh
check_worktree_status()      # Returns VALID:path, INVALID:path, NOT_FOUND
get_worktree_base()          # Calculate worktree base from project root
detect_git_root()            # Find git repository root
get_worktree_branch()        # Get current branch from worktree
list_worktrees()             # List all worktrees as JSON array
check_branch_exists()        # Check if branch exists (local/remote/both/none)
validate_worktree_inputs()   # Validate name and project root
```

### config-sync.zsh

Configuration synchronization:

```zsh
sync_claude_directory()      # Sync .claude/ with rsync
sync_config_file()           # Sync single config file
sync_all_configs()           # Sync all project configs
verify_sync()                # Verify sync completed
list_config_files()          # List available config files
```

### branch-utils.zsh

Branch name parsing and ticket extraction:

```zsh
extract_ticket_number()      # Extract ticket from branch name
parse_branch_name()          # Parse branch into components (JSON)
validate_branch_name()       # Validate branch name format
generate_branch_name()       # Generate branch name from ticket/description
has_ticket_number()          # Check if branch contains ticket
extract_project_prefix()     # Extract project prefix from ticket
list_ticket_patterns()       # Show supported ticket patterns
```

## Ticket Extraction

The skill automatically extracts ticket numbers from branch names using pattern matching.

**Supported Patterns:**
- `PROJ-123` - Atlassian Cloud (Project A)
- `PROJ-456` - Atlassian Cloud (Project B)
- `PROJ-789` - Self-hosted JIRA
- `PROJ-456` - Generic projects
- `ABC123-789` - Projects with numbers in prefix

**Branch Examples:**
```bash
feature/PROJ-123/add-feature     → Ticket: PROJ-123
bugfix/PROJ-456/fix-issue        → Ticket: PROJ-456
feature/PROJ-789/new-work          → Ticket: PROJ-789
feature/no-ticket/description     → Ticket: (none)
```

## Integration with ticket-manager

This skill is designed to be called by a ticket-manager agent:

```bash
# Agent creates worktree for ticket
create-worktree.zsh --name=PROJ-123 --branch=feature/PROJ-123/fix-bug

# Agent validates before resuming work
if validate-worktree.zsh --name=PROJ-123 --quiet; then
    # Worktree exists, sync configs
    sync-configs.zsh --name=PROJ-123
fi

# Agent cleans up completed work
remove-worktree.zsh --name=PROJ-123
```

The agent handles:
- JIRA ticket data fetching
- Branch name generation from ticket summary
- Worktree lifecycle decisions
- User interaction

This skill handles:
- Git worktree operations
- Configuration synchronization
- Validation and cleanup

## Troubleshooting

### "Not in a git repository"
**Solution**: Specify `--project-root=/path/to/repo` or run from within repository

### "Worktree already exists"
**Validate first**: `validate-worktree.zsh --name=NAME`
**If invalid**: `remove-worktree.zsh --name=NAME --force` then recreate

### "Failed to sync .claude directory"
**Check permissions**: Ensure both source and target are writable
**Check rsync**: Verify `rsync` is installed

### "Branch name contains invalid characters"
**Git rules**: No spaces, ~, ^, :, ?, *, [, \, .., @{, //
**Fix**: Use `generate_branch_name()` function to sanitize

### Uncommitted changes blocking removal
**Force removal**: Use `--force` flag
**Or commit first**: Save work before removing worktree

## Best Practices

1. **Name worktrees after tickets** for easy identification
2. **Sync configs regularly** when .claude/ changes in main repo
3. **Validate before resuming** work to catch invalid worktrees early
4. **Clean up completed work** to avoid clutter
5. **Use --force sparingly** only when you're sure about losing changes
6. **Let scripts handle paths** don't cd into worktrees manually

## Security Considerations

- Scripts never execute arbitrary user input
- All paths are validated before use
- No modifications inside worktree directories (black box approach)
- Config files are copied, not symlinked (isolation)
- Force operations require explicit flag

## See Also

- [Usage Guide](references/usage-guide.md) - Comprehensive examples and patterns
- [Git Worktree Documentation](https://git-scm.com/docs/git-worktree) - Official git worktree docs
