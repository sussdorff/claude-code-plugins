#!/usr/bin/env zsh
#
# Script: safety-checks.zsh
# Description: Branch protection and push safety validations
# Usage: Sourced by git-ops.zsh
# Requires: git

# Reset to known ZSH defaults
emulate -LR zsh

# Check if branch is protected (main or master)
# Args: branch name
# Returns: 0 if protected, 1 if not protected
is_protected_branch() {
    typeset branch=$1

    if [[ -z "$branch" ]]; then
        return 1
    fi

    if [[ "$branch" == "main" ]] || [[ "$branch" == "master" ]]; then
        return 0
    else
        return 1
    fi
}

# Check if branch has upstream tracking branch
# Args: branch name
# Returns: 0 if has upstream, 1 if no upstream
has_upstream() {
    typeset branch=$1

    if [[ -z "$branch" ]]; then
        return 1
    fi

    # Try to get upstream branch
    if git rev-parse --abbrev-ref "$branch@{upstream}" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Check if remote 'origin' exists
# Returns: 0 if exists, 1 if not
check_remote_exists() {
    if git remote get-url origin &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Check if local branch is ahead of remote
# Args: branch name
# Returns: 0 if ahead, 1 if not ahead
is_ahead_of_remote() {
    typeset branch=$1

    if [[ -z "$branch" ]]; then
        return 1
    fi

    # Check if has upstream
    if ! has_upstream "$branch"; then
        # No upstream, can't be ahead
        return 1
    fi

    # Get status
    typeset status=$(git status -sb 2>/dev/null | head -1)

    if [[ "$status" =~ "ahead" ]]; then
        return 0
    else
        return 1
    fi
}

# Check if local branch is behind remote
# Args: branch name
# Returns: 0 if behind, 1 if not behind
is_behind_remote() {
    typeset branch=$1

    if [[ -z "$branch" ]]; then
        return 1
    fi

    # Check if has upstream
    if ! has_upstream "$branch"; then
        # No upstream, can't be behind
        return 1
    fi

    # Get status
    typeset status=$(git status -sb 2>/dev/null | head -1)

    if [[ "$status" =~ "behind" ]]; then
        return 0
    else
        return 1
    fi
}

# Check if pre-commit hooks exist
# Returns: 0 if hooks exist, 1 if no hooks
check_hooks_exist() {
    typeset git_dir=$(git rev-parse --git-dir 2>/dev/null)

    if [[ -z "$git_dir" ]]; then
        return 1
    fi

    # Check for pre-commit hook
    if [[ -f "$git_dir/hooks/pre-commit" ]] && [[ -x "$git_dir/hooks/pre-commit" ]]; then
        return 0
    else
        return 1
    fi
}

# Get current branch name
# Returns: branch name or empty string
get_current_branch() {
    git branch --show-current 2>/dev/null
}

# Check if in a git repository
# Returns: 0 if in repo, 1 if not
is_git_repo() {
    if git rev-parse --git-dir &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Check if working directory is clean (no uncommitted changes)
# Returns: 0 if clean, 1 if dirty
is_working_directory_clean() {
    if [[ -z $(git status --porcelain 2>/dev/null) ]]; then
        return 0
    else
        return 1
    fi
}

# Get upstream branch name
# Args: branch name
# Returns: upstream branch name or empty string
get_upstream_branch() {
    typeset branch=$1

    if [[ -z "$branch" ]]; then
        return 1
    fi

    git rev-parse --abbrev-ref "$branch@{upstream}" 2>/dev/null
}

# Count commits ahead of remote
# Args: branch name
# Returns: number of commits ahead
count_commits_ahead() {
    typeset branch=$1

    if [[ -z "$branch" ]]; then
        echo "0"
        return 1
    fi

    if ! has_upstream "$branch"; then
        echo "0"
        return 1
    fi

    typeset upstream=$(get_upstream_branch "$branch")
    typeset -i count=$(git rev-list --count "$upstream..$branch" 2>/dev/null || echo "0")

    echo "$count"
}

# Count commits behind remote
# Args: branch name
# Returns: number of commits behind
count_commits_behind() {
    typeset branch=$1

    if [[ -z "$branch" ]]; then
        echo "0"
        return 1
    fi

    if ! has_upstream "$branch"; then
        echo "0"
        return 1
    fi

    typeset upstream=$(get_upstream_branch "$branch")
    typeset -i count=$(git rev-list --count "$branch..$upstream" 2>/dev/null || echo "0")

    echo "$count"
}
