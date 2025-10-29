#!/usr/bin/env zsh
#
# Script: commit-helpers.zsh
# Description: Commit validation, authorship checks, and hook handling
# Usage: Sourced by git-ops.zsh
# Requires: git

# Reset to known ZSH defaults
emulate -LR zsh

# Validate commit message structure based on style
# Args: message, style
# Returns: 0 if valid, 1 if invalid
validate_commit_message() {
    typeset message=$1
    typeset style=$2

    # Empty message is always invalid
    if [[ -z "$message" ]]; then
        echo "Error: Commit message cannot be empty" >&2
        return 1
    fi

    case "$style" in
        conventional)
            # Must match: type(scope?): message
            # Valid types: feat, fix, docs, refactor, test, chore, perf, style
            if ! echo "$message" | grep -qE '^(feat|fix|docs|refactor|test|chore|perf|style)(\([a-z0-9-]+\))?: .+'; then
                echo "Error: Invalid commit message for style: conventional" >&2
                echo "Expected format: type(scope?): message" >&2
                echo "" >&2
                echo "Valid types: feat, fix, docs, refactor, test, chore, perf, style" >&2
                echo "Example: feat(auth): add user authentication" >&2
                return 1
            fi
            ;;
        *)
            # Other styles: just check not empty (already done above)
            ;;
    esac

    return 0
}

# Check if files were modified by hooks after commit
# Returns: 0 if modified, 1 if not
files_were_modified_by_hooks() {
    # After commit, check if working directory has changes
    if [[ -n $(git status --porcelain 2>/dev/null) ]]; then
        return 0
    else
        return 1
    fi
}

# Determine if it's safe to amend the last commit
# Safe if: commit is by current user AND commit has not been pushed
# Returns: 0 if safe, 1 if not safe
should_amend_commit() {
    typeset is_own_commit
    typeset not_pushed

    is_own_commit=$(check_authorship)
    not_pushed=$(check_not_pushed)

    if [[ "$is_own_commit" == "true" ]] && [[ "$not_pushed" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

# Check if last commit was created by current user
# Returns: "true" if own commit, "false" otherwise
check_authorship() {
    typeset author=$(git log -1 --format='%an %ae' 2>/dev/null)
    typeset current_user=$(git config user.name 2>/dev/null)
    typeset current_email=$(git config user.email 2>/dev/null)

    if [[ -z "$author" ]]; then
        # No commits yet
        echo "false"
        return 1
    fi

    if [[ "$author" == "$current_user $current_email" ]]; then
        echo "true"
        return 0
    else
        echo "false"
        return 1
    fi
}

# Check if commit has NOT been pushed to remote
# Returns: "true" if not pushed (local only), "false" if pushed
check_not_pushed() {
    # Get current branch
    typeset branch=$(git branch --show-current 2>/dev/null)

    if [[ -z "$branch" ]]; then
        # Detached HEAD or no branch
        echo "false"
        return 1
    fi

    # Check if branch has upstream
    if ! git rev-parse --abbrev-ref "$branch@{upstream}" &>/dev/null; then
        # No upstream, so definitely not pushed
        echo "true"
        return 0
    fi

    # Check if local branch is ahead of remote
    typeset status=$(git status -sb 2>/dev/null | head -1)

    if [[ "$status" =~ "ahead" ]]; then
        # Local has commits that remote doesn't
        echo "true"
        return 0
    else
        # Either up-to-date or behind (not ahead = pushed)
        echo "false"
        return 1
    fi
}

# Check if there are staged changes to commit
# Returns: 0 if changes staged, 1 if nothing to commit
has_staged_changes() {
    # Check for staged changes
    if git diff --cached --quiet 2>/dev/null; then
        # No staged changes
        return 1
    else
        # Has staged changes
        return 0
    fi
}

# Check if there are unstaged changes
# Returns: 0 if changes exist, 1 if working directory clean
has_unstaged_changes() {
    # Check for unstaged changes
    if git diff --quiet 2>/dev/null; then
        # No unstaged changes
        return 1
    else
        # Has unstaged changes
        return 0
    fi
}

# Get commit statistics for display
# Returns: string with file count and insertions/deletions
get_commit_stats() {
    git diff --cached --shortstat 2>/dev/null || echo "No changes"
}

# Handle pre-commit hook modifications
# This function should be called after a commit if hooks modified files
# Returns: 0 on success, 1 on error
handle_hook_modifications() {
    echo "Pre-commit hooks modified files" >&2

    if should_amend_commit; then
        echo "  → Amending commit (safe: own commit, not pushed)" >&2
        git add -u
        if git commit --amend --no-edit; then
            echo "✅ Commit amended successfully" >&2
            return 0
        else
            echo "⚠️  Failed to amend commit" >&2
            return 1
        fi
    else
        echo "  → Creating new commit (not safe to amend)" >&2

        # Check why it's not safe
        typeset is_own=$(check_authorship)
        typeset not_pushed=$(check_not_pushed)

        if [[ "$is_own" != "true" ]]; then
            echo "     Reason: Last commit by different author" >&2
        fi
        if [[ "$not_pushed" != "true" ]]; then
            echo "     Reason: Commit already pushed to remote" >&2
        fi

        git add -u
        if git commit -m "chore: apply pre-commit hook changes"; then
            echo "✅ New commit created for hook changes" >&2
            return 0
        else
            echo "⚠️  Failed to create new commit" >&2
            return 1
        fi
    fi
}
