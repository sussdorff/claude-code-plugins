# Variable Scoping with typeset in ZSH

Based on Christopher Allen's Opinionated Best Practices.

## Overview

In ZSH, `typeset` provides powerful control over variable scoping, types, and attributes. It's more versatile than simple `local` declarations and is the recommended ZSH-native approach for variable management.

## Why typeset Over local

While `local` works in ZSH (borrowed from bash), `typeset` offers:

- **Type enforcement** (integers, arrays, associative arrays)
- **Read-only variables** (constants)
- **Explicit global/local control**
- **Attribute assignment** (uppercase, lowercase, etc.)
- **Better clarity** about variable intent

## typeset Basics

### Script-Scoped Variables

Explicitly define variables in the current script/function context:

```zsh
# ❌ BAD - Vague scope
my_Function() {
    ScriptVar="value"  # Is this local? Global? Unclear!
    echo "Script variable: $ScriptVar"
}

# ✅ GOOD - Explicit scope
my_Function() {
    typeset ScriptScopedVar="value"  # Clear: scoped to this context
    echo "Script scoped variable: $ScriptScopedVar"
}
```

### Global Variables: typeset -g

Make variables explicitly global:

```zsh
typeset -g GLOBAL_VAR="global_value"
echo "Global variable: $GLOBAL_VAR"

# Accessible anywhere in script and child functions
my_Function() {
    echo "$GLOBAL_VAR"  # Works
}
```

**Best Practice:** Enable `warn_create_global` to catch accidental globals:

```zsh
setopt warn_create_global

my_Function() {
    AccidentalGlobal="oops"  # ZSH warns: creating global variable
}
```

### Local Variables: typeset (no flags) or local

Variables local to a function:

```zsh
my_Function() {
    typeset localVar="value"  # ZSH way
    # OR
    local localVar="value"    # Bash-compatible way

    echo "Local variable: $localVar"
}

# localVar not accessible here
echo "$localVar"  # Empty
```

**Note:** In ZSH, `typeset` without flags creates a local variable within a function (dynamic scoping).

## Dynamic Scoping in ZSH

ZSH uses **dynamic scoping**: variables are visible within the function and any functions it calls.

```zsh
parent_Function() {
    typeset parentVar="from parent"

    child_Function() {
        # Can access parentVar (dynamic scoping)
        echo "$parentVar"  # Prints: "from parent"

        # But should declare own locals
        typeset childVar="from child"
    }

    child_Function
    echo "$childVar"  # Empty - childVar is local to child
}
```

## Type-Specific Variables

### Read-Only Variables: typeset -r

Create constants that cannot be modified:

```zsh
typeset -r ReadOnlyVar="constant"
echo "$ReadOnlyVar"  # constant

# Attempt to modify
ReadOnlyVar="new_value"  # ERROR: read-only variable: ReadOnlyVar
```

**Use cases:**
- Configuration constants
- API endpoints
- Version numbers
- Paths that shouldn't change

### Integer Variables: typeset -i

Declare integer-only variables:

```zsh
typeset -i IntCounter=42
echo "$IntCounter"  # 42

# Arithmetic without $(( ))
IntCounter+=10
echo "$IntCounter"  # 52

# Non-integer assignment converts to 0
IntCounter="text"
echo "$IntCounter"  # 0 (no error, silent conversion)
```

**Benefits:**
- Faster arithmetic
- Type safety
- Clearer intent

#### Integer Booleans (Idiomatic ZSH)

For boolean flags, use **integers with `(( ))` arithmetic tests** instead of string comparisons:

```zsh
# ❌ AVOID - String boolean (less idiomatic)
typeset found=false
if [[ "$found" == "true" ]]; then
    echo "Found it"
fi
found=true

# ✅ PREFER - Integer boolean (more idiomatic)
typeset -i found=0
if (( found )); then
    echo "Found it"
fi
found=1

# ✅ GOOD - Negation with (( ! ))
typeset -i has_errors=0
if (( ! has_errors )); then
    echo "No errors"
fi
```

**Why prefer integers:**
- **Idiomatic:** ZSH excels at arithmetic, `(( ))` is natural
- **Concise:** `(( flag ))` vs `[[ "$flag" == "true" ]]`
- **Type-safe:** Can't accidentally set to "tru" or "FALSE"
- **Arithmetic-friendly:** Easy to count, increment, use in expressions

**Convention:**
- `0` = false/no/off
- `1` (or any non-zero) = true/yes/on

**Example in functions:**
```zsh
process_data() {
    typeset -i had_stash=0

    if stash_changes; then
        had_stash=1
    fi

    # Do work...

    if (( had_stash )); then
        restore_changes
    fi
}
```

### Array Variables: typeset -a

Declare indexed arrays:

```zsh
typeset -a ArrayVar=("element1" "element2" "element3")
echo "${ArrayVar[@]}"  # element1 element2 element3

# Access by index (1-based in ZSH!)
echo "${ArrayVar[1]}"  # element1
echo "${ArrayVar[2]}"  # element2

# Out-of-bounds returns empty (no error)
echo "${ArrayVar[10]}"  # (empty)

# Array length
echo "${#ArrayVar[@]}"  # 3
```

#### Explicit Array Declaration (Best Practice)

For clarity, separate type declaration from initialization:

```zsh
# ✅ GOOD - Explicit type declaration (clear intent)
typeset -a branches  # Declare as array type
branches=()          # Initialize empty

# Then populate
while IFS= read -r line; do
    branches+=("$line")
done < <(command)

# ❌ WORKS - Combined declaration (less explicit)
typeset -a branches=()  # Both declare and init in one line
```

**Benefits of explicit declaration:**
- **Clarity:** Separates "what type" from "what value"
- **Documentation:** Makes array type immediately visible
- **Pattern:** Consistent with other typed declarations

**When to use:**
- Arrays that will be populated in loops
- Complex initialization logic
- When type clarity is important

### Associative Arrays: typeset -A

Declare key-value dictionaries:

```zsh
typeset -A AssocArray

AssocArray[key1]="value1"
AssocArray[key2]="value2"
AssocArray[database_host]="localhost"
AssocArray[database_port]="5432"

echo "${AssocArray[key1]}"  # value1
echo "${AssocArray[database_host]}"  # localhost

# Non-existent key returns empty (no error)
echo "${AssocArray[nonExistent]}"  # (empty)

# Iterate over keys
for key in "${(@k)AssocArray}"; do
    echo "$key: ${AssocArray[$key]}"
done
```

## Combining typeset Options

Combine flags for powerful declarations:

### Read-Only Global Constant

```zsh
typeset -gr GLOBAL_READ_ONLY_CONSTANT="constant_value"

# Global and cannot be modified
echo "$GLOBAL_READ_ONLY_CONSTANT"  # constant_value

# This fails:
GLOBAL_READ_ONLY_CONSTANT="new"  # ERROR: read-only variable
```

### Local Integer

```zsh
my_Function() {
    typeset -i localInt=100

    # Arithmetic
    localInt+=50
    echo "Local integer: $localInt"  # 150
}

# Not accessible outside
echo "$localInt"  # Empty
```

### Read-Only Array

```zsh
typeset -ra FIXED_ARRAY=("one" "two" "three")

# Cannot modify
FIXED_ARRAY[1]="modified"  # ERROR: read-only variable
```

## Practical Patterns

### Pattern 1: Function Parameters

Parse function parameters into local variables:

```zsh
process_Users() {
    typeset -a Users_Array=("$@")  # All parameters as array
    typeset -i idx=1

    while (( idx <= $#Users_Array )); do
        typeset Name="${Users_Array[idx]}"
        typeset Age="${Users_Array[idx+1]}"
        typeset Email="${Users_Array[idx+2]}"

        echo "Processing user:"
        echo "  Name: $Name"
        echo "  Age: $Age"
        echo "  Email: $Email"

        (( idx += 3 ))  # Next user (3 fields per user)
    done
}

# Usage
process_Users "Alice" 30 "alice@example.com" "Bob" 25 "bob@example.com"
```

### Pattern 2: Configuration Parameters

Use associative arrays for configuration:

```zsh
process_Config() {
    typeset -A Config_Associative_Array=("$@")
    local key

    echo "Processing configuration settings:"
    for key in "${(@k)Config_Associative_Array}"; do
        echo "  $key: ${Config_Associative_Array[$key]}"
    done

    # Access specific config
    local dbHost="${Config_Associative_Array[database_host]}"
    local dbPort="${Config_Associative_Array[database_port]}"

    echo "Connecting to $dbHost:$dbPort"
}

# Usage
process_Config \
    "database_host" "localhost" \
    "database_port" "5432" \
    "username" "admin" \
    "password" "secret"
```

### Pattern 3: Typed Function Locals

```zsh
calculate_Stats() {
    typeset -a numbers=("$@")
    typeset -i total=0
    typeset -i count=${#numbers[@]}
    local number

    # Sum
    for number in "${numbers[@]}"; do
        (( total += number ))
    done

    # Average
    typeset -i average=$((total / count))

    echo "Total: $total"
    echo "Count: $count"
    echo "Average: $average"
}

calculate_Stats 10 20 30 40 50
```

## Avoiding Global Variable Overuse

### Why Global Variables Are Problematic

1. **Unintended side effects** - Changes anywhere affect everywhere
2. **Hard to debug** - Hard to track where values change
3. **Name collisions** - Risk of overwriting
4. **Tight coupling** - Functions become interdependent
5. **Testing difficulty** - Global state makes unit testing hard

### Strategies to Avoid Globals

#### 1. Use Local Variables

```zsh
# ❌ BAD - Global
RESULT=""

calculate() {
    RESULT=$((5 * 10))  # Modifies global
}

# ✅ GOOD - Local with return
calculate() {
    typeset -i result=$((5 * 10))
    echo "$result"  # Return via stdout
}

RESULT=$(calculate)  # Capture result
```

#### 2. Dynamic Scoping with typeset

```zsh
# Child functions see parent's locals
parent_Function() {
    typeset SharedData="available to children"

    child_Function() {
        # Can access SharedData (dynamic scoping)
        echo "$SharedData"

        # But declare own locals
        typeset childLocal="not visible to parent"
    }

    child_Function
}
```

#### 3. Unique Naming for True Globals

When globals are unavoidable:

```zsh
# ✅ GOOD - Very specific names
typeset -g GIT_UTILITY_SCRIPT_DIR="/path/to/git/util"
typeset -g _ZUTIL_DEBUG=false
typeset -g _ZUTIL_TOP_SCRIPT_DIR="/path/to/top"

# ❌ BAD - Generic names
typeset -g DEBUG=false      # Too generic!
typeset -g DIR="/path"      # Too generic!
```

#### 4. Enable warn_create_global

```zsh
#!/usr/bin/env zsh
setopt warn_create_global

my_Function() {
    AccidentalGlobal="oops"  # ZSH warns!
}
```

#### 5. Encapsulate in Functions

```zsh
# ❌ BAD - Lots of global state
DATABASE_HOST="localhost"
DATABASE_PORT=5432
DATABASE_USER="admin"

connect() {
    # Uses globals
    echo "Connecting to $DATABASE_HOST:$DATABASE_PORT as $DATABASE_USER"
}

# ✅ GOOD - Pass parameters
connect_Database() {
    typeset host="$1"
    typeset -i port="$2"
    typeset user="$3"

    echo "Connecting to $host:$port as $user"
}

connect_Database "localhost" 5432 "admin"
```

#### 6. Use Environment Variables Sparingly

Only for truly cross-script needs:

```zsh
# Only if needed across multiple independent scripts
export JIRA_API_BASE="https://api.atlassian.net"
export JIRA_AUTH_TOKEN="secret"

# Document in script header:
# Requires: JIRA_API_BASE, JIRA_AUTH_TOKEN environment variables
```

#### 7. Read-Only for Necessary Globals

```zsh
# If global is needed, make it read-only
typeset -gr API_VERSION="v3"
typeset -gr MAX_RETRIES=5
typeset -gr TIMEOUT_SECONDS=30
```

#### 8. Document Global Usage

```zsh
#
# Global Variables:
#   JIRA_INSTANCE_NAME - Set by configure_Jira_Api()
#   JIRA_API_BASE - Set by configure_Jira_Api()
#   JIRA_AUTH_HEADER - Set by configure_Jira_Api()
#

configure_Jira_Api() {
    typeset -g JIRA_INSTANCE_NAME="$1"
    typeset -g JIRA_API_BASE="https://api.atlassian.net"
    typeset -g JIRA_AUTH_HEADER="Authorization: Bearer ..."
}
```

## Best Practices Summary

### ✅ DO

```zsh
# Prefer typeset for ZSH scripts
typeset localVar="value"

# Use appropriate types
typeset -i count=0
typeset -a items=()
typeset -A config=()

# Make constants read-only
typeset -r CONSTANT="value"

# Be explicit about globals
typeset -g GLOBAL_VAR="value"

# Use descriptive names
typeset ticketData
typeset outputDirectory
```

### ❌ DON'T

```zsh
# Avoid vague scoping
SomeVar="value"  # Local? Global? Unclear!

# Avoid generic global names
typeset -g DATA="value"
typeset -g RESULT="value"

# Avoid silent type coercion surprises
typeset -i num="text"  # Becomes 0 silently
```

## Quick Reference

| Declaration | Effect |
|-------------|--------|
| `typeset var="value"` | Script/function scoped |
| `typeset -g var="value"` | Global |
| `typeset -r var="value"` | Read-only (constant) |
| `typeset -i var=42` | Integer |
| `typeset -a var=()` | Array |
| `typeset -A var=()` | Associative array |
| `typeset -gr var="value"` | Global read-only constant |
| `local var="value"` | Local (bash-compatible) |

## Summary

- **Prefer `typeset`** for ZSH scripts (more powerful than `local`)
- **Use type flags** (`-i`, `-a`, `-A`) for clarity and safety
- **Make constants read-only** (`-r`) to prevent modification
- **Be explicit about scope** (`-g` for global, or no flags for local)
- **Avoid global variables** - use function parameters and return values
- **Enable `warn_create_global`** to catch accidental globals
- **Document global usage** when truly necessary
