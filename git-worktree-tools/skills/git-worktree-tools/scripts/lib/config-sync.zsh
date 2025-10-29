#!/usr/bin/env zsh
# Configuration Sync Functions - Sync project configs to worktrees
# Keeps worktrees in sync with main repository configurations

# Reset to known ZSH defaults (for library consistency)
emulate -LR zsh

# Sync .claude directory from main repo to worktree
# Args: $1 - project root, $2 - worktree path
# Returns: 0 on success, 1 on failure
# Stderr: Progress messages
sync_claude_directory() {
    typeset project_root=$1
    typeset worktree_path=$2

    typeset source_dir="${project_root}/.claude"
    typeset target_dir="${worktree_path}/.claude"

    # Check if source exists
    if [[ ! -d "$source_dir" ]]; then
        echo "  ℹ️  No .claude directory in main repository - skipping" >&2
        return 0
    fi

    echo "  → Syncing .claude directory..." >&2

    # Create target directory if it doesn't exist
    mkdir -p "$target_dir"

    # Use rsync for robust syncing with deletion of removed files
    if rsync -a --delete-after "${source_dir}/" "${target_dir}/"; then
        echo "  ✅ .claude directory synced" >&2
        return 0
    else
        echo "  ❌ Failed to sync .claude directory" >&2
        return 1
    fi
}

# Sync a single configuration file
# Args: $1 - file name (e.g., "CLAUDE.local.md"), $2 - project root, $3 - worktree path
# Returns: 0 on success or if file doesn't exist, 1 on copy failure
# Stderr: Progress messages
sync_config_file() {
    typeset file_name=$1
    typeset project_root=$2
    typeset worktree_path=$3

    typeset source_file="${project_root}/${file_name}"
    typeset target_file="${worktree_path}/${file_name}"

    # Check if source exists
    if [[ ! -f "$source_file" ]]; then
        echo "  ℹ️  No ${file_name} in main repository - skipping" >&2
        return 0
    fi

    echo "  → Syncing ${file_name}..." >&2

    # Copy file
    if cp "$source_file" "$target_file"; then
        echo "  ✅ ${file_name} synced" >&2
        return 0
    else
        echo "  ❌ Failed to sync ${file_name}" >&2
        return 1
    fi
}

# Sync all project configurations to worktree
# Args: $1 - project root, $2 - worktree path
# Returns: 0 if all succeeded, 1 if any failed
# Stderr: Progress messages
sync_all_configs() {
    typeset project_root=$1
    typeset worktree_path=$2

    echo "🔄 Syncing project configurations..." >&2

    typeset sync_failed=false

    # Sync .claude directory
    if ! sync_claude_directory "$project_root" "$worktree_path"; then
        sync_failed=true
    fi

    # Sync CLAUDE.local.md
    if ! sync_config_file "CLAUDE.local.md" "$project_root" "$worktree_path"; then
        sync_failed=true
    fi

    # Sync .env
    if ! sync_config_file ".env" "$project_root" "$worktree_path"; then
        sync_failed=true
    fi

    if [[ "$sync_failed" == "true" ]]; then
        echo "⚠️  Some configuration files failed to sync" >&2
        return 1
    else
        echo "✅ All configurations synced successfully" >&2
        return 0
    fi
}

# Verify a sync operation completed successfully
# Args: $1 - source path, $2 - target path
# Returns: 0 if verified, 1 if verification failed
verify_sync() {
    typeset source=$1
    typeset target=$2

    # If source doesn't exist, target shouldn't either (or we don't care)
    if [[ ! -e "$source" ]]; then
        return 0
    fi

    # Check if target exists
    if [[ ! -e "$target" ]]; then
        return 1
    fi

    # For files, check size matches
    if [[ -f "$source" ]] && [[ -f "$target" ]]; then
        typeset source_size=$(stat -f%z "$source" 2>/dev/null || stat -c%s "$source" 2>/dev/null)
        typeset target_size=$(stat -f%z "$target" 2>/dev/null || stat -c%s "$target" 2>/dev/null)

        if [[ "$source_size" != "$target_size" ]]; then
            return 1
        fi
    fi

    # For directories, just verify it exists
    if [[ -d "$source" ]] && [[ -d "$target" ]]; then
        return 0
    fi

    return 0
}

# List configuration files that would be synced
# Args: $1 - project root
# Returns: JSON array of config file info
# Exit: 0 on success
list_config_files() {
    typeset project_root=$1
    typeset -a configs

    # Check .claude directory
    if [[ -d "${project_root}/.claude" ]]; then
        typeset file_count=$(find "${project_root}/.claude" -type f 2>/dev/null | wc -l | tr -d ' ')
        typeset claude_json=$(jq -n \
            --arg path ".claude/" \
            --arg type "directory" \
            --arg files "$file_count" \
            '{path: $path, type: $type, file_count: ($files | tonumber)}')
        configs+=("$claude_json")
    fi

    # Check CLAUDE.local.md
    if [[ -f "${project_root}/CLAUDE.local.md" ]]; then
        typeset claude_local_json=$(jq -n \
            --arg path "CLAUDE.local.md" \
            --arg type "file" \
            '{path: $path, type: $type}')
        configs+=("$claude_local_json")
    fi

    # Check .env
    if [[ -f "${project_root}/.env" ]]; then
        typeset env_json=$(jq -n \
            --arg path ".env" \
            --arg type "file" \
            '{path: $path, type: $type}')
        configs+=("$env_json")
    fi

    # Output as JSON array
    if [[ ${#configs[@]} -eq 0 ]]; then
        echo "[]"
    else
        printf '%s\n' "${configs[@]}" | jq -s '.'
    fi

    return 0
}
