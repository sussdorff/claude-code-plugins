#!/usr/bin/env zsh
# Branch Synchronizer - Intelligent branch sync with conflict-aware rebasing
# Part of solutio-claude-skills

# Reset to known ZSH defaults
emulate -LR zsh

# Enable strict error handling
setopt ERR_EXIT       # Exit on error
setopt ERR_RETURN     # Return on error in functions
setopt NO_UNSET       # Error on undefined variables
setopt PIPE_FAIL      # Fail if any command in pipeline fails

# Script directory (readonly constant)
typeset -r SCRIPT_DIR="${${(%):-%x}:A:h}"

# Load library functions
source "${SCRIPT_DIR}/lib/config-functions.zsh"
source "${SCRIPT_DIR}/lib/sync-functions.zsh"
source "${SCRIPT_DIR}/lib/branch-functions.zsh"

# Cleanup function
cleanup() {
    # Cleanup any temporary resources if needed
    # Currently no cleanup required, but prepared for future use
    :
}

# Register cleanup for all exit scenarios
trap cleanup EXIT INT TERM

# Default values (script-level variables - explicit global scope)
typeset -g repo_path=""
typeset -g branch_name=""
typeset -g pattern=""
typeset -g base_branch="main"
typeset -g show_status=false

# Usage function
usage() {
    cat << 'EOF'
Usage: sync-branch.zsh [OPTIONS]

Synchronize git branches with intelligent rebase and conflict handling.

Options:
  --path PATH              Repository or worktree path (default: current directory)
  --branch BRANCH          Specific branch to sync (default: current branch)
  --pattern PATTERN        Find branch by ticket pattern (e.g., PROJ-123)
  --base-branch BRANCH     Base branch to rebase onto (default: main)
  --status                 Show sync status without performing sync
  -h, --help              Show this help message

Examples:
  # Sync current branch in current directory
  sync-branch.zsh

  # Sync specific worktree
  sync-branch.zsh --path /repo/.worktrees/PROJ-123

  # Find and sync ticket branch
  sync-branch.zsh --pattern PROJ-123

  # Sync with custom base branch
  sync-branch.zsh --base-branch develop

  # Check sync status
  sync-branch.zsh --status

Exit Codes:
  0   Success - branch synchronized
  1   Failure - conflicts or errors

Environment Variables:
  BRANCH_SYNC_AGENT_MODE   Set to "true" to force agent mode (abort on conflicts)

Notes:
  - Uses ticket patterns from jira-analyzer.json for --pattern option
  - Never auto-pushes after rebase (manual review required)
  - Handles conflicts differently in agent vs interactive mode
EOF
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --path)
            repo_path="$2"
            export BRANCH_SYNC_PATH_PROVIDED=true
            shift 2
            ;;
        --path=*)
            repo_path="${1#*=}"
            export BRANCH_SYNC_PATH_PROVIDED=true
            shift
            ;;
        --branch)
            branch_name="$2"
            shift 2
            ;;
        --branch=*)
            branch_name="${1#*=}"
            shift
            ;;
        --pattern)
            pattern="$2"
            shift 2
            ;;
        --pattern=*)
            pattern="${1#*=}"
            shift
            ;;
        --base-branch)
            base_branch="$2"
            shift 2
            ;;
        --base-branch=*)
            base_branch="${1#*=}"
            shift
            ;;
        --status)
            show_status=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Determine repository path
if [[ -z "$repo_path" ]]; then
    repo_path=$(pwd)
fi

# Validate repository path
if [[ ! -d "$repo_path" ]]; then
    echo "Error: Path does not exist: $repo_path" >&2
    echo "  Current directory: $(pwd)" >&2
    echo "  Tip: Use --path to specify a different directory" >&2
    exit 1
fi

# Check if it's a git repository
if ! git -C "$repo_path" rev-parse --git-dir >/dev/null 2>&1; then
    echo "Error: Not a git repository: $repo_path" >&2
    echo "  To initialize: cd '$repo_path' && git init" >&2
    echo "  Or specify a valid git repository with --path" >&2
    exit 1
fi

# If pattern is provided, find the branch
if [[ -n "$pattern" ]]; then
    echo "🔍 Finding branch for pattern: $pattern"

    # Check if pattern is already merged
    if check_if_pattern_merged "$pattern" "$repo_path" "$base_branch"; then
        echo ""
        echo "❌ Pattern ${pattern} has already been merged to ${base_branch}"
        echo "   No synchronization needed."
        exit 1
    fi

    # Find branch matching pattern
    if found_branch=$(find_ticket_branch "$pattern" "$repo_path"); then
        branch_name="$found_branch"
        echo "✅ Found branch: $branch_name"
    else
        echo "❌ No branch found for pattern: $pattern" >&2
        echo "  Checked both local and remote branches" >&2
        echo "  Tip: Verify pattern matches your ticket format (e.g., PROJ-123, PROJ-456)" >&2
        echo "  Available patterns from config: $(get_ticket_prefixes "$repo_path" 2>/dev/null || echo 'none configured')" >&2
        exit 1
    fi
fi

# Determine branch name
if [[ -z "$branch_name" ]]; then
    branch_name=$(git -C "$repo_path" branch --show-current)
    if [[ -z "$branch_name" ]]; then
        echo "Error: Not on a branch (detached HEAD state)" >&2
        echo "  Current HEAD: $(git -C "$repo_path" rev-parse --short HEAD 2>/dev/null)" >&2
        echo "  To recover:" >&2
        echo "    1. Create branch: git checkout -b new-branch-name" >&2
        echo "    2. Or switch to existing: git checkout main" >&2
        exit 1
    fi
fi

# Validate branch exists
if ! git -C "$repo_path" show-ref --verify --quiet "refs/heads/$branch_name" 2>/dev/null; then
    # Try to create local branch from remote
    if git -C "$repo_path" show-ref --verify --quiet "refs/remotes/origin/$branch_name" 2>/dev/null; then
        echo "Creating local branch tracking origin/${branch_name}..."
        git -C "$repo_path" checkout -b "$branch_name" "origin/$branch_name" >/dev/null 2>&1
    else
        echo "Error: Branch does not exist: $branch_name" >&2
        echo "  Available local branches:" >&2
        git -C "$repo_path" branch --format='    %(refname:short)' 2>/dev/null | head -10 >&2
        typeset -i branch_count=$(git -C "$repo_path" branch 2>/dev/null | wc -l)
        if [[ $branch_count -gt 10 ]]; then
            echo "    ... and $((branch_count - 10)) more" >&2
        fi
        echo "  To create: git checkout -b $branch_name" >&2
        exit 1
    fi
fi

# If showing status only, display and exit
if [[ "$show_status" == "true" ]]; then
    echo "📊 Sync Status for $branch_name"
    echo ""
    get_sync_status "$repo_path" "$base_branch"
    exit 0
fi

# Display sync information
echo ""
echo "🔄 Branch Synchronizer"
echo "  Repository: $repo_path"
echo "  Branch: $branch_name"
echo "  Base: $base_branch"
echo ""

# Check if we're on the correct branch
typeset current_branch=$(git -C "$repo_path" branch --show-current)
if [[ "$current_branch" != "$branch_name" ]]; then
    echo "⚠️  Switching from $current_branch to $branch_name"
    git -C "$repo_path" checkout "$branch_name" >/dev/null 2>&1
fi

# Perform sync and rebase
if sync_and_rebase_branch "$repo_path" "$branch_name" "$base_branch"; then
    echo ""
    echo "✅ Branch synchronized successfully"
    echo ""
    echo "📌 Next steps:"
    echo "  1. Review the changes"
    echo "  2. Test your code"
    echo "  3. Push to remote: git push origin $branch_name"

    # If force-push is needed
    if git -C "$repo_path" show-ref --verify --quiet "refs/remotes/origin/$branch_name" 2>/dev/null; then
        typeset -i behind_remote=$(git -C "$repo_path" rev-list --count "origin/${branch_name}..HEAD" 2>/dev/null || echo "0")
        if [[ $behind_remote -gt 0 ]]; then
            echo ""
            echo "⚠️  Note: Your local branch has diverged from remote"
            echo "    Force-push may be needed: git push --force-with-lease origin $branch_name"
        fi
    fi

    exit 0
else
    echo ""
    echo "❌ Synchronization failed"
    echo "  Branch: $branch_name" >&2
    echo "  Repository: $repo_path" >&2
    echo "  Current state: $(git -C "$repo_path" status --short 2>/dev/null | head -3 || echo 'unknown')" >&2
    echo "  Check output above for specific error details" >&2
    exit 1
fi
