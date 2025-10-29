# Error Handling in Bash

Robust patterns for detecting, handling, and reporting errors.

## Core Principles

1. **Fail fast**: Use `set -e` to exit on errors
2. **Fail loud**: Report errors to stderr
3. **Clean up**: Use trap to clean up resources
4. **Be specific**: Provide context in error messages

## Basic Error Detection

### Exit Codes

```bash
# Check exit code explicitly
command_that_might_fail
if [[ $? -ne 0 ]]; then
    echo "Error: Command failed" >&2
    exit 1
fi

# Or use directly in if
if ! command_that_might_fail; then
    echo "Error: Command failed" >&2
    exit 1
fi

# Or with || operator
command_that_might_fail || {
    echo "Error: Command failed" >&2
    exit 1
}
```

### Capture and Check

```bash
#!/usr/bin/env bash
set -e

# Capture output and check
output=$(command_that_might_fail) || {
    echo "Error: Command failed" >&2
    exit 1
}

echo "Success: $output"
```

## Trap for Cleanup

### Basic Trap

```bash
#!/usr/bin/env bash

cleanup() {
    echo "Cleaning up..." >&2
    # Remove temporary files
    rm -f /tmp/myapp.*
}

# Register cleanup function
trap cleanup EXIT

# Script logic here
```

### Trap on Error

```bash
#!/usr/bin/env bash
set -e

error_handler() {
    local exit_code=$?
    echo "Error: Script failed with exit code $exit_code at line $1" >&2
    # Additional cleanup
}

trap 'error_handler $LINENO' ERR

# Script logic here
```

### Trap Multiple Signals

```bash
#!/usr/bin/env bash

cleanup() {
    echo "Interrupted, cleaning up..." >&2
    # Cleanup code
    exit 1
}

trap cleanup EXIT INT TERM

# Script logic here
```

## Error Reporting

### Write to Stderr

```bash
# Always write errors to stderr (>&2)

echo "Error: File not found" >&2
printf "Error: %s\n" "$message" >&2

# Not stdout!
# echo "Error: File not found"  # WRONG
```

### Contextual Error Messages

```bash
#!/usr/bin/env bash

process_file() {
    local file="$1"

    if [[ ! -f "$file" ]]; then
        echo "Error: File does not exist: $file" >&2
        return 1
    fi

    if [[ ! -r "$file" ]]; then
        echo "Error: Cannot read file: $file" >&2
        return 1
    fi

    # Process file
}
```

### Error with Stack Trace

```bash
#!/usr/bin/env bash

error_with_trace() {
    local message="$1"

    echo "Error: $message" >&2
    echo "Stack trace:" >&2

    local frame=0
    while caller $frame >&2; do
        ((frame++))
    done

    exit 1
}

# Usage
my_function() {
    error_with_trace "Something went wrong"
}
```

## Handling Expected Failures

### Try-Catch Pattern

```bash
#!/usr/bin/env bash
set -e

# Temporarily disable exit on error
set +e
output=$(command_that_might_fail 2>&1)
exit_code=$?
set -e

if [[ $exit_code -ne 0 ]]; then
    echo "Warning: Command failed: $output" >&2
    # Handle failure
else
    echo "Success: $output"
fi
```

### Ignoring Specific Failures

```bash
#!/usr/bin/env bash
set -e

# Command that we expect might fail
command_that_might_fail || true

# Or with explicit check
if command_that_might_fail; then
    echo "Command succeeded"
else
    echo "Command failed (expected)" >&2
fi
```

## Advanced Patterns

### Retry Logic

```bash
retry() {
    local max_attempts="$1"
    shift
    local command=("$@")
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if "${command[@]}"; then
            return 0
        fi

        echo "Attempt $attempt failed, retrying..." >&2
        ((attempt++))
        sleep 2
    done

    echo "Error: Command failed after $max_attempts attempts" >&2
    return 1
}

# Usage
retry 3 curl -f https://api.example.com/data
```

### Timeout Pattern

```bash
#!/usr/bin/env bash

run_with_timeout() {
    local timeout="$1"
    shift
    local command=("$@")

    timeout "$timeout" "${command[@]}" || {
        local exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            echo "Error: Command timed out after ${timeout}s" >&2
        else
            echo "Error: Command failed with exit code $exit_code" >&2
        fi
        return $exit_code
    }
}

# Usage
run_with_timeout 10s curl https://slow-api.example.com
```

### Rollback on Failure

```bash
#!/usr/bin/env bash
set -e

deploy() {
    local backup_dir
    backup_dir="$(mktemp -d)"

    # Backup current version
    cp -r /var/www/app "$backup_dir/"

    # Register rollback
    trap "echo 'Rolling back...'; cp -r $backup_dir/* /var/www/app/; rm -rf $backup_dir" ERR

    # Deploy steps (any failure triggers rollback)
    git pull
    npm install
    npm run build
    systemctl restart app

    # Success - remove backup
    rm -rf "$backup_dir"
    trap - ERR  # Remove error trap
}
```

## Testing Exit Codes

### Function Return Values

```bash
validate_input() {
    local input="$1"

    if [[ -z "$input" ]]; then
        return 1  # Failure
    fi

    if [[ ! "$input" =~ ^[0-9]+$ ]]; then
        return 2  # Invalid format
    fi

    return 0  # Success
}

# Usage
if validate_input "$user_input"; then
    echo "Valid input"
elif [[ $? -eq 2 ]]; then
    echo "Error: Input must be numeric" >&2
else
    echo "Error: Input is required" >&2
fi
```

## Common Pitfalls

### Pitfall 1: Testing $? After Other Commands

```bash
# ❌ WRONG
command_that_fails
if [[ -n "$var" ]]; then  # This sets $? !
    if [[ $? -eq 0 ]]; then  # Wrong $?
        echo "Success"
    fi
fi

# ✅ CORRECT
command_that_fails
status=$?  # Capture immediately
if [[ -n "$var" ]]; then
    if [[ $status -eq 0 ]]; then
        echo "Success"
    fi
fi
```

### Pitfall 2: Not Cleaning Up on Error

```bash
# ❌ WRONG
temp_file=$(mktemp)
command_that_might_fail
rm "$temp_file"  # Doesn't run if command fails

# ✅ CORRECT
temp_file=$(mktemp)
trap 'rm -f "$temp_file"' EXIT
command_that_might_fail
```

### Pitfall 3: Masking Errors in Pipes

```bash
# ❌ WRONG (without pipefail)
#!/usr/bin/env bash
set -e

curl https://api.example.com | jq '.data'
# If curl fails, jq returns 0, script continues

# ✅ CORRECT
#!/usr/bin/env bash
set -eo pipefail

curl https://api.example.com | jq '.data'
# If curl fails, entire pipeline fails
```

## Error Handling Checklist

- [ ] Script starts with `set -euo pipefail`
- [ ] Errors written to stderr (`>&2`)
- [ ] Cleanup registered with `trap cleanup EXIT`
- [ ] Exit codes checked explicitly when needed
- [ ] Error messages include context
- [ ] Temporary files cleaned up
- [ ] Expected failures handled with `|| true` or `set +e`
- [ ] Critical sections have rollback logic

## Summary

**Essential pattern**:
```bash
#!/usr/bin/env bash
set -euo pipefail

cleanup() {
    # Remove temporary files
    rm -f /tmp/myapp.*
}

trap cleanup EXIT
trap 'echo "Error at line $LINENO" >&2' ERR

# Script logic here
```

**Key practices**:
1. Use `set -euo pipefail`
2. Write errors to stderr
3. Register cleanup with trap
4. Provide context in error messages
5. Handle expected failures explicitly
