# Common Patterns and Code Snippets

Practical, reusable patterns for ZSH scripts combining best practices from multiple sources.

## Script Template

### Comprehensive Script Template

```zsh
#!/usr/bin/env zsh
#
# Script: my-script.zsh
# Description: Does something useful
# Usage: my-script.zsh [OPTIONS] <arg>
# Requires: jq, curl

# Reset to known ZSH defaults and enable strict error handling
emulate -LR zsh
setopt ERR_EXIT       # Exit on error
setopt ERR_RETURN     # Return on error in function
setopt NO_UNSET       # Error on undefined variables
setopt PIPE_FAIL      # Fail if any command in pipeline fails
setopt EXTENDED_GLOB  # Enable extended globbing
setopt NULL_GLOB      # Don't error on no glob matches

# Script information (ZSH-specific, works when sourced too)
typeset -r ScriptPath="${(%):-%x}"
typeset -r ScriptDir="${${(%):-%x}:A:h}"
typeset -r ScriptName="${${(%):-%x}:t}"

# Cleanup function
cleanup() {
    # Remove temp files, etc.
    [[ -n "${TmpDir:-}" ]] && rm -rf "$TmpDir"
}

# Register cleanup
trap cleanup EXIT INT TERM

# Main script logic
main() {
    # Check arguments
    if [[ $# -lt 1 ]]; then
        echo "Usage: $ScriptName <arg>" >&2
        return 1
    fi

    # Create temp directory
    typeset -r TmpDir=$(mktemp -d -t "${ScriptName}-XXXXXX")

    # Your logic here
    echo "Processing: $1"

    return 0
}

# Run main with all arguments
main "$@"
```

## Logging Patterns

### Simple Logging

```zsh
#!/usr/bin/env zsh

# Log file location
typeset -r LOG_FILE="${HOME}/logs/script.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log_Message() {
    local level="$1"
    local message="$2"

    # Create log file if it doesn't exist
    if [[ ! -f "$LOG_FILE" ]]; then
        touch "$LOG_FILE" || {
            echo "Error: Cannot create log file: $LOG_FILE" >&2
            return 1
        }
    fi

    # Write log entry
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" >> "$LOG_FILE" || {
        echo "Error: Cannot write to log file: $LOG_FILE" >&2
        return 1
    }
}

# Usage
log_Message "INFO" "Script started"
log_Message "ERROR" "Something went wrong"
log_Message "DEBUG" "Debug information"
```

### Logging with Console Output

```zsh
# Log to both file and console
log_Message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local logEntry="$timestamp [$level] $message"

    # Write to log file
    echo "$logEntry" >> "$LOG_FILE" 2>/dev/null

    # Also output to console
    echo "$logEntry"
}

# Level-specific functions
log_Info() {
    log_Message "INFO" "$1"
}

log_Error() {
    log_Message "ERROR" "$1" >&2  # Errors to stderr
}

log_Debug() {
    [[ "${DEBUG:-false}" == "true" ]] && log_Message "DEBUG" "$1"
}

# Usage
log_Info "Starting process"
log_Error "Failed to connect"
DEBUG=true log_Debug "Connection string: $conn"
```

## Temporary File Handling

### Safe Temporary Directory Pattern

```zsh
#!/usr/bin/env zsh
emulate -LR zsh
setopt ERR_EXIT NO_UNSET PIPE_FAIL

# Create temporary directory
typeset -r TmpDir=$(mktemp -d -t script-XXXXXX)

# Cleanup function
cleanup() {
    if [[ -n "${TmpDir:-}" ]] && [[ -d "$TmpDir" ]]; then
        rm -rf "$TmpDir"
        echo "Cleaned up: $TmpDir" >&2
    fi
}

# Register cleanup for all exit scenarios
trap cleanup EXIT INT TERM

# Use temporary directory
typeset -r tmpFile="${TmpDir}/data.json"
echo '{"key": "value"}' > "$tmpFile"

# Process file
jq '.key' "$tmpFile"

# Cleanup happens automatically
```

### Temporary File with Preserve Option

```zsh
#!/usr/bin/env zsh

# Option to preserve temp files
typeset Preserve=false

cleanup() {
    if [[ "$Preserve" == "false" ]]; then
        [[ -n "${TmpDir:-}" ]] && rm -rf "$TmpDir"
        echo "Cleaned up temp directory" >&2
    else
        echo "Preserved temp directory: $TmpDir" >&2
    fi
}

trap cleanup EXIT INT TERM

# Parse --preserve flag
while [[ $# -gt 0 ]]; do
    case "$1" in
        --preserve)
            Preserve=true
            shift
            ;;
        *)
            break
            ;;
    esac
done

# Create and use temp directory
typeset -r TmpDir=$(mktemp -d)
echo "Using temp directory: $TmpDir"

# ... do work ...
```

### Function-Level Cleanup with `always` Block

ZSH provides an `always` block for function-level cleanup that's more reliable than `trap` in certain contexts:

```zsh
#!/usr/bin/env zsh

# Using always block for function cleanup
process_Data() {
    typeset input_file="$1"
    typeset temp_file=$(mktemp -t process-XXXXXX)

    {
        # Main processing logic
        jq '.data' "$input_file" > "$temp_file"

        # Transform data
        while IFS= read -r line; do
            echo "Processing: $line"
        done < "$temp_file"

        # Return result
        return 0
    } always {
        # This runs on ALL function exits (success, error, return)
        rm -f "$temp_file"
    }
}

# Usage
process_Data "input.json"
```

**When to use `always` vs `trap`:**

| Pattern | Use Case | Scope |
|---------|----------|-------|
| `trap cleanup EXIT` | Script-level cleanup | Entire script |
| `{ } always { }` | Function-level cleanup | Single function |
| `trap 'cmd' RETURN` | ❌ **Don't use** - Not supported in ZSH strict mode |

**Why `always` is better for functions:**
- Works in all ZSH modes (including strict mode)
- Executes on any function exit (return, error, or natural end)
- Cleaner syntax for function-scoped cleanup
- Doesn't conflict with script-level traps

**Common mistake (from Bash):**
```zsh
# ❌ BAD - Bash idiom that fails in ZSH
my_function() {
    typeset temp=$(mktemp)
    trap "rm -f '$temp'" RETURN  # Error: undefined signal: RETURN
    # ...
}

# ✅ GOOD - ZSH way
my_function() {
    typeset temp=$(mktemp)
    {
        # ... function code ...
    } always {
        rm -f "$temp"
    }
}
```

## Argument Parsing

### Simple Argument Parsing

```zsh
#!/usr/bin/env zsh

# Default values
typeset Verbose=false
typeset OutputDir="/tmp/output"
typeset InputFile=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--verbose)
            Verbose=true
            shift
            ;;
        -o|--output)
            OutputDir="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [-v] [-o DIR] <input-file>"
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
        *)
            InputFile="$1"
            shift
            ;;
    esac
done

# Validate required arguments
if [[ -z "$InputFile" ]]; then
    echo "Error: Input file required" >&2
    exit 1
fi

# Use arguments
[[ "$Verbose" == "true" ]] && echo "Processing: $InputFile"
echo "Output directory: $OutputDir"
```

### Advanced Argument Parsing with typeset

```zsh
#!/usr/bin/env zsh

parse_Arguments() {
    typeset -A Config=(
        [verbose]=false
        [output]="/tmp"
        [count]=0
    )

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --verbose)
                Config[verbose]=true
                shift
                ;;
            --output)
                Config[output]="$2"
                shift 2
                ;;
            --count)
                Config[count]="$2"
                shift 2
                ;;
            *)
                Config[input]="$1"
                shift
                ;;
        esac
    done

    # Output config as key=value pairs
    for key in "${(@k)Config}"; do
        echo "$key=${Config[$key]}"
    done
}

# Usage
eval $(parse_Arguments "$@")
echo "Verbose: $verbose"
echo "Output: $output"
echo "Count: $count"
```

## Error Handling

### Robust Error Handling

```zsh
#!/usr/bin/env zsh
emulate -LR zsh
setopt ERR_EXIT ERR_RETURN NO_UNSET PIPE_FAIL

# Error handler
handle_Error() {
    local exitCode=$?
    local line=$1

    echo "ERROR: Command failed with exit code $exitCode at line $line" >&2
    echo "Command: ${(%):-%x}" >&2

    # Cleanup before exit
    cleanup

    exit $exitCode
}

# Register error handler
trap 'handle_Error $LINENO' ERR

# Cleanup function
cleanup() {
    # Cleanup resources
    :
}

trap cleanup EXIT INT TERM

# Functions with explicit error handling
fetch_Data() {
    local url="$1"
    local output="$2"

    if ! curl -sf "$url" > "$output" 2>&1; then
        echo "ERROR: Failed to fetch $url" >&2
        return 1
    fi

    if [[ ! -s "$output" ]]; then
        echo "ERROR: Empty response from $url" >&2
        return 1
    fi

    return 0
}

# Usage
if ! fetch_Data "https://api.example.com/data" "/tmp/data.json"; then
    echo "Failed to fetch data" >&2
    exit 1
fi
```

### Try-Catch Pattern

```zsh
# Emulate try-catch with functions
try() {
    "$@"
    return $?
}

catch() {
    local exitCode=$?
    if [[ $exitCode -ne 0 ]]; then
        "$@" $exitCode
    fi
    return 0
}

# Example error handler
on_Error() {
    local code=$1
    echo "Caught error with code: $code" >&2
    # Handle error
}

# Usage
try some_risky_command || catch on_Error
```

## Checking Dependencies

### Check Required Commands

```zsh
#!/usr/bin/env zsh

check_Dependencies() {
    typeset -a required=("$@")
    typeset -a missing=()

    for cmd in "${required[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "Error: Missing required commands:" >&2
        for cmd in "${missing[@]}"; do
            echo "  - $cmd" >&2
        done
        return 1
    fi

    return 0
}

# Usage
check_Dependencies git jq curl || exit 1
```

### Check with Installation Hints

```zsh
check_Command() {
    local cmd="$1"
    local hint="$2"

    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: Required command '$cmd' not found" >&2
        [[ -n "$hint" ]] && echo "Install: $hint" >&2
        return 1
    fi
    return 0
}

# Usage
check_Command "jq" "brew install jq" || exit 1
check_Command "gh" "brew install gh" || exit 1
```

## File and Directory Operations

### Safe Directory Changes

```zsh
# Save and restore directory
save_And_Restore_Dir() {
    typeset -r OriginalDir="$PWD"

    # Change directory
    cd "$1" || return 1

    # Do work
    "$2"

    # Restore
    cd "$OriginalDir"
}

# Or use subshell (automatic restoration)
process_In_Dir() {
    (
        cd "$1" || exit 1
        # Work here
        echo "In: $PWD"
    )
    # Back to original directory automatically
}
```

### Create Directory if Not Exists

```zsh
ensure_Directory() {
    local dir="$1"

    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir" || {
            echo "Error: Cannot create directory: $dir" >&2
            return 1
        }
        echo "Created directory: $dir"
    fi

    return 0
}

# Usage
ensure_Directory "/path/to/output" || exit 1
```

## Progress Indication

### Simple Progress Counter

```zsh
#!/usr/bin/env zsh

typeset -a files=(/path/to/files/*)
typeset -i total=${#files[@]}
typeset -i current=0

for file in "${files[@]}"; do
    (( current++ ))

    echo "Processing [$current/$total]: $file"

    # Process file
    sleep 0.1
done

echo "Completed: $total files"
```

### Progress with Percentage

```zsh
process_With_Progress() {
    typeset -a items=("$@")
    typeset -i total=${#items[@]}
    typeset -i current=0

    for item in "${items[@]}"; do
        (( current++ ))

        typeset -i percent=$((current * 100 / total))

        echo -ne "\rProcessing: $current/$total ($percent%)  "

        # Process item
        sleep 0.1
    done

    echo -e "\n✓ Completed"
}

# Usage
process_With_Progress "item1" "item2" "item3" "item4" "item5"
```

## Configuration File Handling

### Read Configuration File

```zsh
#!/usr/bin/env zsh

load_Config() {
    local configFile="$1"

    if [[ ! -f "$configFile" ]]; then
        echo "Error: Config file not found: $configFile" >&2
        return 1
    fi

    # Source configuration
    source "$configFile" || {
        echo "Error: Failed to load config: $configFile" >&2
        return 1
    }

    return 0
}

# Usage
typeset -r ConfigFile="${HOME}/.myapp/config.zsh"
load_Config "$ConfigFile" || exit 1
```

### JSON Configuration

```zsh
load_Json_Config() {
    local configFile="$1"

    if [[ ! -f "$configFile" ]]; then
        echo "Error: Config file not found: $configFile" >&2
        return 1
    fi

    # Validate JSON
    if ! jq empty "$configFile" 2>/dev/null; then
        echo "Error: Invalid JSON in $configFile" >&2
        return 1
    fi

    # Read values
    typeset -g API_BASE=$(jq -r '.api.base' "$configFile")
    typeset -g API_TOKEN=$(jq -r '.api.token' "$configFile")

    return 0
}
```

## Interactive Prompts

### Simple Confirmation

```zsh
confirm() {
    local prompt="$1"
    local response

    read "response?$prompt [y/N]: "

    case "$response" in
        [yY]|[yY][eE][sS])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Usage
if confirm "Delete all files?"; then
    echo "Deleting..."
else
    echo "Cancelled"
fi
```

### Select from Options

```zsh
select_Option() {
    local prompt="$1"
    shift
    local -a options=("$@")

    echo "$prompt"
    select opt in "${options[@]}"; do
        if [[ -n "$opt" ]]; then
            echo "$opt"
            return 0
        fi
    done
}

# Usage
choice=$(select_Option "Choose environment:" "Development" "Staging" "Production")
echo "Selected: $choice"
```

## Summary

### Essential Patterns

1. **Always use a script template** with emulate, error handling, and cleanup
2. **Use trap for script-level cleanup**, `always` blocks for function-level cleanup
3. **Log important operations** for debugging and auditing
4. **Check dependencies** before running main logic
5. **Handle errors explicitly** with meaningful messages
6. **Use temporary directories** safely with automatic cleanup
7. **Parse arguments** consistently with clear defaults
8. **Validate inputs** before processing
9. **Provide user feedback** (progress, confirmations)
10. **Document usage** in script header

### Quick Pattern Reference

```zsh
# Template start
#!/usr/bin/env zsh
emulate -LR zsh
setopt ERR_EXIT NO_UNSET PIPE_FAIL

# Script info
typeset -r ScriptDir="${${(%):-%x}:A:h}"

# Cleanup
cleanup() { rm -rf "${TmpDir:-}"; }
trap cleanup EXIT INT TERM

# Temp directory
typeset -r TmpDir=$(mktemp -d)

# Check dependencies
command -v jq &> /dev/null || { echo "jq required" >&2; exit 1; }

# Main logic
main() {
    # Your code
}

main "$@"
```
