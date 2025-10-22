#!/usr/bin/env zsh
# Core Worktree Functions - Fundamental git worktree operations
# Operates from outside worktree directories (black box approach)

# Reset to known ZSH defaults (for library consistency)
emulate -LR zsh

# Check if worktree exists and is valid
# Args: $1 - worktree name, $2 - project root
# Returns: "VALID:path", "INVALID:path", or "NOT_FOUND"
# Exit: 0 always (status in output)
check_worktree_status() {
    typeset worktree_name=$1
    typeset project_root=$2

    # Calculate worktree directory
    typeset worktree_base=$(get_worktree_base "$project_root")
    typeset worktree_dir="${worktree_base}/${worktree_name}"

    # Check if directory exists
    if [[ ! -d "$worktree_dir" ]]; then
        echo "NOT_FOUND"
        return 0
    fi

    # Check if it's registered as a git worktree
    if git -C "$project_root" worktree list | grep -q "$worktree_dir"; then
        echo "VALID:${worktree_dir}"
        return 0
    else
        echo "INVALID:${worktree_dir}"
        return 0
    fi
}

# Calculate worktree base directory from project root
# Args: $1 - project root path
# Returns: worktree base path (stdout)
# Exit: 0 on success
get_worktree_base() {
    typeset project_root=$1
    echo "${project_root}.worktrees"
}

# Detect if we're inside a git repository
# Args: $1 - directory to check (optional, defaults to current)
# Returns: project root path if in git repo
# Exit: 0 if in git repo, 1 otherwise
detect_git_root() {
    typeset check_dir=${1:-.}
    typeset root=$(git -C "$check_dir" rev-parse --show-toplevel 2>/dev/null)

    if [[ -z "$root" ]]; then
        return 1
    fi

    echo "$root"
    return 0
}

# Get current branch name from worktree
# Args: $1 - worktree directory path
# Returns: branch name (stdout)
# Exit: 0 on success, 1 if can't determine
get_worktree_branch() {
    typeset worktree_path=$1

    if [[ ! -d "$worktree_path" ]]; then
        return 1
    fi

    typeset branch=$(git -C "$worktree_path" branch --show-current 2>/dev/null)

    if [[ -z "$branch" ]]; then
        return 1
    fi

    echo "$branch"
    return 0
}

# List all worktrees for a project
# Args: $1 - project root
# Returns: JSON array of worktree info
# Exit: 0 on success
list_worktrees() {
    typeset project_root=$1

    typeset temp_file=$(mktemp -t worktree-list-XXXXXX.json)

    # Use ZSH always block for cleanup on function exit
    {
        # Get worktree list in porcelain format
    git -C "$project_root" worktree list --porcelain > "$temp_file" 2>/dev/null

    # Parse porcelain format into JSON array
    typeset -a worktrees
    typeset worktree_path=""
    typeset worktree_head=""
    typeset worktree_branch=""

    # ZSH regex: $MATCH = full match, ${match[1..n]} = capture groups (1-indexed)
    while IFS= read -r line; do
        if [[ "$line" =~ ^worktree\ (.*)$ ]]; then
            # Save previous worktree if exists
            if [[ -n "$worktree_path" ]]; then
                typeset wt_json=$(jq -n \
                    --arg path "$worktree_path" \
                    --arg head "$worktree_head" \
                    --arg branch "$worktree_branch" \
                    '{path: $path, head: $head, branch: $branch}')
                worktrees+=("$wt_json")
            fi

            # Start new worktree - extract path from first capture group
            worktree_path="${match[1]}"
            worktree_head=""
            worktree_branch=""
        elif [[ "$line" =~ ^HEAD\ (.*)$ ]]; then
            worktree_head="${match[1]}"
        elif [[ "$line" =~ ^branch\ (.*)$ ]]; then
            worktree_branch="${match[1]}"
        fi
    done < "$temp_file"

    # Save last worktree
    if [[ -n "$worktree_path" ]]; then
        typeset wt_json=$(jq -n \
            --arg path "$worktree_path" \
            --arg head "$worktree_head" \
            --arg branch "$worktree_branch" \
            '{path: $path, head: $head, branch: $branch}')
        worktrees+=("$wt_json")
    fi

        # Output as JSON array
        if [[ ${#worktrees[@]} -eq 0 ]]; then
            echo "[]"
        else
            printf '%s\n' "${worktrees[@]}" | jq -s '.'
        fi
    } always {
        # Cleanup temp file on function exit
        rm -f "$temp_file"
    }

    return 0
}

# Check if branch exists (local or remote)
# Args: $1 - project root, $2 - branch name
# Returns: "local", "remote", "both", or "none"
# Exit: 0 always
check_branch_exists() {
    typeset project_root=$1
    typeset branch_name=$2

    typeset has_local=false
    typeset has_remote=false

    # Check local branch
    if git -C "$project_root" show-ref --verify --quiet "refs/heads/$branch_name" 2>/dev/null; then
        has_local=true
    fi

    # Check remote branch
    if git -C "$project_root" show-ref --verify --quiet "refs/remotes/origin/$branch_name" 2>/dev/null; then
        has_remote=true
    fi

    if [[ "$has_local" == "true" ]] && [[ "$has_remote" == "true" ]]; then
        echo "both"
    elif [[ "$has_local" == "true" ]]; then
        echo "local"
    elif [[ "$has_remote" == "true" ]]; then
        echo "remote"
    else
        echo "none"
    fi

    return 0
}

# Validate inputs for worktree operations
# Args: $1 - worktree name, $2 - project root
# Returns: error message if invalid (stdout)
# Exit: 0 if valid, 1 if invalid
validate_worktree_inputs() {
    typeset worktree_name=$1
    typeset project_root=$2

    # Check worktree name is not empty
    if [[ -z "$worktree_name" ]]; then
        echo "Error: Worktree name is required" >&2
        return 1
    fi

    # Check project root is a directory
    if [[ ! -d "$project_root" ]]; then
        echo "Error: Project root does not exist: $project_root" >&2
        return 1
    fi

    # Check project root is a git repository
    if ! git -C "$project_root" rev-parse --git-dir &>/dev/null; then
        echo "Error: Not a git repository: $project_root" >&2
        return 1
    fi

    return 0
}
