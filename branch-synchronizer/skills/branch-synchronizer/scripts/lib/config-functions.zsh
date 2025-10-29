#!/usr/bin/env zsh
# Config Functions - Read ticket patterns from jira-analyzer.json
# Supports project-local and global configuration hierarchy

# Reset to known ZSH defaults (local to sourced functions)
emulate -L zsh

# Find jira-analyzer.json configuration file
# Checks project root first, then home directory
# Returns: path to config file, or empty string if not found
find_config_file() {
    typeset repo_root=${1:-.}

    # Try to find git repository root if path provided is within a repo
    if [[ -d "$repo_root/.git" ]] || git -C "$repo_root" rev-parse --git-dir >/dev/null 2>&1; then
        repo_root=$(git -C "$repo_root" rev-parse --show-toplevel 2>/dev/null || echo "$repo_root")
    fi

    # Check project-local config first (priority)
    typeset project_config="${repo_root}/.jira-analyzer.json"
    if [[ -f "$project_config" ]]; then
        echo "$project_config"
        return 0
    fi

    # Fallback to global config
    typeset global_config="${HOME}/.jira-analyzer.json"
    if [[ -f "$global_config" ]]; then
        echo "$global_config"
        return 0
    fi

    # No config found
    return 1
}

# Load ticket patterns from jira-analyzer.json
# Returns: Regex pattern for matching ticket prefixes (e.g., "CH2|FALL|CSC")
# Exits with error if no config found
load_ticket_patterns() {
    typeset repo_root=${1:-.}

    typeset config_file
    if ! config_file=$(find_config_file "$repo_root"); then
        echo "Error: No jira-analyzer.json found" >&2
        echo "  Checked:" >&2
        echo "    - ${repo_root}/.jira-analyzer.json (project-local)" >&2
        echo "    - ${HOME}/.jira-analyzer.json (global)" >&2
        echo "" >&2
        echo "Create a config file with ticket prefixes:" >&2
        echo '  { "instances": [{ "prefixes": ["PROJ", "BUG"] }] }' >&2
        return 1
    fi

    # Validate JSON
    if ! jq empty "$config_file" 2>/dev/null; then
        echo "Error: Invalid JSON in $config_file" >&2
        return 1
    fi

    # Extract all prefixes from all instances and build regex pattern
    typeset pattern
    pattern=$(jq -r '[.instances[].prefixes[]] | unique | join("|")' "$config_file")

    if [[ -z "$pattern" ]] || [[ "$pattern" == "null" ]]; then
        echo "Error: No prefixes found in $config_file" >&2
        echo "  Expected structure: { \"instances\": [{ \"prefixes\": [...] }] }" >&2
        return 1
    fi

    echo "$pattern"
    return 0
}

# Get all configured ticket prefixes as an array
# Returns: Space-separated list of prefixes
get_ticket_prefixes() {
    typeset repo_root=${1:-.}

    typeset config_file
    if ! config_file=$(find_config_file "$repo_root"); then
        return 1
    fi

    # Extract all prefixes and return as space-separated list
    jq -r '[.instances[].prefixes[]] | unique | join(" ")' "$config_file"
}

# Check if a ticket number matches configured patterns
# Args: ticket_number, repo_root (optional)
# Returns: 0 if valid, 1 if invalid
validate_ticket_pattern() {
    typeset ticket=$1
    typeset repo_root=${2:-.}

    typeset pattern
    if ! pattern=$(load_ticket_patterns "$repo_root"); then
        return 1
    fi

    # Build full regex: PREFIX-NUMBER
    typeset ticket_regex="^(${pattern})-[0-9]+$"

    if [[ "$ticket" =~ $ticket_regex ]]; then
        return 0
    else
        return 1
    fi
}

# Get configuration source (project or global)
# Returns: "project" or "global"
get_config_source() {
    typeset repo_root=${1:-.}

    if [[ -d "$repo_root/.git" ]] || git -C "$repo_root" rev-parse --git-dir >/dev/null 2>&1; then
        repo_root=$(git -C "$repo_root" rev-parse --show-toplevel 2>/dev/null || echo "$repo_root")
    fi

    if [[ -f "${repo_root}/.jira-analyzer.json" ]]; then
        echo "project"
    elif [[ -f "${HOME}/.jira-analyzer.json" ]]; then
        echo "global"
    else
        echo "none"
    fi
}
