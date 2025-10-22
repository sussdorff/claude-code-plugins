# Branch Synchronizer - Usage Guide

Comprehensive guide for using the branch-synchronizer skill.

## Table of Contents

- [Quick Start](#quick-start)
- [Common Workflows](#common-workflows)
- [Advanced Usage](#advanced-usage)
- [Integration Examples](#integration-examples)
- [Configuration](#configuration)
- [jq Recipes](#jq-recipes)

## Quick Start

### Sync Current Branch

The simplest use case - sync the current branch in the current directory:

```zsh
cd /path/to/repo
./sync-branch.zsh
```

This will:
1. Fetch latest from origin
2. Pull any remote changes to your branch
3. Rebase onto main (or specified base branch)
4. Auto-stash uncommitted changes if needed

### Sync Specific Worktree

When working with git worktrees (common with ticket-manager):

```zsh
./sync-branch.zsh --path /repo/.worktrees/PROJ-123
```

### Find and Sync by Ticket

Let the script find the branch for you:

```zsh
./sync-branch.zsh --pattern PROJ-123
```

The script will:
1. Search for branches containing "PROJ-123"
2. Select the most recently updated branch if multiple exist
3. Sync that branch with main

## Common Workflows

### Daily Branch Maintenance

Keep your feature branches up-to-date with main:

```zsh
# Morning routine - sync all active worktrees
for worktree in /repo/.worktrees/*; do
  echo "Syncing $(basename $worktree)..."
  ./sync-branch.zsh --path "$worktree"
done
```

### Pre-Pull Request

Before creating a PR, ensure your branch is current:

```zsh
# Sync and check status
./sync-branch.zsh
./sync-branch.zsh --status

# If successful, create PR
if [ $? -eq 0 ]; then
  gh pr create --fill
fi
```

### Resume Work on Old Branch

When resuming work on a branch after days/weeks:

```zsh
# Find the branch
./sync-branch.zsh --pattern PROJ-456

# Review what changed in main
git log --oneline origin/main ^$(git merge-base HEAD origin/main)

# Continue work
```

### Multi-Branch Updates

Update all branches for a specific epic or feature:

```zsh
# Find all related branches
git branch -a | grep "CH2-1000" | while read branch; do
  branch=$(echo $branch | sed 's/remotes\/origin\///')
  ./sync-branch.zsh --branch "$branch"
done
```

## Advanced Usage

### Custom Base Branch

Working with develop or release branches:

```zsh
# Rebase onto develop
./sync-branch.zsh --base-branch develop

# Rebase onto release branch
./sync-branch.zsh --base-branch release/v2.0
```

### Agent Mode vs Interactive Mode

**Agent Mode** (called by automation):
```zsh
# Set environment variable to force agent mode
export BRANCH_SYNC_AGENT_MODE=true
./sync-branch.zsh --path /worktree

# Conflicts will abort automatically
# Exit code 1 indicates conflict or failure
```

**Interactive Mode** (manual use):
```zsh
# Unset agent mode for interactive guidance
unset BRANCH_SYNC_AGENT_MODE
./sync-branch.zsh

# Conflicts will show guided resolution
```

### Check Sync Status

See if a branch needs syncing without actually syncing:

```zsh
# Check current branch
./sync-branch.zsh --status

# Check specific worktree
./sync-branch.zsh --path /worktree --status

# Parse JSON output
./sync-branch.zsh --status | jq '.needs_sync'
```

### Conditional Sync

Only sync if behind main:

```zsh
if ./sync-branch.zsh --status | jq -e '.needs_sync == true' >/dev/null; then
  echo "Branch needs sync, updating..."
  ./sync-branch.zsh
else
  echo "Branch is up-to-date"
fi
```

## Integration Examples

### With ticket-manager

Integrate into ticket workspace creation:

```zsh
# In ticket-manager script
setup_workspace() {
  local ticket=$1
  local worktree=$2

  # Create worktree
  git worktree add "$worktree" ...

  # Sync the branch
  branch-synchronizer/scripts/sync-branch.zsh --path "$worktree"
}
```

### With CI/CD Pipeline

Pre-merge branch validation:

```yaml
# .gitlab-ci.yml
check-sync-status:
  script:
    - branch-synchronizer/scripts/sync-branch.zsh --status
    - |
      if [ $(./sync-branch.zsh --status | jq -r '.commits_behind') -gt 0 ]; then
        echo "Branch is behind main, please sync"
        exit 1
      fi
```

### With Pre-commit Hook

Ensure branch is current before committing:

```zsh
#!/usr/bin/env zsh
# .git/hooks/pre-commit

if branch-synchronizer/scripts/sync-branch.zsh --status | jq -e '.commits_behind > 10' >/dev/null; then
  echo "⚠️  Branch is >10 commits behind main"
  echo "Consider syncing: ./branch-synchronizer/scripts/sync-branch.zsh"
  # Don't block commit, just warn
fi
```

### With Claude Code Agent

Use in agent workflows:

```
User: "Sync my branch before testing"
Claude: [Invokes branch-synchronizer]
        ./sync-branch.zsh --path "$WORKTREE_PATH"

User: "Update all CH2-500 branches"
Claude: [Finds branches with pattern]
        ./sync-branch.zsh --pattern CH2-500
```

## Configuration

### jira-analyzer.json Setup

The skill uses ticket patterns from `jira-analyzer.json`:

**Project-local** (`.jira-analyzer.json` in repo root):
```json
{
  "instances": [
    {
      "name": "company-jira",
      "type": "cloud",
      "url": "https://company.atlassian.net",
      "prefixes": ["PROJ", "BUG", "FEAT"],
      "auth": {
        "email": "you@company.com",
        "token": "..."
      }
    }
  ]
}
```

**Global** (`~/.jira-analyzer.json`):
```json
{
  "instances": [
    {
      "name": "personal-jira",
      "prefixes": ["PERS"],
      "auth": { ... }
    },
    {
      "name": "work-jira",
      "prefixes": ["WORK", "TASK"],
      "auth": { ... }
    }
  ]
}
```

### Environment Variables

**BRANCH_SYNC_AGENT_MODE**:
- `true`: Force agent mode (abort on conflicts)
- `false` or unset: Interactive mode (guide resolution)

**BRANCH_SYNC_PATH_PROVIDED**:
- Set automatically when `--path` is used
- Helps detect agent vs interactive mode

## jq Recipes

### Check if Branch Needs Sync

```zsh
# Simple check
./sync-branch.zsh --status | jq -r '.needs_sync'

# Get commit count behind
./sync-branch.zsh --status | jq -r '.commits_behind'

# Conditional script
if ./sync-branch.zsh --status | jq -e '.needs_sync' >/dev/null; then
  echo "Sync needed"
fi
```

### Get Branch Information

```zsh
# Current branch name
./sync-branch.zsh --status | jq -r '.branch'

# Commits ahead of main
./sync-branch.zsh --status | jq -r '.commits_ahead'

# Has uncommitted changes
./sync-branch.zsh --status | jq -r '.has_uncommitted_changes'

# Has remote branch
./sync-branch.zsh --status | jq -r '.has_remote_branch'
```

### Format Status Report

```zsh
# Human-readable report
./sync-branch.zsh --status | jq -r '
  "Branch: \(.branch)",
  "Base: \(.base_branch)",
  "Ahead: \(.commits_ahead) commits",
  "Behind: \(.commits_behind) commits",
  "Uncommitted: \(.has_uncommitted_changes)",
  "Needs sync: \(.needs_sync)"
'

# Compact one-liner
./sync-branch.zsh --status | jq -r '
  "\(.branch): \(.commits_ahead) ahead, \(.commits_behind) behind"
'
```

### Find Branches Needing Sync

```zsh
# Check all worktrees
for worktree in /repo/.worktrees/*; do
  name=$(basename "$worktree")
  status=$(./sync-branch.zsh --path "$worktree" --status)
  behind=$(echo "$status" | jq -r '.commits_behind')

  if [ "$behind" -gt 0 ]; then
    echo "$name: $behind commits behind"
  fi
done
```

### Track Sync History

```zsh
# Log sync status to file
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  ./sync-branch.zsh --status
} | jq -s '{timestamp: .[0], status: .[1]}' >> .sync-history.jsonl

# Analyze sync patterns
cat .sync-history.jsonl | jq -r '
  select(.status.commits_behind > 5) |
  "\(.timestamp): \(.status.branch) was \(.status.commits_behind) behind"
'
```

## Conflict Resolution

### Interactive Conflict Resolution

When conflicts occur in interactive mode:

```
⚠️  Conflicts detected during rebase

Conflicting files:
    - src/file1.js
    - src/file2.js

To resolve:
  1. Edit conflicting files
  2. git add <resolved-files>
  3. git rebase --continue

Or to abort:
  git rebase --abort
```

**Step-by-step resolution:**

```zsh
# 1. Check conflicting files
git status

# 2. Open files and resolve conflicts
vim src/file1.js

# 3. Mark as resolved
git add src/file1.js src/file2.js

# 4. Continue rebase
git rebase --continue

# 5. If more conflicts, repeat 2-4
# 6. When done, push
git push --force-with-lease origin branch-name
```

### Agent Conflict Handling

When conflicts occur in agent mode:

```
⚠️  Rebase encountered conflicts - auto-aborting
ℹ️  Worktree left at original state

Manual resolution needed:
  cd /path/to/worktree
  git rebase origin/main
  # Resolve conflicts
  git rebase --continue
```

The agent aborts automatically and leaves the worktree clean.

## Performance Tips

### Reduce Fetch Overhead

If you've already fetched recently:

```zsh
# Fetch once
git fetch --all

# Then sync multiple branches (they'll reuse the fetch)
./sync-branch.zsh --pattern CH2-100
./sync-branch.zsh --pattern CH2-101
```

### Batch Operations

Sync multiple worktrees efficiently:

```zsh
# Parallel sync (careful with conflicts)
find /repo/.worktrees -maxdepth 1 -type d | \
  xargs -P 4 -I {} ./sync-branch.zsh --path {}

# Sequential with error handling
for worktree in /repo/.worktrees/*; do
  if ./sync-branch.zsh --path "$worktree"; then
    echo "✅ $(basename $worktree)"
  else
    echo "❌ $(basename $worktree) - manual review needed"
  fi
done
```

## Debugging

### Verbose Mode

Add debugging to library functions:

```zsh
# In sync-branch.zsh, add at top:
set -x  # Enable command tracing

# Or for specific function:
typeset -ft sync_and_rebase_branch  # Trace this function
```

### Check Library Loading

```zsh
# Verify all libraries load
zsh -n ./sync-branch.zsh
zsh -n ./lib/*.zsh

# Check for syntax errors
shellcheck ./sync-branch.zsh ./lib/*.zsh
```

### Test Configuration

```zsh
# Source config functions
source ./lib/config-functions.zsh

# Test pattern loading
load_ticket_patterns .
get_ticket_prefixes .
validate_ticket_pattern "PROJ-123" .
```

## See Also

- [SKILL.md](../SKILL.md) - Main skill documentation
- [troubleshooting.md](./troubleshooting.md) - Common issues and solutions
- [ticket-manager](../../charly-server-dev-tools/) - Ticket workspace orchestrator
