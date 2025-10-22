#!/usr/bin/env zsh
# Branch Utilities - Parse branch names and extract ticket information
# Provides branch-aware functionality for ticket extraction

# Reset to known ZSH defaults (for library consistency)
emulate -LR zsh

# Extract ticket number from branch name
# Args: $1 - branch name
# Returns: ticket number if found (e.g., "PROJ-123"), empty if not found
# Exit: 0 if found, 1 if not found
extract_ticket_number() {
    typeset branch_name=$1

    # Common ticket patterns:
    # - PROJ-123 (Atlassian Cloud)
    # - PROJ-456 (Atlassian Cloud)
    # - PROJ-789 (Self-hosted JIRA)
    # - PROJ-456 (Generic)
    # Pattern: uppercase letters + optional digits + dash + digits

    # ZSH regex: $MATCH = full match, ${match[1..n]} = capture groups (1-indexed)
    if [[ "$branch_name" =~ ([A-Z]+[0-9]*-[0-9]+) ]]; then
        echo "${match[1]}"  # First capture group contains ticket number
        return 0
    fi

    return 1
}

# Parse branch name into components
# Args: $1 - branch name (e.g., "feature/PROJ-123/add-feature")
# Returns: JSON object with components
# Exit: 0 on success
parse_branch_name() {
    typeset branch_name=$1

    typeset branch_type=""
    typeset ticket=""
    typeset description=""

    # ZSH regex: $MATCH = full match, ${match[1..n]} = capture groups (1-indexed)
    # Extract branch type (feature, bugfix, hotfix, etc.)
    if [[ "$branch_name" =~ ^([^/]+)/ ]]; then
        branch_type="${match[1]}"  # First capture group
    fi

    # Extract ticket number
    ticket=$(extract_ticket_number "$branch_name")

    # Extract description (part after ticket or after type)
    if [[ -n "$ticket" ]]; then
        # Description comes after ticket
        if [[ "$branch_name" =~ ${ticket}/(.+)$ ]]; then
            description="${match[1]}"
        fi
    elif [[ -n "$branch_type" ]]; then
        # No ticket, description comes after type
        if [[ "$branch_name" =~ ^${branch_type}/(.+)$ ]]; then
            description="${match[1]}"
        fi
    else
        # No type prefix, entire name is description
        description="$branch_name"
    fi

    # Build JSON object
    jq -n \
        --arg branch "$branch_name" \
        --arg type "$branch_type" \
        --arg ticket "$ticket" \
        --arg desc "$description" \
        '{
            branch: $branch,
            type: $type,
            ticket: $ticket,
            description: $desc
        }'

    return 0
}

# Validate branch name format
# Args: $1 - branch name
# Returns: error message if invalid, empty if valid
# Exit: 0 if valid, 1 if invalid
validate_branch_name() {
    typeset branch_name=$1

    # Check not empty
    if [[ -z "$branch_name" ]]; then
        echo "Error: Branch name cannot be empty" >&2
        return 1
    fi

    # Check for invalid characters (git branch name rules)
    # Cannot contain: space, ~, ^, :, ?, *, [, \, .., @{, //
    if [[ "$branch_name" =~ [[:space:]~^:?*\[\]\\] ]] || \
       [[ "$branch_name" == *..* ]] || \
       [[ "$branch_name" =~ @\{ ]] || \
       [[ "$branch_name" =~ // ]]; then
        echo "Error: Branch name contains invalid characters" >&2
        return 1
    fi

    # Cannot start or end with /
    if [[ "$branch_name" =~ ^/ ]] || [[ "$branch_name" =~ /$ ]]; then
        echo "Error: Branch name cannot start or end with /" >&2
        return 1
    fi

    # Cannot start with -
    if [[ "$branch_name" =~ ^- ]]; then
        echo "Error: Branch name cannot start with -" >&2
        return 1
    fi

    return 0
}

# Generate branch name from components
# Args: $1 - ticket (optional), $2 - description (required)
# Returns: branch name (stdout)
# Exit: 0 on success
generate_branch_name() {
    typeset ticket=$1
    typeset description=$2

    # Sanitize description (lowercase, replace non-alphanumeric with dash, limit length)
    typeset sanitized_desc=$(echo "$description" | \
        tr '[:upper:]' '[:lower:]' | \
        sed 's/[^a-z0-9]/-/g' | \
        sed 's/--*/-/g' | \
        sed 's/^-//' | \
        sed 's/-$//' | \
        cut -c1-50)

    # Build branch name
    if [[ -n "$ticket" ]]; then
        echo "feature/${ticket}/${sanitized_desc}"
    else
        echo "feature/${sanitized_desc}"
    fi

    return 0
}

# Check if branch name contains a ticket number
# Args: $1 - branch name
# Returns: "true" or "false"
# Exit: 0 always
has_ticket_number() {
    typeset branch_name=$1

    if extract_ticket_number "$branch_name" &>/dev/null; then
        echo "true"
    else
        echo "false"
    fi

    return 0
}

# Extract project prefix from ticket number
# Args: $1 - ticket number (e.g., "PROJ-123")
# Returns: project prefix (e.g., "CH2")
# Exit: 0 on success, 1 if not a valid ticket format
extract_project_prefix() {
    typeset ticket=$1

    # ZSH regex: $MATCH = full match, ${match[1..n]} = capture groups (1-indexed)
    if [[ "$ticket" =~ ^([A-Z]+[0-9]*)-[0-9]+$ ]]; then
        echo "${match[1]}"  # First capture group contains project prefix
        return 0
    fi

    return 1
}

# List common ticket patterns for reference
# Returns: JSON array of ticket pattern examples
# Exit: 0 on success
list_ticket_patterns() {
    typeset patterns='[
  {
    "pattern": "PROJ-123",
    "description": "Atlassian Cloud - Project A project",
    "regex": "CH2-[0-9]+"
  },
  {
    "pattern": "PROJ-456",
    "description": "Atlassian Cloud - Project B project",
    "regex": "FALL-[0-9]+"
  },
  {
    "pattern": "PROJ-789",
    "description": "Self-hosted JIRA - CSC project",
    "regex": "CSC-[0-9]+"
  },
  {
    "pattern": "PROJ-456",
    "description": "Generic project pattern",
    "regex": "[A-Z]+-[0-9]+"
  },
  {
    "pattern": "ABC123-789",
    "description": "Project with numbers in prefix",
    "regex": "[A-Z]+[0-9]+-[0-9]+"
  }
]'

    echo "$patterns" | jq '.'
    return 0
}
