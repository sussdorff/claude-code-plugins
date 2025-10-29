# Strict Mode and Shell Options in ZSH

## Strict Error Handling with `set -euo pipefail`

### What Each Flag Does

```zsh
#!/bin/zsh

set -e          # Exit on error
set -u          # Error on undefined variables
set -o pipefail # Pipe fails if any command fails

# Or combined:
set -euo pipefail
```

### Flag Explanations

- **`-e`**: Exit immediately if a command exits with non-zero status
- **`-u`**: Treat unset variables as errors
- **`-o pipefail`**: Return value of pipeline is status of last command to exit with non-zero

## Best Practice: Reset Options with `emulate`

**Always reset options at the beginning of scripts** to ensure consistent behavior.

### Basic Pattern

```zsh
#!/bin/zsh

# Reset to known state
emulate -LR zsh

# Then set required options
setopt ERR_EXIT      # Same as set -e
setopt NO_UNSET      # Same as set -u
setopt PIPE_FAIL     # Same as set -o pipefail
```

### The `emulate` Command

```zsh
# Full syntax
emulate -LR zsh

# Flags:
#   -L: Enable LOCAL_OPTIONS (options are scoped to function)
#   -R: Reset all options to defaults
#   zsh: Emulate zsh mode
```

### Why `emulate` is Important

Script behavior can change based on user's shell configuration:

```zsh
# User might have in ~/.zshrc
setopt EXTENDED_GLOB
setopt KSH_ARRAYS
# ... etc

# Without emulate, your script inherits these settings!
```

## LOCAL_OPTIONS Pattern

**For functions that need specific options**, use LOCAL_OPTIONS to scope changes.

### Pattern: Function-Scoped Options

```zsh
#!/bin/zsh

compat_function() {
    # Isolate option changes to this function
    emulate -L zsh
    setopt LOCAL_OPTIONS KSH_ARRAYS

    # Inside this function, arrays are 0-indexed
    local arr=("first" "second")
    echo "${arr[0]}"  # "first"
}

# Outside function, normal ZSH behavior
main_arr=("first" "second")
echo "${main_arr[1]}"  # "first"
```

### Benefits of LOCAL_OPTIONS

1. **Isolation**: Changes don't affect caller
2. **Safety**: Options restore automatically on function return
3. **Clarity**: Explicit about which functions use special options

## Common Options for Scripts

### Recommended for Robust Scripts

```zsh
#!/bin/zsh
emulate -LR zsh

# Error handling
setopt ERR_EXIT       # Exit on error
setopt ERR_RETURN     # Return from function on error
setopt PIPE_FAIL      # Pipeline fails if any command fails
setopt NO_UNSET       # Error on undefined variables

# Globbing
setopt EXTENDED_GLOB  # Enable ^, ~, # in patterns
setopt GLOB_DOTS      # Include dotfiles in globs
setopt NULL_GLOB      # Don't error on no matches (expands to nothing)

# Safety
setopt NO_CLOBBER     # Don't overwrite files with > (use >! to override)
setopt WARN_CREATE_GLOBAL  # Warn when creating global variables in functions
```

### Options for Interactive Use (Not Scripts)

```zsh
# DON'T set these in scripts
setopt AUTO_CD        # cd by typing directory name
setopt CORRECT        # Spelling correction
setopt SHARE_HISTORY  # Share history between sessions
```

## Considerations with `set -euo pipefail`

### Can Mask Issues

While strict error handling is valuable, it can hide problems:

```zsh
set -euo pipefail

# Silent exit if command fails
result=$(some_command || echo "default")

# Hard to trace exact failure point in complex scripts
command1 | command2 | command3  # Which failed?
```

### Add Explicit Error Handling

```zsh
#!/bin/zsh
set -euo pipefail

fetch_data() {
    local url="$1"
    local output="$2"

    if ! curl -s "$url" > "$output" 2>&1; then
        echo "ERROR: Failed to fetch $url" >&2
        return 1
    fi

    if [[ ! -s "$output" ]]; then
        echo "ERROR: Empty response from $url" >&2
        return 1
    fi

    return 0
}
```

## Checking Current Options

### Check if Option is Set

```zsh
# Using [[ -o option_name ]]
if [[ -o ERR_EXIT ]]; then
    echo "ERR_EXIT is enabled"
fi

# Check specific option
[[ -o NO_UNSET ]] && echo "Will error on undefined vars"
```

### List All Options

```zsh
# Show all options and their states
setopt

# Show only set options
setopt | grep "^[a-z]"

# Show specific option
setopt | grep EXTENDED_GLOB
```

## Script Template with Best Practices

```zsh
#!/usr/bin/env zsh
#
# Script: my-script.zsh
# Description: Does something useful
# Usage: my-script.zsh <arg>

# Reset to known zsh defaults
emulate -LR zsh

# Enable strict error handling
setopt ERR_EXIT       # Exit on error
setopt ERR_RETURN     # Return on error in function
setopt NO_UNSET       # Error on undefined variables
setopt PIPE_FAIL      # Fail if any command in pipeline fails

# Enable extended globbing
setopt EXTENDED_GLOB
setopt NULL_GLOB      # Don't error on no glob matches

# Script configuration
SCRIPT_DIR="${0:A:h}"  # Absolute path to script directory
SCRIPT_NAME="${0:t}"   # Script basename

# Cleanup on exit
cleanup() {
    # Remove temp files, etc.
    :
}
trap cleanup EXIT INT TERM

# Main script logic
main() {
    if [[ $# -lt 1 ]]; then
        echo "Usage: $SCRIPT_NAME <arg>" >&2
        return 1
    fi

    # ... script logic ...
}

main "$@"
```

## NO_UNSET Gotcha: Arithmetic Expressions

### The Problem

When using `setopt NO_UNSET`, the `(( var++ ))` syntax can fail even when the variable is properly declared:

```zsh
#!/usr/bin/env zsh
emulate -LR zsh
setopt ERR_EXIT NO_UNSET

typeset -i counter=0
(( counter++ ))  # FAILS! Script exits here
echo "Never reached"
```

**Why it fails**: The `(( var++ ))` expression evaluates to 0 when `var` is 0, which combined with `NO_UNSET` and `ERR_EXIT` causes the script to exit.

### The Solution

Use explicit assignment instead of increment operators:

```zsh
#!/usr/bin/env zsh
emulate -LR zsh
setopt ERR_EXIT NO_UNSET

typeset -i counter=0

# ❌ WRONG - Fails with NO_UNSET
(( counter++ ))

# ✅ CORRECT - Works with NO_UNSET
counter=$((counter + 1))
```

### Complete Example

```zsh
#!/usr/bin/env zsh
emulate -LR zsh
setopt ERR_EXIT NO_UNSET PIPE_FAIL

typeset -i total=0
typeset -i errors=0

for file in *.txt; do
    total=$((total + 1))  # Use explicit assignment

    if ! process_file "$file"; then
        errors=$((errors + 1))
    fi
done

echo "Processed $total files with $errors errors"
```

### Why This Matters

This is a **known ZSH quirk** when combining strict error modes. The workaround is simple but not obvious - always use `var=$((var + 1))` instead of `(( var++ ))` in strict mode scripts.

## emulate sh - POSIX Compatibility Mode

### When to Use

For scripts that must run on minimal systems (Recovery, installers):

```zsh
#!/bin/sh
# Or with explicit emulation:

#!/bin/zsh
emulate -LR sh

# Now script behaves like POSIX sh
# - Arrays work differently
# - Many zsh features unavailable
# - Better portability
```

### Caveats

- **Limited features**: Many ZSH features unavailable
- **Different syntax**: Avoid ZSH-specific constructs
- **Consider /bin/sh directly**: May be clearer than emulate

## Option Naming Conventions

### Two Forms

```zsh
# Long form (preferred in scripts for clarity)
setopt ERR_EXIT
setopt NO_UNSET
setopt EXTENDED_GLOB

# Short form (same as above)
set -e
set -u
# (no short form for EXTENDED_GLOB)
```

### Negation

```zsh
# Enable
setopt CLOBBER

# Disable (add NO_ prefix)
setopt NO_CLOBBER

# Or use unsetopt
unsetopt CLOBBER
```

## Common Pitfalls

### Pitfall 1: Global Options from .zshrc

```zsh
#!/bin/zsh
# BAD - inherits user's interactive options
# Some user has: setopt KSH_ARRAYS

arr=("first" "second")
echo "${arr[1]}"  # Might be "second" if they set KSH_ARRAYS!
```

```zsh
#!/bin/zsh
# GOOD - reset to known state
emulate -LR zsh

arr=("first" "second")
echo "${arr[1]}"  # Always "first"
```

### Pitfall 2: Forgetting LOCAL_OPTIONS

```zsh
process_bash_style() {
    setopt KSH_ARRAYS  # BAD - affects whole script!
    # ...
}

# Now rest of script has 0-based arrays!
```

```zsh
process_bash_style() {
    emulate -L zsh
    setopt LOCAL_OPTIONS KSH_ARRAYS  # GOOD - scoped
    # ...
}
# Option restored on return
```

### Pitfall 3: Relying on Interactive Options

```zsh
#!/bin/zsh
# Assumes user has AUTO_CD - BAD!
some-directory  # Might not work in all environments
```

```zsh
#!/bin/zsh
# Explicit - GOOD
cd some-directory
```

## When NOT to Use Strict Mode

Some scenarios where strict mode can be counterproductive:

```zsh
# Interactive wrapper scripts
# - Allow graceful degradation
# - Don't exit terminal on error

# Test/verification scripts
# - Need to check if commands fail
# - Continue testing after failures

# Backward compatibility scripts
# - Must work with older zsh versions
# - Some options not available
```

## Summary

### Core Principles

1. **Always use `emulate -LR zsh`** at script start
2. **Enable error handling**: ERR_EXIT, NO_UNSET, PIPE_FAIL
3. **Use LOCAL_OPTIONS** for function-scoped changes
4. **Never set global options** in scripts (they leak)
5. **Document option assumptions** in comments

### Quick Reference

```zsh
# Script header
#!/usr/bin/env zsh
emulate -LR zsh
setopt ERR_EXIT NO_UNSET PIPE_FAIL

# Function with local options
func() {
    emulate -L zsh
    setopt LOCAL_OPTIONS KSH_ARRAYS
    # ...
}

# Check option
[[ -o ERR_EXIT ]] && echo "Strict mode"

# List all options
setopt
```
