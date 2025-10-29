# Function Libraries and Code Organization

Guide for organizing reusable functions in Bash scripts and when to extract them into library files.

## Philosophy

**Good code organization**:
- Makes functions discoverable and reusable
- Reduces duplication across scripts
- Enables testing in isolation
- Clarifies dependencies and concerns

**Balance**: Don't over-engineer. Extract to libraries when you have genuine reuse, not speculative "maybe someday."

## When to Keep Functions Inline

### Keep in Main Script When

✅ **Function is used only in this script**
```bash
#!/usr/bin/env bash
set -euo pipefail

# Used only here - keep inline
validate_input() {
    local file="$1"
    [[ -f "$file" ]] || { echo "File not found: $file" >&2; return 1; }
}

main() {
    validate_input "$1"
    # ... rest of script
}
```

✅ **Function is tightly coupled to script logic**
```bash
# This cleanup is specific to this script's temp files
cleanup() {
    rm -rf "$TMP_DIR"
    docker stop "$CONTAINER_ID" 2>/dev/null || true
}
```

✅ **Script is small (< 200 lines) with few functions**
- Overhead of library structure outweighs benefits
- All code is visible in one file

## When to Extract to Library

### Extract to Library When

✅ **Function is reused across 2+ scripts**
```bash
# git-functions.sh - Shared across multiple scripts
get_current_branch() {
    git rev-parse --abbrev-ref HEAD
}

get_repo_root() {
    git rev-parse --show-toplevel
}
```

✅ **Function provides domain-specific utilities**
```bash
# jira-functions.sh - JIRA-specific operations
get_ticket_status() {
    local ticket="$1"
    jira view "$ticket" --template='{{.fields.status.name}}'
}

get_ticket_summary() {
    local ticket="$1"
    jira view "$ticket" --template='{{.fields.summary}}'
}
```

✅ **Functions form a cohesive module**
```bash
# validation-functions.sh - All validation logic
validate_email() { ... }
validate_url() { ... }
validate_semver() { ... }
```

✅ **Script is getting large (> 300 lines)**
- Extract reusable chunks to libraries
- Keeps main script focused on orchestration

## Library Organization Patterns

### Pattern 1: `lib/` Directory Structure (Recommended)

**Best for**: Projects with multiple related scripts

```bash
project/
├── main-script.sh           # Primary entry point
├── deploy.sh                # Deployment script
├── backup.sh                # Backup script
└── lib/                     # Shared function libraries
    ├── git-functions.sh     # Git operations
    ├── config-functions.sh  # Configuration management
    ├── jira-functions.sh    # JIRA integration
    └── validation-functions.sh  # Input validation
```

**Usage in scripts**:
```bash
#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source libraries
source "${SCRIPT_DIR}/lib/git-functions.sh"
source "${SCRIPT_DIR}/lib/config-functions.sh"

main() {
    local branch
    branch=$(get_current_branch)  # From git-functions.sh
    echo "On branch: $branch"
}
```

### Pattern 2: Single `functions.sh` Library

**Best for**: Small projects with few shared functions

```bash
project/
├── deploy.sh
├── backup.sh
└── functions.sh    # All shared functions
```

**Usage**:
```bash
#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/functions.sh"
```

### Pattern 3: Prefixed Files in Same Directory

**Best for**: Very simple projects, quick scripts

```bash
project/
├── main.sh
├── lib-git.sh        # Git utilities
├── lib-docker.sh     # Docker utilities
└── lib-utils.sh      # General utilities
```

## Library File Structure

### Recommended Library Template

```bash
#!/usr/bin/env bash
#
# Library: git-functions.sh
# Description: Git repository operations
# Dependencies: git (required)
#
# Usage:
#   source "$(dirname "${BASH_SOURCE[0]}")/git-functions.sh"

# Prevent re-sourcing
[[ -n "${_GIT_FUNCTIONS_LOADED:-}" ]] && return 0
readonly _GIT_FUNCTIONS_LOADED=1

# Library-specific strict mode (optional, can rely on caller's settings)
set -euo pipefail

# ============================================================================
# Public Functions
# ============================================================================

# Get the current git branch name
# Returns: Branch name (e.g., "main", "feature/foo")
# Exits: 1 if not in a git repository
get_current_branch() {
    git rev-parse --abbrev-ref HEAD 2>/dev/null || {
        echo "Error: Not in a git repository" >&2
        return 1
    }
}

# Get the git repository root directory
# Returns: Absolute path to repository root
# Exits: 1 if not in a git repository
get_repo_root() {
    git rev-parse --show-toplevel 2>/dev/null || {
        echo "Error: Not in a git repository" >&2
        return 1
    }
}

# Check if current branch is clean (no uncommitted changes)
# Returns: 0 if clean, 1 if dirty
is_branch_clean() {
    [[ -z $(git status --porcelain) ]]
}

# ============================================================================
# Private Functions (internal use only)
# ============================================================================

# Private functions prefixed with underscore
_validate_git_installed() {
    command -v git >/dev/null 2>&1 || {
        echo "Error: git is not installed" >&2
        return 1
    }
}
```

### Key Elements

1. **Header comment**: Purpose, dependencies, usage
2. **Re-sourcing guard**: Prevent multiple loads
3. **Strict mode**: Optional (can rely on caller)
4. **Public functions**: Main API, well-documented
5. **Private functions**: Prefixed with `_`, internal use only

## Sourcing Best Practices

### Always Use Absolute Paths

```bash
# ✅ GOOD: Absolute path using SCRIPT_DIR
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/functions.sh"

# ❌ BAD: Relative path (breaks if PWD changes)
source "./lib/functions.sh"

# ❌ BAD: Assumes location (fragile)
source "/usr/local/lib/functions.sh"
```

### Source at Top of Script

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Script metadata
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

# 2. Source libraries BEFORE using them
source "${SCRIPT_DIR}/lib/config-functions.sh"
source "${SCRIPT_DIR}/lib/git-functions.sh"

# 3. Now define script-specific functions
main() {
    # Can use sourced functions here
    local branch
    branch=$(get_current_branch)
}
```

### Check Sourcing Succeeded

```bash
# For critical libraries
source "${SCRIPT_DIR}/lib/required-functions.sh" || {
    echo "Error: Failed to load required-functions.sh" >&2
    exit 1
}

# For optional libraries
if [[ -f "${SCRIPT_DIR}/lib/optional-functions.sh" ]]; then
    source "${SCRIPT_DIR}/lib/optional-functions.sh"
fi
```

## Function Organization by Concern

### Organize by Domain, Not Type

**✅ GOOD: Organized by domain**
```bash
lib/
├── git-functions.sh         # Git operations
├── jira-functions.sh        # JIRA operations
├── docker-functions.sh      # Docker operations
└── kubernetes-functions.sh  # Kubernetes operations
```

**❌ BAD: Organized by type**
```bash
lib/
├── getters.sh      # Mixed: get_branch, get_ticket, get_container
├── setters.sh      # Mixed: set_config, set_status, set_label
└── validators.sh   # Mixed: validate_git, validate_jira, validate_docker
```

**Why**: Domain organization makes it clear which library to source and reduces coupling.

### Granularity Guidelines

**Too granular** (overhead outweighs benefits):
```bash
lib/
├── get-current-branch.sh    # Single function
├── get-repo-root.sh         # Single function
└── is-branch-clean.sh       # Single function
```

**Good granularity** (cohesive modules):
```bash
lib/
└── git-functions.sh         # All git-related functions
```

**Rule of thumb**:
- **Minimum**: 3-5 related functions per library
- **Maximum**: 20-30 functions (split if larger)

## Naming Conventions

### Library Files

```bash
# ✅ GOOD: Descriptive, domain-specific
git-functions.sh
config-functions.sh
validation-functions.sh
kubernetes-deploy-functions.sh

# ❌ BAD: Too generic
utils.sh         # What kind of utils?
helpers.sh       # What do they help with?
common.sh        # Too vague
```

### Functions

```bash
# Public functions: lowercase_with_underscores
get_current_branch() { ... }
validate_email() { ... }
deploy_to_kubernetes() { ... }

# Private functions: _leading_underscore
_validate_git_installed() { ... }
_parse_config_file() { ... }
```

## Dependency Management

### Declare Dependencies in Header

```bash
#!/usr/bin/env bash
#
# Library: kubernetes-functions.sh
# Dependencies:
#   - kubectl (required)
#   - jq (required)
#   - yq (optional, for YAML manipulation)

# Check required dependencies
_check_dependencies() {
    local missing=()

    command -v kubectl >/dev/null || missing+=("kubectl")
    command -v jq >/dev/null || missing+=("jq")

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "Error: Missing required dependencies: ${missing[*]}" >&2
        return 1
    fi
}

# Run dependency check when sourced
_check_dependencies || return 1
```

### Library Inter-Dependencies

```bash
# config-functions.sh depends on validation-functions.sh

#!/usr/bin/env bash
# Library: config-functions.sh
# Dependencies: validation-functions.sh, jq

# Source dependencies
readonly LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${LIB_DIR}/validation-functions.sh"

load_config() {
    local config_file="$1"

    # Use function from validation-functions.sh
    validate_json_file "$config_file" || return 1

    # ... rest of function
}
```

**Note**: Keep dependency chains shallow (1-2 levels max) to avoid complexity.

## Testing Library Functions

### Make Libraries Testable

```bash
# lib/git-functions.sh

get_current_branch() {
    # Testable: Doesn't exit on error, returns error code
    git rev-parse --abbrev-ref HEAD 2>/dev/null || return 1
}

# lib/git-functions.test.sh (simple test script)

#!/usr/bin/env bash
set -euo pipefail

readonly TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${TEST_DIR}/git-functions.sh"

test_get_current_branch() {
    local branch
    branch=$(get_current_branch)

    if [[ -z "$branch" ]]; then
        echo "FAIL: get_current_branch returned empty" >&2
        return 1
    fi

    echo "PASS: get_current_branch returned: $branch"
}

# Run tests
test_get_current_branch
```

### Use Mocking for External Commands

```bash
# lib/git-functions.sh

# Allow overriding git command for testing
GIT_CMD="${GIT_CMD:-git}"

get_current_branch() {
    $GIT_CMD rev-parse --abbrev-ref HEAD 2>/dev/null || return 1
}

# Test script can set GIT_CMD to a mock
# GIT_CMD="./mock-git.sh" bash test.sh
```

## Common Patterns

### Pattern 1: Configuration Loading

```bash
# lib/config-functions.sh

load_config() {
    local config_file="$1"

    [[ -f "$config_file" ]] || {
        echo "Error: Config file not found: $config_file" >&2
        return 1
    }

    # Load config using jq
    local config
    config=$(jq -c '.' "$config_file") || {
        echo "Error: Invalid JSON in $config_file" >&2
        return 1
    }

    echo "$config"
}

get_config_value() {
    local config="$1"
    local key="$2"
    local default="${3:-}"

    echo "$config" | jq -r ".${key} // \"${default}\""
}
```

### Pattern 2: Retry Logic

```bash
# lib/retry-functions.sh

retry() {
    local max_attempts="${1:-3}"
    local delay="${2:-5}"
    shift 2
    local cmd=("$@")

    local attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if "${cmd[@]}"; then
            return 0
        fi

        echo "Attempt $attempt/$max_attempts failed, retrying in ${delay}s..." >&2
        sleep "$delay"
        ((attempt++))
    done

    echo "Error: All $max_attempts attempts failed" >&2
    return 1
}

# Usage: retry 5 10 curl -f https://api.example.com
```

### Pattern 3: Logging

```bash
# lib/logging-functions.sh

# Log levels
readonly LOG_DEBUG=0
readonly LOG_INFO=1
readonly LOG_WARN=2
readonly LOG_ERROR=3

LOG_LEVEL="${LOG_LEVEL:-$LOG_INFO}"

log_debug() { [[ $LOG_LEVEL -le $LOG_DEBUG ]] && echo "[DEBUG] $*" >&2; }
log_info()  { [[ $LOG_LEVEL -le $LOG_INFO  ]] && echo "[INFO]  $*" >&2; }
log_warn()  { [[ $LOG_LEVEL -le $LOG_WARN  ]] && echo "[WARN]  $*" >&2; }
log_error() { [[ $LOG_LEVEL -le $LOG_ERROR ]] && echo "[ERROR] $*" >&2; }

# Usage:
# log_info "Starting deployment"
# log_error "Deployment failed"
```

### Pattern 4: Environment Detection

```bash
# lib/platform-functions.sh

is_macos() {
    [[ "$(uname -s)" == "Darwin" ]]
}

is_linux() {
    [[ "$(uname -s)" == "Linux" ]]
}

get_os_type() {
    case "$(uname -s)" in
        Darwin) echo "macos" ;;
        Linux)  echo "linux" ;;
        MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
        *) echo "unknown" ;;
    esac
}
```

## Migration Strategy

### Refactoring Inline Functions to Library

**Step 1**: Identify reusable functions
```bash
# Before: Everything in main.sh
main.sh (500 lines)
├── get_current_branch()      # Used in deploy.sh too
├── validate_email()          # Used in signup.sh too
├── deploy_specific_function()  # Only used here
└── main()
```

**Step 2**: Create lib directory and extract
```bash
# After: Extracted to libraries
project/
├── main.sh (300 lines)
├── deploy.sh
├── signup.sh
└── lib/
    ├── git-functions.sh      # get_current_branch()
    └── validation-functions.sh  # validate_email()

# deploy_specific_function() stays in main.sh
```

**Step 3**: Update scripts to source libraries
```bash
# main.sh
source "${SCRIPT_DIR}/lib/git-functions.sh"
source "${SCRIPT_DIR}/lib/validation-functions.sh"

# deploy.sh
source "${SCRIPT_DIR}/lib/git-functions.sh"

# signup.sh
source "${SCRIPT_DIR}/lib/validation-functions.sh"
```

## Anti-Patterns

### Anti-Pattern 1: God Object Library

```bash
# ❌ BAD: Everything in one library
lib/utils.sh (2000 lines)
├── get_current_branch()
├── validate_email()
├── deploy_to_kubernetes()
├── parse_json()
├── send_slack_message()
└── ... 50 more unrelated functions

# ✅ GOOD: Organized by domain
lib/
├── git-functions.sh
├── validation-functions.sh
├── kubernetes-functions.sh
├── json-functions.sh
└── slack-functions.sh
```

### Anti-Pattern 2: Circular Dependencies

```bash
# ❌ BAD: Circular dependency
# config-functions.sh sources git-functions.sh
# git-functions.sh sources config-functions.sh

# ✅ GOOD: Linear dependency chain or shared base
lib/
├── base-functions.sh      # Shared utilities
├── config-functions.sh    # Sources base-functions.sh
└── git-functions.sh       # Sources base-functions.sh
```

### Anti-Pattern 3: Side Effects on Source

```bash
# ❌ BAD: Library runs code when sourced
# lib/database-functions.sh
DB_CONNECTION=$(connect_to_database)  # Runs immediately!

# ✅ GOOD: Library only defines functions
# lib/database-functions.sh
connect_to_database() {
    # Called explicitly by user
    ...
}
```

### Anti-Pattern 4: Global Variable Pollution

```bash
# ❌ BAD: Library uses generic global names
# lib/functions.sh
config="..."      # Conflicts with caller's $config
status="..."      # Conflicts with caller's $status

# ✅ GOOD: Library uses prefixed or local variables
# lib/git-functions.sh
_GIT_LIB_CONFIG="..."     # Prefixed
# Or use readonly to prevent accidental override
readonly GIT_LIB_VERSION="1.0"
```

## Summary

**When to extract to library**:
- Function reused across 2+ scripts
- Cohesive domain-specific module (5+ related functions)
- Main script exceeds 300 lines

**Organization**:
- Use `lib/` directory for multiple libraries
- One library per domain (git, jira, kubernetes, etc.)
- 5-30 functions per library (split if larger)

**Sourcing**:
- Use absolute paths with `SCRIPT_DIR`
- Source at top of script
- Check critical dependencies

**Naming**:
- `domain-functions.sh` for library files
- `function_name()` for public functions
- `_function_name()` for private functions

**Best practices**:
- Declare dependencies in header
- Prevent re-sourcing with guard
- Keep dependency chains shallow
- Make functions testable
- Avoid side effects on source

**Remember**: Don't over-engineer. Extract libraries when you have genuine reuse, not speculative "maybe someday." Start with inline functions and refactor when duplication appears.
