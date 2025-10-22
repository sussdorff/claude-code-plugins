#!/usr/bin/env zsh
# Create Worktree - Create git worktree and sync project configurations
# Operates from project root, never enters worktree directory

# Reset to known ZSH defaults
emulate -LR zsh

# Enable strict error handling
setopt ERR_EXIT NO_UNSET PIPE_FAIL

# Script metadata (read-only constants)
typeset -r SCRIPT_DIR="${${(%):-%x}:A:h}"
typeset -r SCRIPT_NAME="${${(%):-%x}:t}"

# Load libraries
source "${SCRIPT_DIR}/lib/worktree-functions.zsh"
source "${SCRIPT_DIR}/lib/config-sync.zsh"
source "${SCRIPT_DIR}/lib/branch-utils.zsh"

# Parse arguments
typeset name=""
typeset branch=""
typeset project_root=""
typeset base_branch="origin/main"
typeset skip_sync=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --name=*)
            name="${1#*=}"
            shift
            ;;
        --branch=*)
            branch="${1#*=}"
            shift
            ;;
        --project-root=*)
            project_root="${1#*=}"
            shift
            ;;
        --base-branch=*)
            base_branch="${1#*=}"
            shift
            ;;
        --skip-sync)
            skip_sync=true
            shift
            ;;
        -h|--help)
            cat << 'EOF'
Usage: create-worktree.zsh --name=NAME [OPTIONS]

Create a git worktree and sync project configurations.

Required:
  --name=NAME               Worktree name (e.g., PROJ-123 or feature-name)

Optional:
  --branch=BRANCH           Branch to checkout (creates new if doesn't exist)
  --project-root=PATH       Git repository root (auto-detect if not provided)
  --base-branch=BRANCH      Base branch for new branches (default: origin/main)
  --skip-sync               Skip configuration file sync
  -h, --help                Show this help message

Examples:
  # Create worktree for new ticket
  create-worktree.zsh --name=PROJ-123

  # Create worktree with specific branch
  create-worktree.zsh --name=PROJ-123 --branch=feature/PROJ-123/add-feature

  # Create worktree from specific base
  create-worktree.zsh --name=PROJ-123 --base-branch=develop

Output:
  JSON object with worktree information

Exit Codes:
  0   Success
  1   Error
EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$name" ]]; then
    echo "Error: --name is required" >&2
    echo "Use --help for usage information" >&2
    exit 1
fi

# Auto-detect project root if not provided
if [[ -z "$project_root" ]]; then
    project_root=$(detect_git_root) || {
        echo "Error: Not in a git repository and --project-root not provided" >&2
        exit 1
    }
fi

# Validate inputs
validate_worktree_inputs "$name" "$project_root" || exit 1

# Calculate worktree directory
typeset worktree_base=$(get_worktree_base "$project_root")
typeset worktree_dir="${worktree_base}/${name}"

echo "🆕 Creating worktree: $name" >&2

# Check if worktree already exists
typeset existing_status=$(check_worktree_status "$name" "$project_root")
if [[ "$existing_status" =~ ^VALID: ]]; then
    echo "Error: Worktree already exists: $worktree_dir" >&2
    exit 1
fi

# If status is INVALID, clean up first
if [[ "$existing_status" =~ ^INVALID: ]]; then
    echo "⚠️  Cleaning up invalid worktree..." >&2
    rm -rf "$worktree_dir"
fi

# Ensure worktree base exists
mkdir -p "$worktree_base"

# Determine branch to use
if [[ -z "$branch" ]]; then
    # Try to extract ticket from name and generate branch name
    typeset ticket=$(extract_ticket_number "$name" || echo "")
    if [[ -n "$ticket" ]]; then
        branch="feature/${ticket}/new-work"
        echo "  → Generated branch name: $branch" >&2
    else
        branch="feature/${name}"
        echo "  → Generated branch name: $branch" >&2
    fi
fi

# Validate branch name
if ! validate_branch_name "$branch"; then
    exit 1
fi

# Check if branch exists
typeset branch_exists=$(check_branch_exists "$project_root" "$branch")

echo "  → Branch: $branch (exists: $branch_exists)" >&2

# Create worktree based on branch existence
case "$branch_exists" in
    "both"|"local")
        # Branch exists locally, checkout from local
        echo "  → Checking out existing local branch..." >&2
        git -C "$project_root" worktree add "$worktree_dir" "$branch" || {
            echo "Error: Failed to create worktree" >&2
            exit 1
        }
        ;;
    "remote")
        # Branch exists remotely, create local tracking branch
        echo "  → Checking out remote branch..." >&2
        git -C "$project_root" worktree add "$worktree_dir" "origin/$branch" || {
            echo "Error: Failed to create worktree" >&2
            exit 1
        }
        # Create local tracking branch
        git -C "$worktree_dir" checkout -b "$branch" "origin/$branch" 2>/dev/null || true
        ;;
    "none")
        # Branch doesn't exist, create new one from base
        echo "  → Creating new branch from $base_branch..." >&2
        git -C "$project_root" worktree add -b "$branch" "$worktree_dir" "$base_branch" || {
            echo "Error: Failed to create worktree with new branch" >&2
            exit 1
        }
        ;;
esac

echo "✅ Worktree created at: $worktree_dir" >&2

# Sync configurations unless skipped
if [[ "$skip_sync" == "false" ]]; then
    if ! sync_all_configs "$project_root" "$worktree_dir"; then
        echo "⚠️  Configuration sync had errors, but worktree was created" >&2
    fi
fi

# Get the actual branch name (in case it was created/checked out)
typeset actual_branch=$(get_worktree_branch "$worktree_dir" || echo "$branch")

# Extract ticket from branch if present
typeset ticket=$(extract_ticket_number "$actual_branch" || echo "")

# Output JSON result
jq -n \
    --arg name "$name" \
    --arg path "$worktree_dir" \
    --arg branch "$actual_branch" \
    --arg ticket "$ticket" \
    --arg project_root "$project_root" \
    '{
        name: $name,
        path: $path,
        branch: $branch,
        ticket: $ticket,
        project_root: $project_root,
        status: "created"
    }'

exit 0
