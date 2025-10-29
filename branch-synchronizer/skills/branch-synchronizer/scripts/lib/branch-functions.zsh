#!/usr/bin/env zsh
# Branch Functions - Branch discovery and merge status checking
# Adapted from charly-server-dev-tools git-functions.zsh

# Reset to known ZSH defaults (local to sourced functions)
emulate -L zsh

# Detect existing branches for a pattern
# Args: pattern (e.g., "PROJ-123"), project_root
# Returns: List of branches (one per line)
detect_existing_branches() {
    typeset pattern=$1
    typeset project_root=$2

    # Fetch latest branches
    if ! git -C "$project_root" fetch --all --prune >/dev/null 2>&1; then
        echo "Warning: Could not fetch from remote - continuing with local data" >&2
    fi

    # Find all remote branches containing the pattern
    typeset -a branches  # Explicit array declaration
    branches=()
    while IFS= read -r branch; do
        if [[ -n "$branch" ]]; then
            # Remove 'origin/' prefix and trim whitespace using ZSH pattern matching
            typeset clean_branch="${branch##[[:space:]]#}"
            clean_branch="${clean_branch#origin/}"
            clean_branch="${clean_branch%%[[:space:]]#}"
            branches+=("$clean_branch")
        fi
    done < <(git -C "$project_root" branch -r | grep -i "$pattern" | grep -v "HEAD")

    # Return branches (one per line)
    if [[ ${#branches[@]} -gt 0 ]]; then
        printf '%s\n' "${branches[@]}"
    fi
}

# Check if a pattern has been merged into base branch
# Args: pattern (e.g., "PROJ-123"), project_root, base_branch (optional, default: main)
# Returns: 0 if merged, 1 if not merged
check_if_pattern_merged() {
    typeset pattern=$1
    typeset project_root=${2:-.}
    typeset base_branch=${3:-main}

    echo "Checking if ${pattern} has been merged to ${base_branch}..." >&2

    # Fetch latest base branch
    if ! git -C "$project_root" fetch origin "${base_branch}" >/dev/null 2>&1; then
        echo "Warning: Could not fetch ${base_branch} from remote - using local data" >&2
    fi

    # Check 1: Look for merge commits with pattern in branch name or closes/fixes references
    # Pattern matches:
    #   - Merge branch 'feature/PATTERN/...' into 'main'
    #   - Closes PATTERN
    #   - Fixes PATTERN
    typeset merge_commits=$(git -C "$project_root" log --merges --grep="Merge.*${pattern}\|Closes ${pattern}\|Fixes ${pattern}" --oneline "origin/${base_branch}" 2>/dev/null)

    if [[ -n "$merge_commits" ]]; then
        echo "Pattern ${pattern} has been merged into ${base_branch}:" >&2
        echo "$merge_commits" | head -3 >&2
        return 0
    fi

    # Check 2: Look for branch references in commit messages (first line only, case-insensitive)
    # This catches: "PROJ-123: Feature description" or "[PROJ-123] Feature"
    # But excludes: mentions in commit body like documentation examples
    typeset branch_commits=$(git -C "$project_root" log --format="%s" "origin/${base_branch}" 2>/dev/null | grep -i "^${pattern}:\|^\[${pattern}\]" | head -3)

    if [[ -n "$branch_commits" ]]; then
        echo "Pattern ${pattern} appears to be directly committed to ${base_branch}:" >&2
        # Get the actual commit hashes for these
        while IFS= read -r subject; do
            git -C "$project_root" log --format="%h %s" --grep="^${subject}" --max-count=1 "origin/${base_branch}" 2>/dev/null
        done <<< "$branch_commits" >&2
        return 0
    fi

    echo "Pattern ${pattern} has not been merged to ${base_branch}" >&2
    return 1
}

# Find existing branch for a pattern (local or remote)
# Args: pattern (e.g., "PROJ-123"), project_root
# Returns: branch name if found, empty string if not (exit code 1)
find_ticket_branch() {
    typeset pattern=$1
    typeset project_root=${2:-.}

    echo "Searching for existing branches with ${pattern}..." >&2

    # Fetch latest branches
    if ! git -C "$project_root" fetch --all --prune >/dev/null 2>&1; then
        echo "Warning: Could not fetch from remote - continuing with local data" >&2
    fi

    typeset -a branches  # Explicit array declaration
    branches=()

    # Find remote branches containing the pattern (case-insensitive)
    while IFS= read -r branch; do
        if [[ -n "$branch" ]]; then
            # Remove 'origin/' prefix and trim whitespace using ZSH pattern matching
            typeset clean_branch="${branch##[[:space:]]#}"
            clean_branch="${clean_branch#origin/}"
            clean_branch="${clean_branch%%[[:space:]]#}"
            branches+=("$clean_branch")
        fi
    done < <(git -C "$project_root" branch -r 2>/dev/null | grep -i "${pattern}" | grep -v "HEAD")

    # Find local branches containing the pattern (case-insensitive)
    while IFS= read -r branch; do
        if [[ -n "$branch" ]]; then
            # Remove leading asterisk or plus sign (worktree marker) and trim whitespace using ZSH pattern matching
            typeset clean_branch="${branch##[[:space:]]#}"
            clean_branch="${clean_branch#[*+]}"
            clean_branch="${clean_branch##[[:space:]]#}"
            clean_branch="${clean_branch%%[[:space:]]#}"
            # Only add if not already in list
            typeset -i found=0
            for existing in "${branches[@]}"; do
                if [[ "$existing" == "$clean_branch" ]]; then
                    found=1
                    break
                fi
            done
            if (( ! found )); then
                branches+=("$clean_branch")
            fi
        fi
    done < <(git -C "$project_root" branch 2>/dev/null | grep -i "${pattern}")

    if [[ ${#branches[@]} -eq 0 ]]; then
        echo "No existing branches found for ${pattern}" >&2
        return 1
    fi

    echo "Found ${#branches[@]} branch(es) for ${pattern}:" >&2

    # If only one branch, use it
    if [[ ${#branches[@]} -eq 1 ]]; then
        echo "  → Using: ${branches[1]}" >&2
        echo "${branches[1]}"
        return 0
    fi

    # Multiple branches found - select the most recently updated one
    typeset most_recent=""
    typeset most_recent_date=""

    for branch in "${branches[@]}"; do
        echo "  - $branch" >&2

        # Try to get last commit date for this branch
        typeset branch_date=""

        # First try remote branch
        if git -C "$project_root" show-ref --verify --quiet "refs/remotes/origin/$branch" 2>/dev/null; then
            branch_date=$(git -C "$project_root" log -1 --format="%ci" "origin/$branch" 2>/dev/null)
        # Then try local branch
        elif git -C "$project_root" show-ref --verify --quiet "refs/heads/$branch" 2>/dev/null; then
            branch_date=$(git -C "$project_root" log -1 --format="%ci" "$branch" 2>/dev/null)
        fi

        if [[ -n "$branch_date" ]]; then
            if [[ -z "$most_recent_date" ]] || [[ "$branch_date" > "$most_recent_date" ]]; then
                most_recent="$branch"
                most_recent_date="$branch_date"
            fi
        fi
    done

    if [[ -n "$most_recent" ]]; then
        # ZSH-native substring: 1-based indexing (first 19 chars)
        echo "  → Using most recent: $most_recent (updated: ${most_recent_date[1,19]})" >&2
        echo "$most_recent"
        return 0
    else
        # Fallback to first branch if we couldn't determine dates
        echo "  → Using: ${branches[1]} (couldn't determine dates)" >&2
        echo "${branches[1]}"
        return 0
    fi
}

# List all branches matching a pattern with metadata
# Args: pattern (e.g., "PROJ-123"), project_root
# Returns: JSON array with branch info
list_matching_branches() {
    typeset pattern=$1
    typeset project_root=${2:-.}

    # Fetch latest branches
    if ! git -C "$project_root" fetch --all --prune >/dev/null 2>&1; then
        echo "Warning: Could not fetch from remote - continuing with local data" >&2
    fi

    typeset -a branch_data  # Explicit array declaration
    branch_data=()

    # Find remote branches
    while IFS= read -r branch; do
        if [[ -n "$branch" ]]; then
            # Remove 'origin/' prefix and trim whitespace using ZSH pattern matching
            typeset clean_branch="${branch##[[:space:]]#}"
            clean_branch="${clean_branch#origin/}"
            clean_branch="${clean_branch%%[[:space:]]#}"
            typeset last_commit=$(git -C "$project_root" log -1 --format="%h %s" "origin/$clean_branch" 2>/dev/null | head -1)
            typeset last_date=$(git -C "$project_root" log -1 --format="%ci" "origin/$clean_branch" 2>/dev/null | head -1)

            # Build JSON object
            typeset branch_json=$(jq -n \
                --arg name "$clean_branch" \
                --arg last_commit "$last_commit" \
                --arg last_date "$last_date" \
                --arg location "remote" \
                '{
                    name: $name,
                    last_commit: $last_commit,
                    last_date: $last_date,
                    location: $location
                }')

            branch_data+=("$branch_json")
        fi
    done < <(git -C "$project_root" branch -r 2>/dev/null | grep -i "${pattern}" | grep -v "HEAD")

    # Output as JSON array
    if [[ ${#branch_data[@]} -gt 0 ]]; then
        # Combine all JSON objects into array
        printf '%s\n' "${branch_data[@]}" | jq -s '.'
    else
        echo "[]"
    fi
}

# Check if current branch is behind base branch
# Args: project_root, base_branch (optional, default: main)
# Returns: 0 if behind, 1 if up-to-date
is_branch_behind() {
    typeset project_root=${1:-.}
    typeset base_branch=${2:-main}

    # Fetch latest
    if ! git -C "$project_root" fetch origin "${base_branch}" >/dev/null 2>&1; then
        echo "Warning: Could not fetch ${base_branch} from remote - using local data" >&2
    fi

    typeset -i behind=$(git -C "$project_root" rev-list --count "HEAD..origin/${base_branch}" 2>/dev/null || echo "0")

    if [[ $behind -gt 0 ]]; then
        return 0
    else
        return 1
    fi
}

# Get branch comparison info
# Args: project_root, base_branch (optional, default: main)
# Returns: JSON with comparison data
get_branch_comparison() {
    typeset project_root=${1:-.}
    typeset base_branch=${2:-main}

    typeset current_branch=$(git -C "$project_root" branch --show-current)

    # Fetch latest
    if ! git -C "$project_root" fetch origin "${base_branch}" >/dev/null 2>&1; then
        echo "Warning: Could not fetch ${base_branch} from remote - using local data" >&2
    fi

    typeset -i ahead=$(git -C "$project_root" rev-list --count "origin/${base_branch}..HEAD" 2>/dev/null || echo "0")
    typeset -i behind=$(git -C "$project_root" rev-list --count "HEAD..origin/${base_branch}" 2>/dev/null || echo "0")

    jq -n \
        --arg current "$current_branch" \
        --arg base "$base_branch" \
        --argjson ahead "$ahead" \
        --argjson behind "$behind" \
        '{
            current_branch: $current,
            base_branch: $base,
            commits_ahead: $ahead,
            commits_behind: $behind,
            needs_rebase: ($behind > 0)
        }'
}
