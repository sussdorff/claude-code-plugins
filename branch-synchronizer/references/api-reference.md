# Branch Synchronizer - API Reference

Complete reference for the branch-synchronizer script interface, exit codes, and library functions.

## Table of Contents

- [Main Script: sync-branch.zsh](#main-script-sync-branchzsh)
- [Exit Codes](#exit-codes)
- [Environment Variables](#environment-variables)
- [Library Functions](#library-functions)
- [JSON Output Format](#json-output-format)

## Main Script: sync-branch.zsh

Main entry point for branch synchronization operations.

### Synopsis

```zsh
sync-branch.zsh [OPTIONS]
```

### Description

Synchronize git branches with intelligent rebase and conflict handling. The script fetches latest changes from origin, pulls remote branch changes if available, and rebases the feature branch onto the base branch (default: main). Uncommitted changes are automatically stashed and restored.

### Options

#### `--path PATH`
Repository or worktree path to operate on.

- **Default**: Current directory
- **Type**: String (directory path)
- **Example**: `--path /repo/.worktrees/PROJ-123`
- **Notes**: When provided, sets `BRANCH_SYNC_PATH_PROVIDED=true` to help detect agent mode

#### `--branch BRANCH`
Specific branch name to synchronize.

- **Default**: Current branch (from `git branch --show-current`)
- **Type**: String (branch name)
- **Example**: `--branch feature/PROJ-123/fix-bug`
- **Notes**: Branch must exist locally or as a remote tracking branch

#### `--pattern PATTERN`
Find and synchronize branch matching a ticket pattern.

- **Default**: None
- **Type**: String (ticket identifier)
- **Example**: `--pattern PROJ-123`
- **Notes**:
  - Uses ticket prefixes from jira-analyzer.json
  - Checks if pattern already merged to main
  - Selects most recently updated branch if multiple matches
  - See "Branch Discovery" section for details

#### `--base-branch BRANCH`
Base branch to rebase onto.

- **Default**: `main`
- **Type**: String (branch name)
- **Example**: `--base-branch develop`
- **Notes**: Base branch must exist on origin

#### `--status`
Display sync status without performing synchronization.

- **Default**: `false`
- **Type**: Boolean flag
- **Example**: `--status`
- **Output**: JSON status object (see "JSON Output Format")

#### `-h, --help`
Display help message and exit.

### Examples

```zsh
# Sync current branch in current directory
sync-branch.zsh

# Sync specific worktree
sync-branch.zsh --path /repo/.worktrees/PROJ-123

# Find and sync ticket branch
sync-branch.zsh --pattern PROJ-123

# Sync with custom base branch
sync-branch.zsh --base-branch develop

# Check sync status (JSON output)
sync-branch.zsh --status

# Combine options
sync-branch.zsh --path /worktree --base-branch develop --status
```

### Behavior

When invoked, the script performs these operations in order:

1. **Validation**
   - Validate repository path exists
   - Check if path is a git repository
   - If pattern provided, find matching branch
   - Validate branch exists locally or remotely

2. **Status Mode** (if `--status` flag)
   - Display sync status as JSON
   - Exit without performing sync

3. **Pre-sync**
   - Switch to target branch if needed
   - Stash uncommitted changes if present

4. **Synchronization**
   - Fetch latest from origin
   - Pull remote branch changes (if remote exists)
   - Rebase onto base branch

5. **Post-sync**
   - Restore stashed changes
   - Display next steps
   - Show force-push warning if needed

### Execution Modes

The script adapts its behavior based on how it's invoked:

#### Agent Mode
Triggered when:
- `BRANCH_SYNC_AGENT_MODE=true` is set, OR
- `--path` parameter is provided (heuristic)

**Behavior:**
- Aborts automatically on conflicts
- Returns to original state
- Provides manual resolution instructions
- Exits with code 1

#### Interactive Mode
Triggered when:
- No explicit mode detection signals
- User runs script directly

**Behavior:**
- Guides user through conflict resolution
- Shows conflicting files
- Provides step-by-step instructions
- Waits for manual resolution

## Exit Codes

The script uses standard exit codes to indicate success or failure.

| Exit Code | Status | Description |
|-----------|--------|-------------|
| `0` | Success | Branch synchronized successfully |
| `1` | Failure | Conflicts encountered, validation failed, or errors occurred |

### Exit Code Details

**Exit 0 - Success scenarios:**
- Branch rebased onto base successfully
- No conflicts encountered
- Stashed changes restored (if any)
- Branch ready for review and push

**Exit 1 - Failure scenarios:**
- Repository path does not exist
- Not a git repository
- Pattern not found in jira-analyzer.json
- No branches found matching pattern
- Branch already merged to main
- Not on a branch (detached HEAD)
- Branch does not exist
- Rebase encountered conflicts
- Failed to fetch from origin
- Failed to restore stashed changes

### Exit Code Usage

```zsh
# Check if sync succeeded
if sync-branch.zsh --path /worktree; then
  echo "Sync successful"
  gh pr create
else
  echo "Sync failed - check for conflicts"
fi

# Capture exit code
sync-branch.zsh --pattern PROJ-123
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo "Ready to push"
fi
```

## Environment Variables

### `BRANCH_SYNC_AGENT_MODE`

Controls execution mode behavior.

- **Type**: String
- **Values**:
  - `"true"` - Force agent mode (auto-abort on conflicts)
  - `"false"` or unset - Allow interactive mode detection
- **Default**: Unset (uses heuristic detection)
- **Set by**: User or calling script
- **Example**:
  ```zsh
  export BRANCH_SYNC_AGENT_MODE=true
  sync-branch.zsh --path /worktree
  ```

### `BRANCH_SYNC_PATH_PROVIDED`

Internal flag indicating `--path` parameter was used.

- **Type**: String
- **Values**: `"true"` or unset
- **Default**: Unset
- **Set by**: Script automatically when `--path` is provided
- **Purpose**: Helps detect agent mode (path explicitly provided suggests automation)
- **Note**: This is an internal variable - users should not set it manually

## Library Functions

The script is organized into modular library files in `scripts/lib/`.

### config-functions.zsh

Configuration and pattern loading functions.

#### `load_ticket_patterns()`

Load JIRA ticket patterns from configuration file.

**Signature:**
```zsh
load_ticket_patterns [repo_path]
```

**Arguments:**
- `repo_path` - Repository path (default: current directory)

**Returns:**
- 0 on success
- 1 if config not found or invalid

**Side effects:**
- Sets internal variables with loaded patterns

#### `find_config_file()`

Locate jira-analyzer.json configuration file.

**Search order:**
1. Project-local: `$repo_path/.jira-analyzer.json`
2. Global: `~/.jira-analyzer.json`

**Signature:**
```zsh
find_config_file [repo_path]
```

**Arguments:**
- `repo_path` - Repository path (default: current directory)

**Output:**
- Prints path to config file if found
- Prints nothing if not found

**Returns:**
- 0 if config found
- 1 if config not found

#### `get_ticket_prefixes()`

Extract ticket prefixes from loaded configuration.

**Signature:**
```zsh
get_ticket_prefixes [repo_path]
```

**Arguments:**
- `repo_path` - Repository path (default: current directory)

**Output:**
- Prints space-separated list of prefixes

**Returns:**
- 0 on success
- 1 on failure

**Example:**
```zsh
prefixes=$(get_ticket_prefixes .)
# Output: "CH2 FALL CSC"
```

### sync-functions.zsh

Core synchronization and rebase logic.

#### `is_agent_mode()`

Detect if running in agent mode vs interactive mode.

**Signature:**
```zsh
is_agent_mode
```

**Returns:**
- 0 for agent mode
- 1 for interactive mode

**Detection logic:**
1. If `BRANCH_SYNC_AGENT_MODE` is set, use its value
2. If `BRANCH_SYNC_PATH_PROVIDED` is set, assume agent mode
3. Otherwise, default to interactive mode

#### `handle_rebase_conflict()`

Handle rebase conflicts based on execution mode.

**Signature:**
```zsh
handle_rebase_conflict worktree_dir
```

**Arguments:**
- `worktree_dir` - Path to repository/worktree

**Behavior:**
- **Agent mode**: Abort rebase, restore state, provide manual instructions
- **Interactive mode**: Display conflicting files, guide user through resolution

**Returns:**
- 0 in agent mode (aborted)
- 1 in interactive mode (needs manual resolution)

#### `stash_changes()`

Stash uncommitted changes before rebase.

**Signature:**
```zsh
stash_changes worktree_dir
```

**Arguments:**
- `worktree_dir` - Path to repository/worktree

**Returns:**
- 0 if changes were stashed
- 1 if nothing to stash

**Stash message:**
- `"branch-synchronizer auto-stash"`

#### `restore_changes()`

Restore previously stashed changes after rebase.

**Signature:**
```zsh
restore_changes worktree_dir
```

**Arguments:**
- `worktree_dir` - Path to repository/worktree

**Returns:**
- 0 if stash restored successfully
- 1 if restore failed (conflicts)

**Behavior:**
- Only restores stash with message "branch-synchronizer auto-stash"
- If restore fails, provides manual recovery instructions

#### `sync_and_rebase_branch()`

Main synchronization function - fetch, pull, and rebase.

**Signature:**
```zsh
sync_and_rebase_branch repo_path branch_name base_branch
```

**Arguments:**
- `repo_path` - Path to repository/worktree
- `branch_name` - Branch to synchronize
- `base_branch` - Base branch to rebase onto

**Returns:**
- 0 on successful sync
- 1 on failure (conflicts, fetch errors, etc.)

**Operations:**
1. Stash uncommitted changes if present
2. Fetch latest from origin
3. Pull remote branch changes (if exists)
4. Rebase onto base branch
5. Handle conflicts (mode-aware)
6. Restore stashed changes

#### `get_sync_status()`

Get synchronization status as JSON.

**Signature:**
```zsh
get_sync_status repo_path base_branch
```

**Arguments:**
- `repo_path` - Path to repository/worktree
- `base_branch` - Base branch to compare against

**Output:**
- JSON object with sync status (see "JSON Output Format")

**Returns:**
- Always 0

### branch-functions.zsh

Branch discovery and validation functions.

#### `find_ticket_branch()`

Find branch matching a ticket pattern.

**Signature:**
```zsh
find_ticket_branch pattern repo_path
```

**Arguments:**
- `pattern` - Ticket identifier (e.g., "PROJ-123")
- `repo_path` - Repository path

**Output:**
- Prints branch name if found
- Prints error message to stderr if not found

**Returns:**
- 0 if branch found
- 1 if not found or multiple found

**Behavior:**
- Searches local and remote branches
- Validates pattern against jira-analyzer.json prefixes
- If multiple matches, selects most recently updated
- Displays all matching branches before selection

#### `check_if_pattern_merged()`

Check if a ticket pattern has been merged to base branch.

**Signature:**
```zsh
check_if_pattern_merged pattern repo_path base_branch
```

**Arguments:**
- `pattern` - Ticket identifier
- `repo_path` - Repository path
- `base_branch` - Base branch to check

**Returns:**
- 0 if pattern merged (found in base branch history)
- 1 if not merged

#### `detect_existing_branches()`

Detect all branches matching a pattern.

**Signature:**
```zsh
detect_existing_branches pattern repo_path
```

**Arguments:**
- `pattern` - Search pattern
- `repo_path` - Repository path

**Output:**
- Prints list of matching branch names

**Returns:**
- 0 if branches found
- 1 if no branches found

## JSON Output Format

When invoked with `--status`, the script outputs JSON with sync status information.

### Status Object Schema

```json
{
  "branch": "string",
  "base_branch": "string",
  "current_commit": "string",
  "base_commit": "string",
  "commits_ahead": number,
  "commits_behind": number,
  "has_uncommitted_changes": boolean,
  "has_remote_branch": boolean,
  "needs_sync": boolean,
  "last_commit_date": "string (ISO 8601)",
  "last_commit_message": "string"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `branch` | string | Current branch name |
| `base_branch` | string | Base branch being compared against |
| `current_commit` | string | Current HEAD commit SHA |
| `base_commit` | string | Base branch HEAD commit SHA |
| `commits_ahead` | number | Commits ahead of base branch |
| `commits_behind` | number | Commits behind base branch |
| `has_uncommitted_changes` | boolean | Whether there are uncommitted changes |
| `has_remote_branch` | boolean | Whether branch exists on remote |
| `needs_sync` | boolean | Whether sync is recommended |
| `last_commit_date` | string | Date of last commit (ISO 8601 format) |
| `last_commit_message` | string | Subject of last commit |

### Example Output

```json
{
  "branch": "feature/PROJ-123/fix-bug",
  "base_branch": "main",
  "current_commit": "a1b2c3d4",
  "base_commit": "e5f6g7h8",
  "commits_ahead": 3,
  "commits_behind": 15,
  "has_uncommitted_changes": true,
  "has_remote_branch": true,
  "needs_sync": true,
  "last_commit_date": "2024-01-15T14:30:00Z",
  "last_commit_message": "Fix authentication bug"
}
```

### Processing JSON Output

#### Using jq

```zsh
# Check if sync needed
sync-branch.zsh --status | jq -r '.needs_sync'

# Get commits behind
sync-branch.zsh --status | jq -r '.commits_behind'

# Conditional sync
if sync-branch.zsh --status | jq -e '.needs_sync == true' >/dev/null; then
  sync-branch.zsh
fi

# Format human-readable report
sync-branch.zsh --status | jq -r '
  "Branch: \(.branch)",
  "Base: \(.base_branch)",
  "Ahead: \(.commits_ahead) commits",
  "Behind: \(.commits_behind) commits",
  "Needs sync: \(.needs_sync)"
'
```

#### In Shell Scripts

```zsh
# Parse JSON into variables
STATUS=$(sync-branch.zsh --status)
NEEDS_SYNC=$(echo "$STATUS" | jq -r '.needs_sync')
COMMITS_BEHIND=$(echo "$STATUS" | jq -r '.commits_behind')

if [ "$NEEDS_SYNC" = "true" ]; then
  echo "Branch is $COMMITS_BEHIND commits behind"
  sync-branch.zsh
fi
```

## See Also

- [SKILL.md](../SKILL.md) - Main skill documentation
- [usage-guide.md](./usage-guide.md) - Comprehensive usage examples
- [troubleshooting.md](./troubleshooting.md) - Common issues and solutions
- [integration-guide.md](./integration-guide.md) - Integration patterns
