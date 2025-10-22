# Variable Scoping in Bash

Understanding `local`, `declare`, and preventing global variable leakage.

## The Golden Rule

**Every variable in a function should be `local` unless you explicitly want it global.**

```bash
# ❌ BAD - Accidental global
my_function() {
    result="value"  # Global!
}

# ✅ GOOD - Explicit local
my_function() {
    local result="value"  # Local to function
}
```

## The Problem: Global by Default

```bash
#!/usr/bin/env bash

counter=0

increment() {
    counter=$((counter + 1))  # Modifies global!
}

increment
echo "$counter"  # Prints: 1 (global was modified)
```

**Why this is dangerous**:
- Name collisions
- Unexpected side effects
- Hard-to-debug issues
- Not reusable

## The Solution: `local`

```bash
#!/usr/bin/env bash

my_function() {
    local counter=0  # Local to this function
    counter=$((counter + 1))
    echo "$counter"
}

counter=99
my_function  # Prints: 1
echo "$counter"  # Prints: 99 (global unchanged)
```

## `local` vs `declare`

### Use `local` for Regular Variables

```bash
my_function() {
    local var1="value"
    local var2="another"
    local -i number=42  # Integer
    local -a array=()   # Array
}
```

### Use `declare` for Special Cases

```bash
#!/usr/bin/env bash

my_function() {
    # Read-only variable (constant)
    declare -r CONST="immutable"

    # Export to environment
    declare -x EXPORTED_VAR="visible to child processes"

    # Lowercase string
    declare -l lowercase="BECOMES lowercase"

    # Uppercase string
    declare -u uppercase="becomes UPPERCASE"
}
```

### When to Use Each

| Keyword | Use For | Scope |
|---------|---------|-------|
| `local` | Function variables | Local only |
| `declare` | Special attributes | Local in functions, global at top level |
| `readonly` | Constants | Global/local depending on location |
| `export` | Environment variables | Exported to child processes |

## Scoping Rules

### Rule 1: Functions Have Dynamic Scope

```bash
#!/usr/bin/env bash

outer() {
    local var="outer"
    inner
}

inner() {
    echo "$var"  # Can see 'var' from outer!
}

outer  # Prints: outer
```

**Implication**: Inner functions can access outer function's locals.

### Rule 2: Locals Hide Globals

```bash
#!/usr/bin/env bash

var="global"

my_function() {
    local var="local"
    echo "$var"  # Prints: local
}

my_function
echo "$var"  # Prints: global
```

### Rule 3: Assignment in Declaration Doesn't Fail

```bash
#!/usr/bin/env bash
set -e

my_function() {
    # ❌ WRONG - Masks command failure!
    local result=$(failing_command)
    # Declaration succeeds, assignment fails silently

    # ✅ CORRECT - Separate declaration and assignment
    local result
    result=$(failing_command)  # Fails properly with set -e
}
```

**ShellCheck Warning**: SC2155

## Common Patterns

### Pattern 1: Return Value via Echo

```bash
get_user_name() {
    local user_id="$1"
    local name

    # Fetch name somehow
    name="Alice"

    echo "$name"  # Return via stdout
}

# Usage
user_name=$(get_user_name 42)
echo "User: $user_name"
```

### Pattern 2: Return Status via Exit Code

```bash
validate_input() {
    local input="$1"

    if [[ -z "$input" ]]; then
        return 1  # Failure
    fi

    return 0  # Success
}

# Usage
if validate_input "$user_input"; then
    echo "Valid"
else
    echo "Invalid"
fi
```

### Pattern 3: Multiple Return Values via Global

```bash
#!/usr/bin/env bash

# Declare return variables at top level
declare result_name=""
declare result_age=0

get_user_info() {
    local user_id="$1"

    # Modify globals (documented convention)
    result_name="Alice"
    result_age=30
}

# Usage
get_user_info 42
echo "Name: $result_name, Age: $result_age"
```

**Note**: Document this pattern clearly if used.

### Pattern 4: Return via Nameref (Bash 4.3+)

```bash
#!/usr/bin/env bash

get_user_info() {
    local -n output_ref=$1  # Nameref to caller's variable

    output_ref="Alice (age 30)"
}

# Usage
local user_info
get_user_info user_info
echo "$user_info"  # Prints: Alice (age 30)
```

## Type Attributes with `local`

### Integer Variables

```bash
my_function() {
    local -i counter=0

    counter="not a number"  # Becomes 0
    counter="42abc"         # Becomes 42

    counter+=1  # Arithmetic, not concatenation
}
```

### Arrays

```bash
my_function() {
    local -a indexed_array=()
    indexed_array+=("item1")
    indexed_array+=("item2")

    echo "${indexed_array[0]}"  # item1
}
```

### Associative Arrays (Bash 4.0+)

```bash
my_function() {
    local -A assoc_array=()
    assoc_array[key1]="value1"
    assoc_array[key2]="value2"

    echo "${assoc_array[key1]}"  # value1
}
```

### Read-Only Local Variables

```bash
my_function() {
    local -r CONSTANT="immutable"

    # CONSTANT="change"  # Error: readonly variable
}
```

## Common Pitfalls

### Pitfall 1: Forgetting `local`

```bash
# ❌ Bug-prone
process_file() {
    file="$1"  # Global!
    # ... process file ...
}

# ✅ Correct
process_file() {
    local file="$1"
    # ... process file ...
}
```

### Pitfall 2: Declaring and Assigning Together

```bash
#!/usr/bin/env bash
set -e

# ❌ Masks failure
my_function() {
    local result=$(failing_command)  # Always succeeds!
    echo "$result"
}

# ✅ Separate steps
my_function() {
    local result
    result=$(failing_command)  # Fails properly
    echo "$result"
}
```

### Pitfall 3: Using Global When Local Intended

```bash
# ❌ Subtle bug
for i in $(seq 1 10); do
    process_item "$i"
done

process_item() {
    i="$1"  # Modifies loop variable!
    # ...
}

# ✅ Use local
process_item() {
    local i="$1"  # Safe
    # ...
}
```

### Pitfall 4: Expecting Lexical Scope

```bash
outer() {
    local secret="password"
    inner
}

inner() {
    # Can access outer's local (dynamic scope)
    echo "$secret"  # Works but fragile!
}
```

**Better**: Pass explicitly:
```bash
outer() {
    local secret="password"
    inner "$secret"
}

inner() {
    local secret="$1"
    echo "$secret"
}
```

## Best Practices

### 1. Always Use `local`

```bash
# Every function variable should be local
my_function() {
    local param1="$1"
    local param2="$2"
    local result=""

    # ... logic ...
}
```

### 2. Declare Before Loop

```bash
# ✅ Good
my_function() {
    local item
    for item in "${array[@]}"; do
        echo "$item"
    done
}

# ⚠️  Works but less clear
my_function() {
    for item in "${array[@]}"; do  # item is global!
        echo "$item"
    done
}
```

### 3. Group Declarations

```bash
my_function() {
    # Group related declarations
    local input_file="$1"
    local output_file="$2"

    local -a results=()
    local -i count=0
    local -r MAX_RETRIES=3

    # ... logic ...
}
```

### 4. Use Readonly for Constants

```bash
my_function() {
    local -r MAX_SIZE=1000
    local -r CONFIG_FILE="/etc/myapp.conf"

    # MAX_SIZE=2000  # Error: readonly
}
```

## Checking Scope

### List All Variables

```bash
# All variables (including locals)
declare -p

# Only functions
declare -F

# Specific variable
declare -p var_name
```

### Check if Variable is Local

```bash
my_function() {
    local test_var="value"

    if declare -p test_var 2>/dev/null | grep -q 'declare.*--'; then
        echo "test_var has attributes"
    fi
}
```

## Summary

**Key rules**:
1. Use `local` for all function variables
2. Separate declaration from assignment (avoid SC2155)
3. Use `declare -r` for constants
4. Pass data via parameters, not dynamic scope
5. Document any global variable usage

**Default pattern**:
```bash
my_function() {
    local param="$1"
    local result

    result=$(some_command)
    echo "$result"
}
```
