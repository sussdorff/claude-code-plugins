#!/usr/bin/env zsh
# Remove Worktree - Clean up worktree and remove from git
# Handles both valid and invalid worktrees

# Reset to known ZSH defaults
emulate -LR zsh

# Enable strict error handling
setopt ERR_EXIT NO_UNSET PIPE_FAIL

# Script metadata (read-only constants)
typeset -r SCRIPT_DIR="${${(%):-%x}:A:h}"
typeset -r SCRIPT_NAME="${${(%):-%x}:t}"

# Load libraries
source "${SCRIPT_DIR}/lib/worktree-functions.zsh"

# Parse arguments
typeset name=""
typeset project_root=""
typeset force=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --name=*)
            name="${1#*=}"
            shift
            ;;
        --project-root=*)
            project_root="${1#*=}"
            shift
            ;;
        --force)
            force=true
            shift
            ;;
        -h|--help)
            cat << 'EOF'
Usage: remove-worktree.zsh --name=NAME [OPTIONS]

Remove a git worktree and clean up its directory.

Required:
  --name=NAME               Worktree name to remove

Optional:
  --project-root=PATH       Git repository root (auto-detect if not provided)
  --force                   Force removal even with uncommitted changes
  -h, --help                Show this help message

Examples:
  # Remove worktree
  remove-worktree.zsh --name=PROJ-123

  # Force removal with uncommitted changes
  remove-worktree.zsh --name=PROJ-123 --force

Output:
  JSON object with removal status

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

# Check worktree status
typeset worktree_status=$(check_worktree_status "$name" "$project_root")
typeset status_type="${worktree_status%%:*}"
typeset worktree_path="${worktree_status#*:}"

echo "🗑️  Removing worktree: $name" >&2

case "$status_type" in
    "VALID")
        echo "  → Found valid worktree at: $worktree_path" >&2

        # Check for uncommitted changes unless force
        if [[ "$force" == "false" ]]; then
            if [[ -n $(git -C "$worktree_path" status --porcelain 2>/dev/null) ]]; then
                echo "Error: Worktree has uncommitted changes" >&2
                echo "Use --force to remove anyway" >&2
                exit 1
            fi
        fi

        # Remove using git worktree remove
        echo "  → Removing from git worktree list..." >&2
        if [[ "$force" == "true" ]]; then
            git -C "$project_root" worktree remove --force "$worktree_path" || {
                echo "⚠️  git worktree remove failed, cleaning up directory manually..." >&2
                rm -rf "$worktree_path"
            }
        else
            git -C "$project_root" worktree remove "$worktree_path" || {
                echo "⚠️  git worktree remove failed, cleaning up directory manually..." >&2
                rm -rf "$worktree_path"
            }
        fi

        echo "✅ Worktree removed successfully" >&2
        ;;
    "INVALID")
        echo "  → Found invalid worktree directory at: $worktree_path" >&2
        echo "  → Cleaning up directory..." >&2
        rm -rf "$worktree_path"
        echo "✅ Invalid worktree directory cleaned up" >&2
        ;;
    "NOT_FOUND")
        echo "⚠️  Worktree not found: $name" >&2
        echo "Nothing to remove" >&2
        # Still output JSON and exit 0 (not an error if already removed)
        ;;
esac

# Output JSON result
jq -n \
    --arg name "$name" \
    --arg path "$worktree_path" \
    --arg status "removed" \
    '{
        name: $name,
        path: $path,
        status: $status
    }'

exit 0
