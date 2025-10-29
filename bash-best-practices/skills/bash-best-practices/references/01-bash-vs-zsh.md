# Bash vs ZSH - Critical Differences

Essential guide for migrating from ZSH to Bash or writing portable scripts.

## Why This Matters

**Context**: solutio-claude-skills originally used ZSH but switched to Bash for cross-platform compatibility (Linux, WSL, macOS).

**Key insight**: ZSH and Bash look similar but have subtle, breaking differences. Writing "looks like it works" code leads to production bugs.

## Quick Reference Table

| Feature | Bash | ZSH | Portable |
|---------|------|-----|----------|
| Array indexing | 0-based | 1-based | Use 0-based |
| Word splitting | By default | Disabled by default | Always quote |
| Initialization | `set -euo pipefail` | `emulate -LR zsh` | Use Bash form |
| Variable scoping | `local`/`declare` | `typeset` | Use `local` |
| Path manipulation | `dirname`/`basename` | `${var:A:h}` | Use commands |
| File extension | `.sh` | `.zsh` | Use `.sh` |

## Critical Difference #1: Array Indexing

### The Problem

```bash
# This code produces different results in Bash vs ZSH!
arr=("first" "second" "third")
echo "${arr[0]}"  # Bash: "first"  |  ZSH: ""
echo "${arr[1]}"  # Bash: "second" |  ZSH: "first"
```

### The Solution

**Always use 0-based indexing** (Bash standard):

```bash
#!/usr/bin/env bash

# Correct for Bash
arr=("first" "second" "third")
echo "${arr[0]}"  # "first"
echo "${arr[1]}"  # "second"
echo "${arr[2]}"  # "third"

# Array length (same in both)
echo "${#arr[@]}"  # 3

# Iterate correctly (same in both)
for item in "${arr[@]}"; do
    echo "$item"
done
```

### Migration Pattern

```bash
# ZSH code (1-based)
arr=("a" "b" "c")
first="${arr[1]}"  # Gets "a"

# Convert to Bash (0-based)
arr=("a" "b" "c")
first="${arr[0]}"  # Gets "a"

# Rule: Subtract 1 from all array indices when migrating
```

## Critical Difference #2: Word Splitting

### The Problem

```bash
# ZSH: NO word splitting by default
var="foo bar baz"
for word in $var; do echo "$word"; done
# Output in ZSH: foo bar baz (one iteration)
# Output in Bash: foo / bar / baz (three iterations)
```

### The Solution

**Always quote variables in Bash**:

```bash
#!/usr/bin/env bash

# Safe: Always quote
file="my document.txt"
if [[ -f "$file" ]]; then
    cat "$file"
fi

# Intentional word splitting (rare)
flags="-v -x -a"
# DON'T: command $flags
# DO: Use array
flags=(-v -x -a)
command "${flags[@]}"
```

### Migration Pattern

```bash
# ZSH: Unquoted often works
dir=/path/with spaces
cd $dir  # Works in ZSH (no splitting)

# Bash: Must quote
dir="/path/with spaces"
cd "$dir"  # Required in Bash

# Rule: Add quotes around ALL variable expansions
```

## Critical Difference #3: Strict Mode / Initialization

### The Problem

```bash
# ZSH uses emulate
#!/usr/bin/env zsh
emulate -LR zsh
setopt ERR_EXIT NO_UNSET

# Bash uses set
#!/usr/bin/env bash
set -euo pipefail
```

### The Solution

**Use Bash strict mode pattern**:

```bash
#!/usr/bin/env bash
set -euo pipefail

# What each flag does:
# -e: Exit on error
# -u: Error on undefined variables
# -o pipefail: Fail if any command in pipeline fails

# Optional additions:
set -E  # Inherit ERR trap in functions
```

### Migration Pattern

```bash
# ZSH script header
#!/usr/bin/env zsh
emulate -LR zsh
setopt ERR_EXIT ERR_RETURN NO_UNSET PIPE_FAIL

# Convert to Bash
#!/usr/bin/env bash
set -euo pipefail

# Note: ERR_RETURN doesn't have exact Bash equivalent
# Bash functions inherit -e by default (mostly)
```

## Critical Difference #4: Variable Scoping

### The Problem

```bash
# ZSH uses typeset
my_function() {
    typeset local_var="value"
    typeset -i counter=0
    typeset -r CONST="constant"
}

# Bash uses local/declare
my_function() {
    local local_var="value"
    local -i counter=0
    declare -r CONST="constant"
}
```

### The Solution

**Use `local` for function variables, `declare` for special types**:

```bash
#!/usr/bin/env bash

my_function() {
    # Regular local variables
    local var1="value"
    local var2="another"

    # Integer variables
    local -i counter=0

    # Arrays
    local -a array=()

    # Read-only (constants)
    declare -r CONST="value"

    # Exported (environment variables)
    declare -x ENV_VAR="value"
}
```

### Migration Pattern

```bash
# ZSH code
my_func() {
    typeset result="value"
    typeset -i count=10
    typeset -r MAX=100
}

# Convert to Bash
my_func() {
    local result="value"
    local -i count=10
    declare -r MAX=100
}

# Rule: typeset → local (for regular vars)
#       typeset -r → declare -r (for constants)
```

## Critical Difference #5: Path Manipulation

### The Problem

```bash
# ZSH: Special parameter expansions
script_dir="${${(%):-%x}:A:h}"
script_name="${${(%):-%x}:t}"

# Bash: These don't exist!
```

### The Solution

**Use standard POSIX commands**:

```bash
#!/usr/bin/env bash

# Script directory (robust, handles symlinks)
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Script name
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

# Alternative: Simpler but doesn't resolve symlinks
readonly SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

# For sourced scripts vs executed scripts
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Script is being executed"
else
    echo "Script is being sourced"
fi
```

### Migration Pattern

```bash
# ZSH code
script_dir="${${(%):-%x}:A:h}"
script_name="${${(%):-%x}:t}"

# Convert to Bash
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
script_name="$(basename "${BASH_SOURCE[0]}")"

# For relative paths
parent_dir="$(dirname "$PWD")"  # One level up
```

## Critical Difference #6: Function Definition Syntax

### The Problem

```bash
# ZSH allows: function name { ... }
function my_func {
    echo "No parentheses"
}

# Bash requires either:
# - function name() { ... }
# - name() { ... }
```

### The Solution

**Use standard POSIX syntax**:

```bash
#!/usr/bin/env bash

# Recommended: name() { ... }
my_function() {
    local param="$1"
    echo "$param"
}

# Also works: function name() { ... }
function other_function() {
    echo "Works but redundant"
}

# Opening brace can be on same line or next line
another_function()
{
    echo "K&R style"
}
```

## Critical Difference #7: Associative Arrays

### The Problem

```bash
# ZSH: Available by default
typeset -A config
config[key]="value"

# Bash: Requires version 4.0+, different declaration
declare -A config
config[key]="value"
```

### The Solution

**Check Bash version, use declare -A**:

```bash
#!/usr/bin/env bash

# Verify Bash 4.0+
if (( BASH_VERSINFO[0] < 4 )); then
    echo "Error: Bash 4.0+ required for associative arrays" >&2
    exit 1
fi

# Declare associative array
declare -A config

# Assign values
config[host]="localhost"
config[port]="5432"
config[database]="mydb"

# Access values
echo "${config[host]}"

# Iterate
for key in "${!config[@]}"; do
    echo "$key: ${config[$key]}"
done
```

## Critical Difference #8: Glob Patterns

### The Problem

```bash
# ZSH: Extended glob by default
files=(*.txt~backup.txt)  # All txt except backup.txt

# Bash: Requires shopt
shopt -s extglob
files=(!(backup).txt)
```

### The Solution

**Enable extglob explicitly in Bash**:

```bash
#!/usr/bin/env bash

# Enable extended globbing
shopt -s extglob

# Now you can use:
# ?(pattern) - zero or one occurrence
# *(pattern) - zero or more occurrences
# +(pattern) - one or more occurrences
# @(pattern) - exactly one occurrence
# !(pattern) - anything except pattern

# Example: All .txt files except backup.txt
files=(!(backup).txt)

# Example: All .log or .txt files
files=(@(*.log|*.txt))
```

## Common Migration Pitfalls

### Pitfall 1: Assuming ZSH Idioms Work

```bash
# ❌ ZSH idiom that fails in Bash
arr=(a b c)
echo ${arr[1]}  # Bash: "b", ZSH: "a"

# ✅ Bash-compatible
arr=(a b c)
echo "${arr[0]}"  # Always "a"
```

### Pitfall 2: Unquoted Variables

```bash
# ❌ Works in ZSH, breaks in Bash
file="my file.txt"
cat $file  # Bash error: "my" not found

# ✅ Works in both
cat "$file"
```

### Pitfall 3: Using typeset in Bash Scripts

```bash
# ❌ Works but non-standard
function my_func() {
    typeset var="value"  # Works but shouldn't
}

# ✅ Use local in Bash
function my_func() {
    local var="value"
}
```

### Pitfall 4: Relying on setopt

```bash
# ❌ ZSH-specific
setopt NULL_GLOB
files=(*.txt)

# ✅ Bash equivalent
shopt -s nullglob
files=(*.txt)
```

## Naming Conventions

### File Extensions

**Use `.sh` for Bash scripts** (not `.bash`):

```bash
# Recommended
backup-database.sh
sync-config.sh

# Not recommended (but works)
backup-database.bash
```

**Rationale**: `.sh` is universal shell script extension, more recognizable.

### Variable Names

**Same in both shells** (POSIX standard):

```bash
# Constants: UPPER_SNAKE_CASE
readonly MAX_RETRIES=3
export API_URL="https://api.example.com"

# Variables: lower_snake_case
local user_name="alice"
local output_file="/tmp/output.txt"

# Private/internal: _leading_underscore (optional)
local _temp_state="initialized"
```

## Testing for Compatibility

### Check Script Works in Bash

```bash
# Check syntax without executing
bash -n script.sh

# Run with strict mode
bash -euo pipefail script.sh

# Run with ShellCheck
shellcheck script.sh
```

### Test on Multiple Platforms

```bash
# macOS (BSD utilities)
bash script.sh

# Linux (GNU utilities)
bash script.sh

# WSL (Windows Subsystem for Linux)
bash script.sh
```

## Migration Checklist

When converting ZSH scripts to Bash:

- [ ] Change shebang: `#!/usr/bin/env bash`
- [ ] Replace `emulate -LR zsh` with `set -euo pipefail`
- [ ] Replace `typeset` with `local` (or `declare -r` for constants)
- [ ] Change all array indices (subtract 1, use 0-based)
- [ ] Quote ALL variable expansions: `$var` → `"$var"`
- [ ] Replace ZSH path magic with dirname/basename commands
- [ ] Replace `setopt` with `shopt` or `set` equivalents
- [ ] Test with `bash -n` and ShellCheck
- [ ] Change file extension: `.zsh` → `.sh`
- [ ] Remove ZSH-specific features (no direct Bash equivalent)
- [ ] Test on Linux, macOS, and WSL

## Quick Port Example

### Before (ZSH)

```zsh
#!/usr/bin/env zsh
emulate -LR zsh
setopt ERR_EXIT NO_UNSET

typeset -r SCRIPT_DIR="${${(%):-%x}:A:h}"
typeset config_file="$1"

typeset -a files
files=(${SCRIPT_DIR}/*.conf)

for file in $files; do
    typeset name="${file:t:r}"
    echo "Processing: $name"
done
```

### After (Bash)

```bash
#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
local config_file="$1"

local -a files
files=("${SCRIPT_DIR}"/*.conf)

for file in "${files[@]}"; do
    local name
    name="$(basename "$file" .conf)"
    echo "Processing: $name"
done
```

## Summary

**Key takeaways**:

1. **Array indexing**: Bash is 0-based, ZSH is 1-based
2. **Word splitting**: Bash splits by default, ZSH doesn't
3. **Always quote**: `"$var"` not `$var` in Bash
4. **Use `local`**: Not `typeset` in Bash
5. **Path commands**: Use `dirname`/`basename`, not ZSH magic
6. **Test thoroughly**: ZSH/Bash differences cause subtle bugs

**When in doubt**: Write POSIX-compatible code that works in both shells.
