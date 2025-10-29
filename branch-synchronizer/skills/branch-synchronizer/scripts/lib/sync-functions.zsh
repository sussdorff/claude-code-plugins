#!/usr/bin/env zsh
# Sync Functions - Core synchronization and rebase logic
# Adapted from charly-server-dev-tools git-functions.zsh

# Reset to known ZSH defaults (local to sourced functions)
emulate -L zsh

# Detect if running in agent mode (called with parameters) vs interactive mode
# Agent mode: Script was invoked with explicit parameters
# Interactive mode: Script was run directly by user
# Returns: 0 for agent mode, 1 for interactive mode
is_agent_mode() {
    # If BRANCH_SYNC_AGENT_MODE is explicitly set, use it
    if [[ -n "${BRANCH_SYNC_AGENT_MODE:-}" ]]; then
        if [[ "${BRANCH_SYNC_AGENT_MODE}" == "true" ]]; then
            return 0
        else
            return 1
        fi
    fi

    # Heuristic: If path was explicitly provided, assume agent mode
    # Interactive users typically run from within the directory
    if [[ -n "${BRANCH_SYNC_PATH_PROVIDED:-}" ]]; then
        return 0
    fi

    # Default to interactive mode
    return 1
}

# Handle rebase conflicts based on execution mode
# Args: worktree_dir
# Returns: 0 for agent mode (aborted), 1 for interactive mode (needs manual resolution)
handle_rebase_conflict() {
    typeset worktree_dir=$1

    if is_agent_mode; then
        # Agent mode: Abort and report
        echo "⚠️  Rebase encountered conflicts - auto-aborting" >&2
        git -C "$worktree_dir" rebase --abort 2>&1 >&2
        echo "ℹ️  Worktree left at original state" >&2
        echo "" >&2
        echo "Manual resolution needed:" >&2
        echo "  cd ${worktree_dir}" >&2
        echo "  git rebase origin/main" >&2
        echo "  # Resolve conflicts" >&2
        echo "  git rebase --continue" >&2
        return 0
    else
        # Interactive mode: Guide user through resolution
        echo "" >&2
        echo "⚠️  Conflicts detected during rebase" >&2
        echo "" >&2
        echo "Conflicting files:" >&2
        git -C "$worktree_dir" diff --name-only --diff-filter=U 2>/dev/null | sed 's/^/    - /' >&2
        echo "" >&2
        echo "To resolve:" >&2
        echo "  1. Edit conflicting files" >&2
        echo "  2. git add <resolved-files>" >&2
        echo "  3. git rebase --continue" >&2
        echo "" >&2
        echo "Or to abort:" >&2
        echo "  git rebase --abort" >&2
        echo "" >&2
        return 1
    fi
}

# Stash uncommitted changes before rebase
# Args: worktree_dir
# Returns: 0 if stashed, 1 if nothing to stash
stash_changes() {
    typeset worktree_dir=$1

    if [[ -n $(git -C "$worktree_dir" status --porcelain 2>/dev/null) ]]; then
        echo "  → Stashing uncommitted changes..." >&2
        git -C "$worktree_dir" stash push -m "branch-synchronizer auto-stash" >/dev/null 2>&1
        return 0
    else
        return 1
    fi
}

# Restore stashed changes after rebase
# Args: worktree_dir
# Returns: 0 on success, 1 on failure
restore_changes() {
    typeset worktree_dir=$1

    # Check if there's a stash from branch-synchronizer
    if git -C "$worktree_dir" stash list 2>/dev/null | grep -q "branch-synchronizer auto-stash"; then
        echo "  → Restoring stashed changes..." >&2
        if git -C "$worktree_dir" stash pop >/dev/null 2>&1; then
            return 0
        else
            echo "  ⚠️  Failed to restore stash - may have conflicts" >&2
            echo "     Run 'git stash pop' manually to resolve" >&2
            return 1
        fi
    fi
    return 0
}

# Sync branch with remote and rebase onto base branch
# Args: worktree_dir, branch (optional), base_branch (optional, default: main)
# Returns: 0 on success, 1 on failure
sync_and_rebase_branch() {
    typeset worktree_dir=$1
    typeset branch=${2:-$(git -C "$worktree_dir" branch --show-current)}
    typeset base_branch=${3:-main}

    echo "Syncing branch ${branch} with remote..." >&2

    # Fetch latest changes
    if ! git -C "$worktree_dir" fetch origin >/dev/null 2>&1; then
        echo "Failed to fetch from origin" >&2
        echo "  Repository: $worktree_dir" >&2
        echo "  Possible causes:" >&2
        echo "    - No network connection" >&2
        echo "    - Remote 'origin' not configured: git remote -v" >&2
        echo "    - Authentication issues: check credentials" >&2
        return 1
    fi

    # Check if remote branch exists
    if git -C "$worktree_dir" show-ref --verify --quiet "refs/remotes/origin/$branch" 2>/dev/null; then
        # Pull latest changes from remote branch
        echo "Pulling latest changes from origin/${branch}..." >&2

        # Check if we're behind remote
        typeset -i behind=$(git -C "$worktree_dir" rev-list --count "HEAD..origin/${branch}" 2>/dev/null || echo "0")

        if [[ $behind -gt 0 ]]; then
            echo "  → ${behind} new commit(s) from remote" >&2
            if ! git -C "$worktree_dir" pull origin "$branch" --rebase 2>&1; then
                echo "Failed to pull from origin/${branch}" >&2
                echo "  Repository: $worktree_dir" >&2
                echo "  Branch: $branch" >&2
                echo "  To resolve:" >&2
                echo "    1. Check git status: git -C '$worktree_dir' status" >&2
                echo "    2. Resolve conflicts if any" >&2
                echo "    3. Continue rebase: git rebase --continue" >&2
                echo "    4. Or abort: git rebase --abort" >&2
                return 1
            fi
        else
            echo "  → Already up to date with remote" >&2
        fi
    else
        echo "No remote branch origin/${branch} - this is a local-only branch" >&2
    fi

    # Fetch latest base branch
    echo "Fetching latest ${base_branch} branch..." >&2
    if ! git -C "$worktree_dir" fetch origin "${base_branch}" >/dev/null 2>&1; then
        echo "Warning: Could not fetch ${base_branch} from remote - using local data" >&2
    fi

    # Check if we need to rebase
    typeset base_ref="origin/${base_branch}"
    typeset -i behind_base=$(git -C "$worktree_dir" rev-list --count "HEAD..${base_ref}" 2>/dev/null || echo "0")

    if [[ $behind_base -gt 0 ]]; then
        echo "Rebasing onto ${base_ref} (${behind_base} new commits)..." >&2

        # Stash any uncommitted changes
        typeset -i had_stash=0
        if stash_changes "$worktree_dir"; then
            had_stash=1
        fi

        # Perform rebase
        if git -C "$worktree_dir" rebase "${base_ref}" 2>&1; then
            echo "Successfully rebased onto ${base_ref}" >&2
        else
            # Rebase failed - handle based on mode
            handle_rebase_conflict "$worktree_dir"
            typeset -i conflict_result=$?

            # Restore stashed changes if we had any
            if (( had_stash )); then
                restore_changes "$worktree_dir" || true
            fi

            return 1
        fi

        # Restore stashed changes if any
        if (( had_stash )); then
            restore_changes "$worktree_dir" || true
        fi
    else
        echo "Already up to date with ${base_ref}" >&2
    fi

    return 0
}

# Get sync status information
# Args: worktree_dir, base_branch (optional, default: main)
# Returns: JSON with sync status
get_sync_status() {
    typeset worktree_dir=$1
    typeset base_branch=${2:-main}

    typeset current_branch=$(git -C "$worktree_dir" branch --show-current)
    typeset base_ref="origin/${base_branch}"

    # Count commits ahead/behind
    typeset -i ahead=$(git -C "$worktree_dir" rev-list --count "${base_ref}..HEAD" 2>/dev/null || echo "0")
    typeset -i behind=$(git -C "$worktree_dir" rev-list --count "HEAD..${base_ref}" 2>/dev/null || echo "0")

    # Check for uncommitted changes
    typeset has_changes=false
    if [[ -n $(git -C "$worktree_dir" status --porcelain 2>/dev/null) ]]; then
        has_changes=true
    fi

    # Check if remote branch exists
    typeset has_remote=false
    if git -C "$worktree_dir" show-ref --verify --quiet "refs/remotes/origin/$current_branch" 2>/dev/null; then
        has_remote=true
    fi

    # Build JSON status
    jq -n \
        --arg branch "$current_branch" \
        --arg base "$base_branch" \
        --argjson ahead "$ahead" \
        --argjson behind "$behind" \
        --argjson has_changes "$has_changes" \
        --argjson has_remote "$has_remote" \
        '{
            branch: $branch,
            base_branch: $base,
            commits_ahead: $ahead,
            commits_behind: $behind,
            has_uncommitted_changes: $has_changes,
            has_remote_branch: $has_remote,
            needs_sync: ($behind > 0)
        }'
}
