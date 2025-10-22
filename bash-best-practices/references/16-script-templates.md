# Bash Script Templates

Production-ready templates for common Bash scripting scenarios.

## Basic Script Template

Use this template as a starting point for new Bash scripts:

```bash
#!/usr/bin/env bash
#
# Script: my-script.sh
# Description: Brief description of what this script does
# Usage: my-script.sh [OPTIONS] <args>
# Requires: Bash 4.0+, jq, curl (list dependencies)

# Strict error handling
set -euo pipefail

# Bash version check (add if using Bash 4+ features like mapfile)
if [[ "${BASH_VERSINFO[0]}" -lt 4 ]]; then
    echo "Error: Bash 4.0+ required (current: ${BASH_VERSION})" >&2
    echo "Install: brew install bash  (macOS)" >&2
    exit 1
fi

# Script directory detection (works when symlinked)
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

# Trap errors and provide context
trap 'echo "Error: Command failed at line $LINENO" >&2' ERR

# Cleanup function
cleanup() {
    local exit_code=$?

    # Remove temporary files
    if [[ -n "${tmp_dir:-}" ]] && [[ -d "$tmp_dir" ]]; then
        rm -rf "$tmp_dir"
    fi

    return "$exit_code"
}

# Register cleanup for all exit scenarios
trap cleanup EXIT

# Main script logic
main() {
    # Check arguments
    if [[ $# -lt 1 ]]; then
        echo "Usage: $SCRIPT_NAME <arg>" >&2
        return 1
    fi

    # Create temporary directory
    local tmp_dir
    tmp_dir="$(mktemp -d -t "${SCRIPT_NAME%.sh}.XXXXXX")"

    # Your logic here
    local input="$1"
    echo "Processing: $input"

    # ...

    return 0
}

# Run main with all arguments
main "$@"
```

## Template Design Rationale

1. **`set -euo pipefail`**: Strict error handling (exit on error, undefined vars, pipe failures)
2. **Version check**: Ensures Bash 4.0+ for modern features (omit if Bash 3.2 compatible)
3. **`readonly`**: Immutable constants for script metadata
4. **`trap ... ERR`**: Reports line number on errors
5. **`trap cleanup EXIT`**: Automatic resource cleanup
6. **`${BASH_SOURCE[0]}`**: Reliable script path (works with sourcing and symlinks)
7. **Temporary directory**: Safe location with automatic cleanup

## Script with Command-Line Arguments

```bash
#!/usr/bin/env bash
set -euo pipefail

show_help() {
    cat << 'EOF'
Usage: script.sh [OPTIONS] <input>

Options:
  -v, --verbose    Enable verbose output
  -o, --output DIR Output directory
  -h, --help       Show this help message

Arguments:
  input            Input file to process
EOF
}

main() {
    local verbose=false
    local output_dir="."
    local input_file=""

    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--verbose)
                verbose=true
                shift
                ;;
            -o|--output)
                output_dir="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                return 0
                ;;
            -*)
                echo "Error: Unknown option: $1" >&2
                show_help
                return 1
                ;;
            *)
                input_file="$1"
                shift
                ;;
        esac
    done

    # Validate required arguments
    if [[ -z "$input_file" ]]; then
        echo "Error: Input file required" >&2
        show_help
        return 1
    fi

    # Your logic here
    if [[ "$verbose" == true ]]; then
        echo "Processing $input_file -> $output_dir"
    fi
}

main "$@"
```

## Library/Sourced File Template

For files meant to be sourced (not executed):

```bash
#!/usr/bin/env bash
# Library: my-functions.sh
# Description: Reusable utility functions
#
# Usage: source my-functions.sh

# Prevent double-sourcing
if [[ -n "${MY_FUNCTIONS_LOADED:-}" ]]; then
    return 0
fi
readonly MY_FUNCTIONS_LOADED=true

# Library functions go here
get_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

log_message() {
    local level="$1"
    shift
    echo "[$(get_timestamp)] [$level] $*" >&2
}

# Example usage validation
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: This file should be sourced, not executed" >&2
    echo "Usage: source ${BASH_SOURCE[0]}" >&2
    exit 1
fi
```

## Processing Pipeline Template

For scripts that process data through multiple stages:

```bash
#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Pipeline stage 1: Extract
extract_data() {
    local input="$1"
    # Extract logic
    cat "$input"
}

# Pipeline stage 2: Transform
transform_data() {
    local -a lines
    mapfile -t lines

    for line in "${lines[@]}"; do
        # Transform logic
        echo "${line^^}"  # Convert to uppercase
    done
}

# Pipeline stage 3: Load
load_data() {
    local output="$1"
    # Load logic
    cat > "$output"
}

main() {
    local input_file="$1"
    local output_file="$2"

    extract_data "$input_file" | \
        transform_data | \
        load_data "$output_file"
}

main "$@"
```

## Parallel Processing Template

For scripts that need to process items in parallel:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Bash 5.x required for wait -n
if [[ "${BASH_VERSINFO[0]}" -lt 5 ]] && [[ "${BASH_VERSINFO[0]}" -eq 4 && "${BASH_VERSINFO[1]}" -lt 3 ]]; then
    echo "Error: Bash 4.3+ required for parallel processing" >&2
    exit 1
fi

readonly MAX_JOBS=4

process_item() {
    local item="$1"
    # Processing logic
    echo "Processing: $item"
    sleep 1
}

main() {
    local -a items=("item1" "item2" "item3" "item4" "item5" "item6")
    local job_count=0

    for item in "${items[@]}"; do
        # Start background job
        process_item "$item" &

        job_count=$((job_count + 1))

        # Wait if we've reached max jobs
        if [[ $job_count -ge $MAX_JOBS ]]; then
            wait -n  # Wait for any job to complete
            job_count=$((job_count - 1))
        fi
    done

    # Wait for remaining jobs
    wait
}

main "$@"
```

## Testing-Friendly Template

For scripts designed with testability in mind:

```bash
#!/usr/bin/env bash
set -euo pipefail

# All business logic in functions for easy testing
calculate_result() {
    local input="$1"
    local result=$((input * 2))
    echo "$result"
}

validate_input() {
    local input="$1"

    if [[ ! "$input" =~ ^[0-9]+$ ]]; then
        echo "Error: Input must be a number" >&2
        return 1
    fi

    return 0
}

main() {
    local input="$1"

    if ! validate_input "$input"; then
        return 1
    fi

    local result
    result=$(calculate_result "$input")
    echo "Result: $result"
}

# Only run main if executed (not if sourced for testing)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

## Related References

- [02-strict-mode.md](02-strict-mode.md) - Understanding strict mode variations
- [08-common-patterns.md](08-common-patterns.md) - Additional patterns and snippets
- [06-error-handling.md](06-error-handling.md) - Error handling strategies
- [15-function-libraries.md](15-function-libraries.md) - Organizing reusable functions
