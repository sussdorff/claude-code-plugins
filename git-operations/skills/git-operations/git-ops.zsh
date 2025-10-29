#!/usr/bin/env zsh
#
# Script: git-ops.zsh
# Description: Git operations - Single entry point for commit and push operations
# Usage: git-ops.zsh <command> [options]
# Requires: git

# Reset to known ZSH defaults
emulate -LR zsh

# Enable strict error handling
setopt ERR_EXIT       # Exit on error
setopt ERR_RETURN     # Return on error in functions
setopt NO_UNSET       # Error on undefined variables
setopt PIPE_FAIL      # Fail if any command in pipeline fails

# Script information
typeset -r ScriptPath="${(%):-%x}"
typeset -r ScriptDir="${${(%):-%x}:A:h}"
typeset -r ScriptName="${${(%):-%x}:t}"

# Cleanup function
cleanup() {
    # Remove temporary files if any
    :
}

# Register cleanup for all exit scenarios
trap cleanup EXIT INT TERM

# Load internal libraries
source "${ScriptDir}/lib/commit-helpers.zsh"
source "${ScriptDir}/lib/safety-checks.zsh"
source "${ScriptDir}/lib/style-engine.zsh"

# Show usage information
show_usage() {
    cat << 'EOF'
Usage: git-ops.zsh <command> [options]

Commands:
  commit    Create a commit with style and safety checks
  push      Push with branch protection

Commit Options:
  --message, -m MESSAGE    Commit message (required)
  --allow-empty           Allow empty commits
  --dry-run               Show what would be committed without committing

Push Options:
  --force, -f             Force push (blocked on main/master)
  --set-upstream, -u      Create upstream if missing
  --branch, -b BRANCH     Branch to push (default: current)
  --dry-run               Show what would be pushed without pushing

Examples:
  git-ops.zsh commit -m "feat: add user authentication"
  git-ops.zsh commit -m "fix(api): handle null pointer" --dry-run
  git-ops.zsh push
  git-ops.zsh push --force
  git-ops.zsh push --set-upstream

EOF
}

# Handle commit command
handle_commit() {
    typeset message=""
    typeset allow_empty=false
    typeset dry_run=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --message|-m)
                message="$2"
                shift 2
                ;;
            --allow-empty)
                allow_empty=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1" >&2
                show_usage
                exit 1
                ;;
        esac
    done

    # Validate required arguments
    if [[ -z "$message" ]]; then
        echo "Error: Commit message is required" >&2
        echo "Use: git-ops.zsh commit -m \"message\"" >&2
        exit 1
    fi

    # Check if in git repository
    if ! is_git_repo; then
        echo "Error: Not a git repository" >&2
        exit 2
    fi

    # Step 1: Check for changes to commit
    if ! has_staged_changes; then
        if [[ "$allow_empty" != "true" ]]; then
            echo "Error: No staged changes to commit" >&2
            echo "Stage changes with 'git add' or use --allow-empty" >&2
            exit 2
        fi
    fi

    # Step 2: Read style configuration from CLAUDE.md
    typeset commit_style=$(detect_commit_style)
    typeset attribution=$(detect_attribution_setting)

    echo "Commit style: $commit_style" >&2
    echo "Attribution: $attribution" >&2

    # Step 3: Validate message structure (based on style)
    if ! validate_commit_message "$message" "$commit_style"; then
        exit 1
    fi

    # Step 4: Apply style transformations
    typeset styled_message=$(apply_commit_style "$message" "$commit_style")

    # Step 5: Filter attribution
    if [[ "$attribution" == "none" ]]; then
        styled_message=$(remove_attribution "$styled_message")
    fi

    echo "Styled message: $styled_message" >&2

    # Step 6: Show what would be committed (if dry-run or verbose)
    if [[ "$dry_run" == "true" ]]; then
        echo "" >&2
        echo "Would commit with message:" >&2
        echo "---" >&2
        echo "$styled_message" >&2
        echo "---" >&2
        echo "" >&2
        echo "Changes to be committed:" >&2
        git diff --cached --stat
        exit 0
    fi

    # Step 7: Create commit
    typeset -a commit_flags=()
    if [[ "$allow_empty" == "true" ]]; then
        commit_flags+=(--allow-empty)
    fi

    if ! git commit -m "$styled_message" "${commit_flags[@]}"; then
        echo "Error: Failed to create commit" >&2
        exit 2
    fi

    typeset commit_sha=$(git rev-parse HEAD)
    echo "✅ Commit created: $commit_sha" >&2

    # Step 8: Check for pre-commit hook changes
    if files_were_modified_by_hooks; then
        handle_hook_modifications
    fi

    # Return success
    exit 0
}

# Handle push command
handle_push() {
    typeset force=false
    typeset set_upstream=false
    typeset dry_run=false
    typeset branch=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force|-f)
                force=true
                shift
                ;;
            --set-upstream|-u)
                set_upstream=true
                shift
                ;;
            --branch|-b)
                branch="$2"
                shift 2
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1" >&2
                show_usage
                exit 1
                ;;
        esac
    done

    # Check if in git repository
    if ! is_git_repo; then
        echo "Error: Not a git repository" >&2
        exit 2
    fi

    # Get current branch if not specified
    if [[ -z "$branch" ]]; then
        branch=$(get_current_branch)
        if [[ -z "$branch" ]]; then
            echo "Error: Not on any branch (detached HEAD)" >&2
            exit 2
        fi
    fi

    echo "Branch: $branch" >&2

    # Step 1: Branch protection check
    if is_protected_branch "$branch"; then
        if [[ "$force" == "true" ]]; then
            echo "❌ ERROR: Force push to protected branch '$branch' is not allowed" >&2
            echo "" >&2
            echo "Protected branches: main, master" >&2
            echo "Force-push is only allowed on feature branches." >&2
            exit 1
        fi
    fi

    # Step 2: Check if remote exists
    if ! check_remote_exists; then
        echo "Error: No remote 'origin' configured" >&2
        echo "Add a remote with: git remote add origin <url>" >&2
        exit 2
    fi

    # Step 3: Check upstream
    if ! has_upstream "$branch"; then
        if [[ "$set_upstream" == "true" ]]; then
            echo "Setting upstream for branch '$branch'" >&2

            if [[ "$dry_run" == "true" ]]; then
                echo "Would execute: git push -u origin $branch" >&2
                exit 0
            fi

            if git push -u origin "$branch"; then
                echo "✅ Pushed and set upstream for '$branch'" >&2
                exit 0
            else
                echo "Error: Failed to push and set upstream" >&2
                exit 2
            fi
        else
            echo "Error: Branch '$branch' has no upstream" >&2
            echo "Use --set-upstream to create it: git-ops.zsh push --set-upstream" >&2
            exit 2
        fi
    fi

    # Step 4: Check if ahead/behind remote
    typeset -i ahead=$(count_commits_ahead "$branch")
    typeset -i behind=$(count_commits_behind "$branch")

    if [[ "$behind" -gt 0 ]]; then
        echo "⚠️  Branch is $behind commit(s) behind remote" >&2
        echo "Consider pulling before pushing" >&2
    fi

    if [[ "$ahead" -eq 0 ]]; then
        echo "ℹ️  Branch is up to date with remote (nothing to push)" >&2
        exit 0
    fi

    echo "Branch is $ahead commit(s) ahead of remote" >&2

    # Step 5: Push with appropriate flags
    typeset push_cmd="git push"
    if [[ "$force" == "true" ]]; then
        echo "⚠️  Force pushing to '$branch'" >&2
        push_cmd="git push --force-with-lease"
    fi

    if [[ "$dry_run" == "true" ]]; then
        echo "Would execute: $push_cmd" >&2
        exit 0
    fi

    if $push_cmd; then
        if [[ "$force" == "true" ]]; then
            echo "✅ Force-pushed to '$branch'" >&2
        else
            echo "✅ Pushed to '$branch'" >&2
        fi
        exit 0
    else
        echo "Error: Failed to push" >&2
        exit 2
    fi
}

# Main command routing
main() {
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 1
    fi

    typeset command=$1
    shift

    case "$command" in
        commit)
            handle_commit "$@"
            ;;
        push)
            handle_push "$@"
            ;;
        --help|-h|help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown command: $command" >&2
            show_usage
            exit 1
            ;;
    esac
}

# Execute main
main "$@"
