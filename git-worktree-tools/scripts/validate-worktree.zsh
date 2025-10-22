#!/usr/bin/env zsh
# Validate Worktree - Check if worktree exists and is valid
# Returns structured status information

# Reset to known ZSH defaults
emulate -LR zsh

# Enable strict error handling
setopt ERR_EXIT NO_UNSET PIPE_FAIL

# Script metadata (read-only constants)
typeset -r SCRIPT_DIR="${${(%):-%x}:A:h}"
typeset -r SCRIPT_NAME="${${(%):-%x}:t}"

# Load libraries
source "${SCRIPT_DIR}/lib/worktree-functions.zsh"
source "${SCRIPT_DIR}/lib/branch-utils.zsh"

# Parse arguments
typeset name=""
typeset project_root=""
typeset quiet=false

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
        --quiet)
            quiet=true
            shift
            ;;
        -h|--help)
            cat << 'EOF'
Usage: validate-worktree.zsh --name=NAME [OPTIONS]

Check if a worktree exists and is valid.

Required:
  --name=NAME               Worktree name to validate

Optional:
  --project-root=PATH       Git repository root (auto-detect if not provided)
  --quiet                   Suppress stderr output
  -h, --help                Show this help message

Examples:
  # Validate worktree existence
  validate-worktree.zsh --name=PROJ-123

  # Quiet mode (only JSON output)
  validate-worktree.zsh --name=PROJ-123 --quiet

Output:
  JSON object with validation results:
  {
    "name": "worktree-name",
    "status": "VALID|INVALID|NOT_FOUND",
    "path": "/path/to/worktree",
    "branch": "feature/branch",
    "ticket": "TICKET-123",
    "exists": true|false,
    "is_git_worktree": true|false
  }

Exit Codes:
  0   Worktree is valid
  1   Worktree is invalid or not found
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

# Initialize variables
typeset branch=""
typeset ticket=""
typeset exists=false
typeset is_git_worktree=false

# Determine exists and is_git_worktree flags
case "$status_type" in
    "VALID")
        exists=true
        is_git_worktree=true
        if ! $quiet; then
            echo "✅ Worktree is valid: $worktree_path" >&2
        fi
        # Get branch and ticket info
        branch=$(get_worktree_branch "$worktree_path" || echo "")
        if [[ -n "$branch" ]]; then
            ticket=$(extract_ticket_number "$branch" || echo "")
        fi
        ;;
    "INVALID")
        exists=true
        is_git_worktree=false
        if ! $quiet; then
            echo "❌ Worktree directory exists but is not a valid git worktree: $worktree_path" >&2
        fi
        ;;
    "NOT_FOUND")
        exists=false
        is_git_worktree=false
        if ! $quiet; then
            echo "❌ Worktree not found: $name" >&2
        fi
        worktree_path=""
        ;;
esac

# Output JSON result
jq -n \
    --arg name "$name" \
    --arg status "$status_type" \
    --arg path "$worktree_path" \
    --arg branch "$branch" \
    --arg ticket "$ticket" \
    --argjson exists "$exists" \
    --argjson is_git_worktree "$is_git_worktree" \
    '{
        name: $name,
        status: $status,
        path: $path,
        branch: $branch,
        ticket: $ticket,
        exists: $exists,
        is_git_worktree: $is_git_worktree
    }'

# Exit with appropriate code
if [[ "$status_type" == "VALID" ]]; then
    exit 0
else
    exit 1
fi
