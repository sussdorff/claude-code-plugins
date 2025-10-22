# JSON Processing in ZSH

## Critical: Avoid Pipes and Subshells for Stateful Operations

**Problem**: Pipes and certain operations create subshells, causing variable updates to be lost.

## The Pipe Subshell Problem

### ❌ WRONG - Variables Lost in Pipeline

```zsh
#!/bin/zsh
set -euo pipefail

counter=0

# Variables modified in pipelines are LOST!
jq -c '.[]' file.json | while read line; do
    counter=$((counter + 1))  # Lost when pipe ends!
    echo "Processing item $counter"
done

echo "Total: $counter"  # Still 0!
```

### ❌ WRONG - Echo Pipe Also Creates Subshell

```zsh
counter=0

echo "$data" | while read line; do
    counter=$((counter + 1))  # Also lost!
done

echo "Total: $counter"  # Still 0!
```

## ✅ SAFE PATTERN - Array-Based Iteration

### Load JSON into Array First

```zsh
#!/bin/zsh
set -euo pipefail

# Load JSON into array first
local -a items
while IFS= read -r line; do
    items+=("$line")
done < <(jq -c '.array[]' file.json)

# Process with for loop (no subshell!)
local counter=0
for item in "${items[@]}"; do
    # Extract fields
    local name=$(echo "$item" | jq -r '.name')
    local value=$(echo "$item" | jq -r '.value')

    # Update counters safely
    counter=$((counter + 1))  # Safe - persists!

    echo "Processing $name: $value"
done

echo "Total processed: $counter"  # Works!
```

## Key Rules for JSON Processing

1. **Always load JSON into arrays** before processing
2. **Use `for` loops** instead of `while | pipe` for stateful operations
3. **Use explicit arithmetic**: `counter=$((counter + 1))` not `((counter++))`
4. **Avoid pipes** when you need to track/update variables

## Arithmetic Pitfalls with `set -e`

### ❌ Can Hang or Fail Silently

```zsh
set -e

counter=0
((counter++))  # May fail silently or hang with set -e
```

### ✅ Safe Arithmetic

```zsh
set -e

counter=0
counter=$((counter + 1))  # Explicit, safe
```

## File-Based Processing for Complex Data

**Critical**: For large JSON payloads or complex data, use temporary files instead of command substitution.

### ❌ PROBLEMATIC - Command Substitution

```zsh
set -euo pipefail

# Issues with large JSON, special characters, and strict error handling
local mr_json=$(glab mr list --search "${ticket}" --output json 2>/dev/null || echo "[]")
local branch_name=$(echo "$mr_json" | jq -r '.[0].source_branch')
```

Problems:
- Quoting/escaping issues with special characters
- Fails unpredictably with `set -euo pipefail`
- Hard to debug
- Pipe subshell issues
- Memory concerns with large payloads

### ✅ ROBUST - File-Based Approach

```zsh
set -euo pipefail

# Reliable with any data size
local temp_file=$(mktemp -t operation-XXXXXX.json)

# Write to file
glab mr list --search "${ticket}" --output json > "$temp_file" 2>/dev/null

# Test file, not string
if [[ -s "$temp_file" ]]; then  # File exists and is non-empty
    local branch_name=$(jq -r '.[0].source_branch // empty' "$temp_file")

    if [[ -n "$branch_name" ]]; then
        echo "Branch: $branch_name"
    fi
fi

# Cleanup
rm -f "$temp_file"
```

Benefits:
- Works reliably with `set -euo pipefail`
- No quoting/escaping issues
- Easier to debug (can inspect temp file)
- No pipe subshell issues
- Handles large payloads

## File Testing Over String Comparisons

### ✅ BETTER - File Test

```zsh
if [[ -s "$temp_file" ]]; then  # File exists and is non-empty
    # Process file
    local data=$(jq -r '.field' "$temp_file")
fi
```

### ❌ AVOID - String Comparison After Reading

```zsh
local json=$(cat file.json)
if [[ "$json" != "[]" ]] && [[ -n "$json" ]]; then
    # More fragile
fi
```

## Safe jq Patterns

### Use `// empty` Operator

```zsh
# ✅ CLEAN - jq handles null
local value=$(jq -r '.field // empty' file.json)
if [[ -n "$value" ]]; then
    # Value exists and is not null
    echo "$value"
fi
```

### ❌ VERBOSE - Manual Null Checking

```zsh
local value=$(jq -r '.field' file.json)
if [[ -n "$value" ]] && [[ "$value" != "null" ]]; then
    # More code, same result
    echo "$value"
fi
```

## Safe JSON Construction

**Always use `jq -n` for JSON construction**, never manual string concatenation.

### ❌ WRONG - Manual Concatenation

```zsh
# Escaping nightmares!
local json="{\"name\": \"$name\", \"value\": \"$value\"}"
```

### ✅ CORRECT - Use jq -n

```zsh
# Single values
local json=$(jq -n --arg name "$name" --arg value "$value" '{
    name: $name,
    value: $value
}')

# Arrays
local -a items=("one" "two" "three")
local json=$(jq -n \
    --argjson arr "$(printf '%s\n' "${items[@]}" | jq -R . | jq -s .)" \
    '{items: $arr}'
)
```

## Complete Example: Processing JSON API Response

```zsh
#!/bin/zsh
set -euo pipefail

process_api_data() {
    local api_endpoint="$1"

    # Use temporary file for API response
    local temp_file=$(mktemp -t api-response-XXXXXX.json)

    # Fetch data
    curl -s "$api_endpoint" > "$temp_file" 2>/dev/null

    # Validate response
    if [[ ! -s "$temp_file" ]]; then
        echo "Error: Empty response"
        rm -f "$temp_file"
        return 1
    fi

    # Load items into array
    local -a items
    while IFS= read -r line; do
        items+=("$line")
    done < <(jq -c '.data[]' "$temp_file")

    # Process items with state tracking
    local processed=0
    local failed=0

    for item in "${items[@]}"; do
        local id=$(echo "$item" | jq -r '.id // empty')
        local name=$(echo "$item" | jq -r '.name // empty')

        if [[ -z "$id" ]] || [[ -z "$name" ]]; then
            failed=$((failed + 1))
            continue
        fi

        echo "Processing: $name (ID: $id)"
        processed=$((processed + 1))
    done

    # Cleanup
    rm -f "$temp_file"

    # Results
    echo "Processed: $processed"
    echo "Failed: $failed"
}
```

## Temporary File Cleanup

### ✅ ZSH/Bash - Manual Cleanup

```zsh
local temp_file=$(mktemp -t operation-XXXXXX.json)

# ... do work ...

if [[ condition ]]; then
    rm -f "$temp_file"
    return 0
fi

rm -f "$temp_file"  # Also at end
return 1
```

### Consider trap for Critical Cleanup

```zsh
#!/bin/zsh

cleanup() {
    rm -f "$temp_file"
}

trap cleanup EXIT INT TERM

temp_file=$(mktemp -t operation-XXXXXX.json)

# ... do work ...
# cleanup runs automatically on exit
```

## Common Patterns

### Pattern 1: Load, Process, Count

```zsh
# Load array
local -a records
while IFS= read -r line; do
    records+=("$line")
done < <(jq -c '.[]' data.json)

# Process with counters
local total=0
local valid=0

for record in "${records[@]}"; do
    total=$((total + 1))

    if validate_record "$record"; then
        valid=$((valid + 1))
    fi
done

echo "Valid: $valid / $total"
```

### Pattern 2: Filter and Collect

```zsh
local -a filtered
while IFS= read -r line; do
    filtered+=("$line")
done < <(jq -c '.[] | select(.active == true)' data.json)

# Build new JSON from filtered items
local output=$(jq -n --argjson items "$(printf '%s\n' "${filtered[@]}" | jq -s .)" '{
    filtered_count: ($items | length),
    items: $items
}')
```

### Pattern 3: Transform and Accumulate

```zsh
local -a results
local total_value=0

while IFS= read -r item; do
    local value=$(echo "$item" | jq -r '.value // 0')
    total_value=$((total_value + value))
    results+=("$item")
done < <(jq -c '.items[]' data.json)

echo "Total value: $total_value"
echo "Items processed: ${#results[@]}"
```

## Summary

### Core Principles

1. **Load into arrays** before processing (avoid pipes)
2. **Use temp files** for large/complex JSON
3. **Test files** not strings (`[[ -s file ]]`)
4. **Use `jq -n`** for JSON construction
5. **Use `// empty`** for safe null handling
6. **Explicit arithmetic** (`x=$((x+1))` not `((x++))`)

### When to Use Each Pattern

- **Array loading**: When you need to track state across iterations
- **File-based**: For API responses, large JSON, or complex data
- **jq -n**: When constructing JSON output
- **temp files**: Always for external command output with `set -euo pipefail`
