# Common Bash Patterns

Reusable patterns and templates for everyday scripting tasks.

## Script Templates

### Basic Script Template

```bash
#!/usr/bin/env bash
#
# Script: script-name.sh
# Description: Brief description
# Usage: script-name.sh [OPTIONS] <args>

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

cleanup() {
    # Cleanup code
    :
}

trap cleanup EXIT

main() {
    # Main logic
    echo "Hello, World!"
}

main "$@"
```

### Script with Arguments

```bash
#!/usr/bin/env bash
set -euo pipefail

show_help() {
    cat << EOF
Usage: ${0##*/} [OPTIONS] FILE

Options:
    -h, --help      Show this help
    -v, --verbose   Verbose output
    -o, --output    Output file
EOF
}

main() {
    local verbose=false
    local output_file=""
    local input_file=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -o|--output)
                output_file="$2"
                shift 2
                ;;
            *)
                input_file="$1"
                shift
                ;;
        esac
    done

    if [[ -z "$input_file" ]]; then
        echo "Error: Input file required" >&2
        show_help
        exit 1
    fi

    # Process
    echo "Processing: $input_file"
}

main "$@"
```

## File Operations

### Read File Line by Line

```bash
while IFS= read -r line; do
    echo "Line: $line"
done < file.txt
```

### Read File into Array

```bash
mapfile -t lines < file.txt

# Or older Bash
lines=()
while IFS= read -r line; do
    lines+=("$line")
done < file.txt
```

### Write to File

```bash
# Overwrite
echo "content" > file.txt

# Append
echo "more content" >> file.txt

# Write multiple lines
cat > file.txt << 'EOF'
Line 1
Line 2
Line 3
EOF
```

### Process Files in Directory

```bash
for file in *.txt; do
    [[ -f "$file" ]] || continue  # Skip if no matches
    echo "Processing: $file"
done

# Or with find
while IFS= read -r -d '' file; do
    echo "Processing: $file"
done < <(find . -name "*.txt" -print0)
```

## String Operations

### Check if String Contains Substring

```bash
string="Hello, World!"

if [[ "$string" == *"World"* ]]; then
    echo "Found"
fi
```

### String Replacement

```bash
text="foo bar foo"

# Replace first occurrence
echo "${text/foo/baz}"  # baz bar foo

# Replace all occurrences
echo "${text//foo/baz}"  # baz bar baz
```

### String Splitting

```bash
# Split on delimiter
IFS=',' read -ra parts <<< "a,b,c"
echo "${parts[0]}"  # a
echo "${parts[1]}"  # b

# Reset IFS
IFS=$' \t\n'
```

### Trim Whitespace

```bash
trim() {
    local var="$1"
    # Remove leading whitespace
    var="${var#"${var%%[![:space:]]*}"}"
    # Remove trailing whitespace
    var="${var%"${var##*[![:space:]]}"}"
    echo "$var"
}

result=$(trim "  hello  ")  # "hello"
```

## Date and Time

### Current Date/Time

```bash
# ISO 8601 format
date "+%Y-%m-%d"  # 2025-01-15

# Custom format
date "+%Y%m%d_%H%M%S"  # 20250115_143022

# Timestamp
date +%s  # 1705328162
```

### Date Arithmetic

```bash
# Yesterday
date -d "yesterday" "+%Y-%m-%d"  # Linux
date -v-1d "+%Y-%m-%d"  # macOS

# 7 days ago
date -d "7 days ago" "+%Y-%m-%d"  # Linux
date -v-7d "+%Y-%m-%d"  # macOS
```

## Looping Patterns

### Loop with Counter

```bash
for ((i=0; i<10; i++)); do
    echo "Iteration $i"
done
```

### Loop Until Success

```bash
until command_that_might_fail; do
    echo "Retrying..." >&2
    sleep 2
done
```

### Loop with Timeout

```bash
timeout=30
start=$(date +%s)

while true; do
    if (($(date +%s) - start > timeout)); then
        echo "Timeout" >&2
        break
    fi

    # Do work
    sleep 1
done
```

## Configuration Files

### Read Config File

```bash
# config.conf:
# KEY1=value1
# KEY2=value2

while IFS='=' read -r key value; do
    case $key in
        KEY1) config_key1="$value" ;;
        KEY2) config_key2="$value" ;;
    esac
done < config.conf
```

### Parse INI File

```bash
# config.ini:
# [section1]
# key1=value1
# [section2]
# key2=value2

current_section=""

while IFS= read -r line; do
    # Skip empty lines and comments
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue

    # Section header
    if [[ "$line" =~ ^\[(.+)\]$ ]]; then
        current_section="${BASH_REMATCH[1]}"
        continue
    fi

    # Key=value
    if [[ "$line" =~ ^([^=]+)=(.+)$ ]]; then
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        echo "[$current_section] $key = $value"
    fi
done < config.ini
```

## JSON Processing

### Parse JSON with jq

```bash
# Read JSON file
data=$(jq '.key' data.json)

# Parse JSON from command
data=$(curl -s https://api.example.com/data | jq '.results[]')

# Extract multiple fields
jq -r '.[] | "\(.name): \(.value)"' data.json
```

### Generate JSON

```bash
# Using jq
jq -n \
    --arg name "Alice" \
    --arg age "30" \
    '{name: $name, age: $age}'

# Output: {"name":"Alice","age":"30"}
```

## Parallel Execution

### Background Jobs

```bash
#!/usr/bin/env bash

# Start background jobs
command1 &
pid1=$!

command2 &
pid2=$!

# Wait for all jobs
wait "$pid1" "$pid2"

echo "All jobs completed"
```

### Parallel with xargs

```bash
# Process files in parallel (4 at a time)
find . -name "*.txt" | xargs -P 4 -I {} sh -c 'process_file {}'
```

## Logging

### Simple Logging

```bash
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a app.log
}

log "Application started"
log "Processing data"
```

### Logging Levels

```bash
LOG_LEVEL="${LOG_LEVEL:-INFO}"

log_debug() { [[ "$LOG_LEVEL" == "DEBUG" ]] && echo "[DEBUG] $*" >&2; }
log_info() { echo "[INFO] $*"; }
log_warn() { echo "[WARN] $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }

log_debug "Detailed information"
log_info "General information"
log_warn "Warning message"
log_error "Error occurred"
```

## Process Management

### Check if Process is Running

```bash
if pgrep -x "process_name" > /dev/null; then
    echo "Process is running"
fi
```

### Kill Process by Name

```bash
pkill -9 "process_name"
```

### Wait for Process

```bash
while pgrep -x "process_name" > /dev/null; do
    echo "Waiting for process to finish..." >&2
    sleep 2
done
```

## Network Operations

### Check if Host is Reachable

```bash
if ping -c 1 -W 1 example.com > /dev/null 2>&1; then
    echo "Host is reachable"
fi
```

### Check if Port is Open

```bash
if timeout 1 bash -c "cat < /dev/null > /dev/tcp/example.com/80"; then
    echo "Port 80 is open"
fi
```

### Download File

```bash
# With curl
curl -fsSL https://example.com/file.txt -o output.txt

# With wget
wget -q https://example.com/file.txt -O output.txt
```

## Summary

These patterns cover the most common Bash scripting needs:

- **Script templates**: Starting points for new scripts
- **File operations**: Reading, writing, processing files
- **String operations**: Manipulation and validation
- **Looping**: Various loop patterns
- **Configuration**: Parsing config files
- **JSON**: Processing JSON data
- **Logging**: Structured logging
- **Process management**: Managing processes
- **Network**: Basic network operations

Copy and adapt these patterns for your specific use cases.
