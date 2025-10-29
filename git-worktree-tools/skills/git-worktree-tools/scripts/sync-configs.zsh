#!/usr/bin/env zsh
# Sync Configurations - Update worktree configs from main repository
# Syncs .claude/, CLAUDE.local.md, .env files

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

# Parse arguments
typeset name=""
typeset project_root=""
typeset worktree_path=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --name=*)
            name="${1#*=}"
            shift
            ;;
        --worktree-path=*)
            worktree_path="${1#*=}"
            shift
            ;;
        --project-root=*)
            project_root="${1#*=}"
            shift
            ;;
        -h|--help)
            cat << 'EOF'
Usage: sync-configs.zsh (--name=NAME | --worktree-path=PATH) [OPTIONS]

Sync project configurations from main repository to worktree.

Required (one of):
  --name=NAME               Worktree name to sync
  --worktree-path=PATH      Direct path to worktree directory

Optional:
  --project-root=PATH       Git repository root (auto-detect if not provided)
  -h, --help                Show this help message

Synced Files:
  - .claude/                Directory with project-specific Claude configurations
  - CLAUDE.local.md         Project-specific user instructions
  - .env                    Environment variables

Examples:
  # Sync by worktree name
  sync-configs.zsh --name=PROJ-123

  # Sync by path
  sync-configs.zsh --worktree-path=/path/to/worktree

Output:
  JSON object with sync status

Exit Codes:
  0   Success (all or some configs synced)
  1   Error (no configs synced or worktree invalid)
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$name" ]] && [[ -z "$worktree_path" ]]; then
    echo "Error: Either --name or --worktree-path is required" >&2
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

# Resolve worktree path if name was provided
if [[ -n "$name" ]]; then
    # Validate inputs
    validate_worktree_inputs "$name" "$project_root" || exit 1

    # Check worktree status
    typeset worktree_status=$(check_worktree_status "$name" "$project_root")
    typeset status_type="${worktree_status%%:*}"
    worktree_path="${worktree_status#*:}"

    if [[ "$status_type" != "VALID" ]]; then
        echo "Error: Worktree is not valid: $name" >&2
        echo "Status: $status_type" >&2
        exit 1
    fi

    echo "🔄 Syncing configurations for worktree: $name" >&2
else
    echo "🔄 Syncing configurations to: $worktree_path" >&2
fi

# Validate worktree path exists
if [[ ! -d "$worktree_path" ]]; then
    echo "Error: Worktree directory does not exist: $worktree_path" >&2
    exit 1
fi

# Perform sync
typeset sync_status exit_code
if sync_all_configs "$project_root" "$worktree_path"; then
    sync_status="success"
    exit_code=0
else
    sync_status="partial"
    exit_code=0  # Partial success is still success
fi

# List what was synced
typeset synced_configs=$(list_config_files "$project_root")

# Output JSON result
jq -n \
    --arg name "$name" \
    --arg path "$worktree_path" \
    --arg status "$sync_status" \
    --argjson configs "$synced_configs" \
    '{
        name: $name,
        path: $path,
        status: $status,
        synced_configs: $configs
    }'

exit $exit_code
