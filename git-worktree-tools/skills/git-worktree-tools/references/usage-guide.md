## Git Worktree Tools - Comprehensive Usage Guide

This guide provides detailed examples, patterns, and workflows for using the git-worktree-tools skill.

## Table of Contents

- [Common Workflows](#common-workflows)
- [Script Examples](#script-examples)
- [Library Function Examples](#library-function-examples)
- [Integration Patterns](#integration-patterns)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting Scenarios](#troubleshooting-scenarios)

## Common Workflows

### Workflow 1: New Ticket Development

**Scenario**: Starting work on a new JIRA ticket

```bash
# 1. Create worktree for ticket
CREATE_RESULT=$(./scripts/create-worktree.zsh --name=PROJ-123)

# Extract path from result
WORKTREE_PATH=$(echo "$CREATE_RESULT" | jq -r '.path')
BRANCH=$(echo "$CREATE_RESULT" | jq -r '.branch')

echo "Created worktree at: $WORKTREE_PATH"
echo "Branch: $BRANCH"

# 2. Do development work (in another process/editor)
# ...

# 3. When done, remove worktree
./scripts/remove-worktree.zsh --name=PROJ-123
```

### Workflow 2: Resuming Existing Work

**Scenario**: Resuming work on an existing ticket workspace

```bash
# 1. Validate worktree exists and is valid
if ! ./scripts/validate-worktree.zsh --name=PROJ-123 --quiet; then
    echo "Worktree is invalid or missing, recreating..."
    ./scripts/create-worktree.zsh --name=PROJ-123
fi

# 2. Sync configurations (in case .claude/ changed)
./scripts/sync-configs.zsh --name=PROJ-123

# 3. Extract worktree info
WORKTREE_INFO=$(./scripts/validate-worktree.zsh --name=PROJ-123)
WORKTREE_PATH=$(echo "$WORKTREE_INFO" | jq -r '.path')

echo "Resuming work at: $WORKTREE_PATH"
```

### Workflow 3: Multiple Parallel Tickets

**Scenario**: Working on multiple tickets simultaneously

```bash
# Create worktrees for multiple tickets
for ticket in PROJ-123 CH2-12346 PROJ-456; do
    echo "Creating worktree for $ticket..."
    ./scripts/create-worktree.zsh --name=$ticket
done

# List all worktrees (using library function)
source ./scripts/lib/worktree-functions.zsh
PROJECT_ROOT=$(detect_git_root)
list_worktrees "$PROJECT_ROOT" | jq '.'

# Sync all worktrees when .claude/ changes
for ticket in PROJ-123 CH2-12346 PROJ-456; do
    echo "Syncing $ticket..."
    ./scripts/sync-configs.zsh --name=$ticket
done
```

### Workflow 4: Cleanup Completed Work

**Scenario**: Clean up all merged/completed ticket worktrees

```bash
# List all worktrees
source ./scripts/lib/worktree-functions.zsh
PROJECT_ROOT=$(detect_git_root)
WORKTREES=$(list_worktrees "$PROJECT_ROOT")

# Extract ticket worktrees only (containing ticket patterns)
source ./scripts/lib/branch-utils.zsh
echo "$WORKTREES" | jq -r '.[].path' | while read -r path; do
    # Extract name from path
    name=$(basename "$path")

    # Check if it has a ticket number
    if [[ -n $(extract_ticket_number "$name" 2>/dev/null) ]]; then
        # Check if branch is merged (your logic here)
        # For now, just show what we found
        echo "Found ticket worktree: $name at $path"

        # To remove:
        # ./scripts/remove-worktree.zsh --name=$name
    fi
done
```

## Script Examples

### create-worktree.zsh Examples

#### Example 1: Basic Creation

```bash
# Simplest usage - creates worktree with auto-generated branch
./scripts/create-worktree.zsh --name=PROJ-123

# Output:
# {
#   "name": "PROJ-123",
#   "path": "/path/to/repo.worktrees/PROJ-123",
#   "branch": "feature/PROJ-123/new-work",
#   "ticket": "PROJ-123",
#   "project_root": "/path/to/repo",
#   "status": "created"
# }
```

#### Example 2: Custom Branch Name

```bash
# Specify exact branch to use
./scripts/create-worktree.zsh \
    --name=PROJ-123 \
    --branch=feature/PROJ-123/add-authentication

# Creates worktree and checks out that specific branch
```

#### Example 3: Different Base Branch

```bash
# Create from 'develop' instead of 'origin/main'
./scripts/create-worktree.zsh \
    --name=PROJ-123 \
    --base-branch=develop

# Useful for teams using git-flow or similar
```

#### Example 4: Non-Ticket Work

```bash
# Create worktree for general feature work (no ticket)
./scripts/create-worktree.zsh \
    --name=refactor-logging \
    --branch=feature/refactor-logging

# Output will have empty ticket field:
# {
#   "ticket": "",
#   ...
# }
```

#### Example 5: Skip Config Sync (Testing)

```bash
# Skip syncing .claude/, CLAUDE.local.md, .env
./scripts/create-worktree.zsh \
    --name=test-work \
    --skip-sync

# Useful for testing or temporary worktrees
```

### validate-worktree.zsh Examples

#### Example 1: Check if Valid

```bash
# Standard validation
./scripts/validate-worktree.zsh --name=PROJ-123

# Stderr output:
# ✅ Worktree is valid: /path/to/repo.worktrees/PROJ-123

# JSON output:
# {
#   "status": "VALID",
#   "exists": true,
#   "is_git_worktree": true,
#   ...
# }

# Exit code: 0
```

#### Example 2: Use in Conditionals

```bash
# Quiet mode for scripting
if ./scripts/validate-worktree.zsh --name=PROJ-123 --quiet; then
    echo "Worktree is ready for use"
else
    echo "Worktree needs to be created or fixed"
fi
```

#### Example 3: Extract Information

```bash
# Get worktree details
WORKTREE_INFO=$(./scripts/validate-worktree.zsh --name=PROJ-123 --quiet)

# Extract specific fields
PATH=$(echo "$WORKTREE_INFO" | jq -r '.path')
BRANCH=$(echo "$WORKTREE_INFO" | jq -r '.branch')
TICKET=$(echo "$WORKTREE_INFO" | jq -r '.ticket')

echo "Working on ticket $TICKET"
echo "Location: $PATH"
echo "Branch: $BRANCH"
```

#### Example 4: Validation States

```bash
# NOT_FOUND state
./scripts/validate-worktree.zsh --name=nonexistent
# {"status": "NOT_FOUND", "exists": false, ...}
# Exit code: 1

# INVALID state (directory exists but not a git worktree)
# This happens if directory was created manually or git worktree was corrupted
./scripts/validate-worktree.zsh --name=broken
# {"status": "INVALID", "exists": true, "is_git_worktree": false, ...}
# Exit code: 1
```

### remove-worktree.zsh Examples

#### Example 1: Standard Removal

```bash
# Remove worktree (checks for uncommitted changes)
./scripts/remove-worktree.zsh --name=PROJ-123

# If there are uncommitted changes:
# Error: Worktree has uncommitted changes
# Use --force to remove anyway
```

#### Example 2: Force Removal

```bash
# Remove even with uncommitted changes
./scripts/remove-worktree.zsh --name=PROJ-123 --force

# Output:
# {
#   "name": "PROJ-123",
#   "path": "/path/to/repo.worktrees/PROJ-123",
#   "status": "removed"
# }
```

#### Example 3: Remove Invalid Worktree

```bash
# If worktree is invalid (directory exists but not in git worktree list)
./scripts/remove-worktree.zsh --name=broken-worktree

# Stderr:
# → Found invalid worktree directory at: /path/to/broken-worktree
# → Cleaning up directory...
# ✅ Invalid worktree directory cleaned up
```

### sync-configs.zsh Examples

#### Example 1: Sync by Name

```bash
# Sync configurations for a worktree
./scripts/sync-configs.zsh --name=PROJ-123

# Output:
# {
#   "name": "PROJ-123",
#   "path": "/path/to/repo.worktrees/PROJ-123",
#   "status": "success",
#   "synced_configs": [
#     {"path": ".claude/", "type": "directory", "file_count": 15},
#     {"path": "CLAUDE.local.md", "type": "file"},
#     {"path": ".env", "type": "file"}
#   ]
# }
```

#### Example 2: Sync by Path

```bash
# Sync using direct path (useful when name is unknown)
./scripts/sync-configs.zsh \
    --worktree-path=/path/to/repo.worktrees/PROJ-123

# Same output as Example 1
```

#### Example 3: Sync After Configuration Changes

```bash
# Workflow: Update .claude/ in main repo, then sync all worktrees

# 1. Update .claude/ in main repo
echo "new config" > .claude/settings.json

# 2. Find all worktrees and sync
source ./scripts/lib/worktree-functions.zsh
PROJECT_ROOT=$(detect_git_root)
WORKTREES=$(list_worktrees "$PROJECT_ROOT")

# 3. Sync each one
echo "$WORKTREES" | jq -r '.[].path' | while read -r path; do
    name=$(basename "$path")
    echo "Syncing $name..."
    ./scripts/sync-configs.zsh --name=$name
done
```

## Library Function Examples

### worktree-functions.zsh Examples

#### Example 1: Check Worktree Status

```zsh
source ./scripts/lib/worktree-functions.zsh

# Check status
STATUS=$(check_worktree_status "PROJ-123" "/path/to/repo")
echo "$STATUS"  # Output: "VALID:/path/to/repo.worktrees/PROJ-123"

# Extract status type
STATUS_TYPE="${STATUS%%:*}"
WORKTREE_PATH="${STATUS#*:}"

case "$STATUS_TYPE" in
    "VALID")
        echo "Worktree is valid at $WORKTREE_PATH"
        ;;
    "INVALID")
        echo "Worktree directory exists but is invalid"
        ;;
    "NOT_FOUND")
        echo "Worktree not found"
        ;;
esac
```

#### Example 2: List All Worktrees

```zsh
source ./scripts/lib/worktree-functions.zsh

PROJECT_ROOT=$(detect_git_root)
WORKTREES=$(list_worktrees "$PROJECT_ROOT")

# Pretty print
echo "$WORKTREES" | jq '.[]'

# Count worktrees
WORKTREE_COUNT=$(echo "$WORKTREES" | jq 'length')
echo "Total worktrees: $WORKTREE_COUNT"

# Filter to specific pattern
echo "$WORKTREES" | jq '.[] | select(.branch | contains("CH2"))'
```

#### Example 3: Check Branch Existence

```zsh
source ./scripts/lib/worktree-functions.zsh

PROJECT_ROOT=$(detect_git_root)
BRANCH="feature/PROJ-123/add-feature"

BRANCH_STATUS=$(check_branch_exists "$PROJECT_ROOT" "$BRANCH")

case "$BRANCH_STATUS" in
    "both")
        echo "Branch exists both locally and remotely"
        ;;
    "local")
        echo "Branch exists only locally"
        ;;
    "remote")
        echo "Branch exists only remotely"
        ;;
    "none")
        echo "Branch does not exist"
        ;;
esac
```

### config-sync.zsh Examples

#### Example 1: Sync Individual Components

```zsh
source ./scripts/lib/config-sync.zsh

PROJECT_ROOT="/path/to/repo"
WORKTREE_PATH="/path/to/repo.worktrees/PROJ-123"

# Sync only .claude directory
sync_claude_directory "$PROJECT_ROOT" "$WORKTREE_PATH"

# Sync only CLAUDE.local.md
sync_config_file "CLAUDE.local.md" "$PROJECT_ROOT" "$WORKTREE_PATH"

# Sync only .env
sync_config_file ".env" "$PROJECT_ROOT" "$WORKTREE_PATH"
```

#### Example 2: List Available Configs

```zsh
source ./scripts/lib/config-sync.zsh

PROJECT_ROOT=$(detect_git_root)
CONFIGS=$(list_config_files "$PROJECT_ROOT")

echo "$CONFIGS" | jq '.'

# Output:
# [
#   {"path": ".claude/", "type": "directory", "file_count": 15},
#   {"path": "CLAUDE.local.md", "type": "file"},
#   {"path": ".env", "type": "file"}
# ]
```

### branch-utils.zsh Examples

#### Example 1: Extract Ticket Number

```zsh
source ./scripts/lib/branch-utils.zsh

# Various branch formats
extract_ticket_number "feature/PROJ-123/add-feature"     # Output: PROJ-123
extract_ticket_number "bugfix/PROJ-456/fix-bug"         # Output: PROJ-456
extract_ticket_number "PROJ-789-hotfix"                   # Output: PROJ-789
extract_ticket_number "feature/no-ticket-here"           # No output, exit code 1
```

#### Example 2: Parse Branch Name

```zsh
source ./scripts/lib/branch-utils.zsh

BRANCH="feature/PROJ-123/add-authentication"
PARSED=$(parse_branch_name "$BRANCH")

echo "$PARSED" | jq '.'

# Output:
# {
#   "branch": "feature/PROJ-123/add-authentication",
#   "type": "feature",
#   "ticket": "PROJ-123",
#   "description": "add-authentication"
# }
```

#### Example 3: Generate Branch Name

```zsh
source ./scripts/lib/branch-utils.zsh

# With ticket
BRANCH=$(generate_branch_name "PROJ-123" "Add User Authentication System")
echo "$BRANCH"  # feature/PROJ-123/add-user-authentication-system

# Without ticket
BRANCH=$(generate_branch_name "" "Refactor Database Layer")
echo "$BRANCH"  # feature/refactor-database-layer
```

#### Example 4: Validate Branch Name

```zsh
source ./scripts/lib/branch-utils.zsh

# Valid names
validate_branch_name "feature/PROJ-123/add-feature"    # Exit 0
validate_branch_name "bugfix/fix-issue"                  # Exit 0

# Invalid names
validate_branch_name "feature with spaces"               # Exit 1, error message
validate_branch_name "feature/has:colon"                 # Exit 1, error message
validate_branch_name "/starts-with-slash"                # Exit 1, error message
```

## Integration Patterns

### Pattern 1: ticket-manager Agent Integration

```zsh
#!/usr/bin/env zsh
# ticket-manager agent calling git-worktree-tools

TICKET="PROJ-123"
BRANCH="feature/PROJ-123/fix-authentication-bug"

# 1. Check if worktree exists
if ! .claude/skills/git-worktree-tools/scripts/validate-worktree.zsh \
    --name=$TICKET --quiet; then

    # 2. Create worktree
    echo "Creating worktree for $TICKET..."
    CREATE_RESULT=$(.claude/skills/git-worktree-tools/scripts/create-worktree.zsh \
        --name=$TICKET \
        --branch=$BRANCH)

    WORKTREE_PATH=$(echo "$CREATE_RESULT" | jq -r '.path')
    echo "Created worktree at: $WORKTREE_PATH"
else
    # 3. Worktree exists, sync configs
    echo "Worktree exists, syncing configurations..."
    .claude/skills/git-worktree-tools/scripts/sync-configs.zsh --name=$TICKET

    WORKTREE_INFO=$(.claude/skills/git-worktree-tools/scripts/validate-worktree.zsh \
        --name=$TICKET --quiet)
    WORKTREE_PATH=$(echo "$WORKTREE_INFO" | jq -r '.path')
fi

echo "Ready to work at: $WORKTREE_PATH"
```

### Pattern 2: Cleanup Script

```zsh
#!/usr/bin/env zsh
# Cleanup merged ticket worktrees

source .claude/skills/git-worktree-tools/scripts/lib/worktree-functions.zsh
source .claude/skills/git-worktree-tools/scripts/lib/branch-utils.zsh

PROJECT_ROOT=$(detect_git_root)
WORKTREES=$(list_worktrees "$PROJECT_ROOT")

# Check each worktree
echo "$WORKTREES" | jq -r '.[] | @json' | while IFS= read -r wt; do
    BRANCH=$(echo "$wt" | jq -r '.branch')
    PATH=$(echo "$wt" | jq -r '.path')
    NAME=$(basename "$PATH")

    # Skip main worktree
    if [[ "$PATH" == "$PROJECT_ROOT" ]]; then
        continue
    fi

    # Check if branch is merged into main
    git -C "$PROJECT_ROOT" fetch origin main >/dev/null 2>&1

    if git -C "$PROJECT_ROOT" branch --merged origin/main | grep -q "$BRANCH"; then
        echo "Branch $BRANCH is merged, removing worktree $NAME..."
        .claude/skills/git-worktree-tools/scripts/remove-worktree.zsh \
            --name=$NAME --force
    else
        echo "Branch $BRANCH not merged, keeping worktree"
    fi
done
```

### Pattern 3: Configuration Syncer

```zsh
#!/usr/bin/env zsh
# Sync all worktrees after updating .claude/ in main repo

source .claude/skills/git-worktree-tools/scripts/lib/worktree-functions.zsh

PROJECT_ROOT=$(detect_git_root)
WORKTREES=$(list_worktrees "$PROJECT_ROOT")

echo "Syncing configurations to all worktrees..."

echo "$WORKTREES" | jq -r '.[].path' | while read -r path; do
    # Skip main worktree
    if [[ "$path" == "$PROJECT_ROOT" ]]; then
        continue
    fi

    NAME=$(basename "$path")
    echo "  → Syncing $NAME..."

    .claude/skills/git-worktree-tools/scripts/sync-configs.zsh \
        --name=$NAME --quiet
done

echo "✅ All worktrees synced"
```

## Advanced Usage

### Using with Different Git Workflows

#### Git Flow

```bash
# Create worktree from develop branch
./scripts/create-worktree.zsh \
    --name=PROJ-123 \
    --base-branch=develop

# Create hotfix worktree from main
./scripts/create-worktree.zsh \
    --name=hotfix-critical \
    --branch=hotfix/fix-security-issue \
    --base-branch=origin/main
```

#### Trunk-Based Development

```bash
# All feature branches from main
./scripts/create-worktree.zsh \
    --name=PROJ-123 \
    --base-branch=origin/main

# Short-lived feature branches
./scripts/create-worktree.zsh \
    --name=quick-fix \
    --branch=fix/quick-bugfix
```

### Custom Worktree Locations

```bash
# The worktree base is calculated as ${PROJECT_ROOT}.worktrees/
# To use a different location, symlink the .worktrees directory:

ln -s /path/to/custom/worktrees /path/to/project.worktrees

# Now all worktrees will be created in the custom location
```

### Batch Operations

```bash
# Create multiple worktrees from a list
TICKETS=(PROJ-123 CH2-12346 PROJ-456 PROJ-789)

for ticket in "${TICKETS[@]}"; do
    echo "Creating worktree for $ticket..."
    ./scripts/create-worktree.zsh --name=$ticket || {
        echo "Failed to create $ticket" >&2
    }
done

# Sync all at once
for ticket in "${TICKETS[@]}"; do
    ./scripts/sync-configs.zsh --name=$ticket
done
```

## Troubleshooting Scenarios

### Scenario 1: Worktree Directory Exists But Invalid

**Problem**: Directory exists but git doesn't recognize it as a worktree

```bash
# Validate shows INVALID
./scripts/validate-worktree.zsh --name=PROJ-123
# {"status": "INVALID", ...}

# Solution: Force remove and recreate
./scripts/remove-worktree.zsh --name=PROJ-123 --force
./scripts/create-worktree.zsh --name=PROJ-123
```

### Scenario 2: Permission Denied on Config Sync

**Problem**: Cannot sync .claude/ directory due to permissions

```bash
# Check permissions in main repo
ls -la .claude/

# Fix permissions
chmod -R u+rw .claude/

# Try sync again
./scripts/sync-configs.zsh --name=PROJ-123
```

### Scenario 3: Branch Name Conflicts

**Problem**: Want to create worktree but branch name already taken

```bash
# Check branch status
source ./scripts/lib/worktree-functions.zsh
PROJECT_ROOT=$(detect_git_root)
check_branch_exists "$PROJECT_ROOT" "feature/PROJ-123/old-name"

# Create with different branch name
./scripts/create-worktree.zsh \
    --name=PROJ-123 \
    --branch=feature/PROJ-123/new-approach
```

### Scenario 4: Recovering from Corrupted Worktree

**Problem**: Git worktree is corrupted or in inconsistent state

```bash
# 1. Try normal remove (may fail)
./scripts/remove-worktree.zsh --name=PROJ-123 --force

# 2. If that fails, manually remove from git
git worktree prune

# 3. Remove directory
rm -rf /path/to/repo.worktrees/PROJ-123

# 4. Recreate
./scripts/create-worktree.zsh --name=PROJ-123
```

### Scenario 5: Missing .claude/ Directory

**Problem**: Main repo doesn't have .claude/ directory yet

```bash
# Create it
mkdir -p .claude

# Add some config
echo "# Project settings" > .claude/README.md

# Now sync will work
./scripts/sync-configs.zsh --name=PROJ-123
```
