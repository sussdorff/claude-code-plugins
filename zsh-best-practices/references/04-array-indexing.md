# Array Indexing in ZSH

## The 1-Based Index Difference

**Critical:** ZSH arrays are indexed starting from **1**, not 0 (unlike bash/ksh).

### ZSH Default (1-Based)

```zsh
#!/bin/zsh
fruits=("apple" "banana" "cherry")

echo "${fruits[1]}"  # apple
echo "${fruits[2]}"  # banana
echo "${fruits[3]}"  # cherry
echo "${fruits[0]}"  # (empty - index 0 doesn't exist)
```

### Bash/KSH (0-Based)

```bash
#!/bin/bash
fruits=("apple" "banana" "cherry")

echo "${fruits[0]}"  # apple
echo "${fruits[1]}"  # banana
echo "${fruits[2]}"  # cherry
```

## Historical Context

- **Most shells use 1-based indexing**: Bourne, csh, tcsh, fish, rc, es, yash
- **ksh is the exception**: Uses 0-based (bash copied ksh)
- **ZSH follows the majority**: Stays with traditional 1-based indexing

## Enabling 0-Based Indexing (Compatibility Mode)

### Using KSH_ARRAYS Option

```zsh
#!/bin/zsh
setopt KSH_ARRAYS  # Enable 0-based indexing

fruits=("apple" "banana" "cherry")
echo "${fruits[0]}"  # apple
echo "${fruits[1]}"  # banana
echo "${fruits[2]}"  # cherry
```

### ⚠️ Critical Warnings

1. **Never set in .zshrc**: This breaks interactive ZSH and all tools expecting ZSH behavior
2. **Isolate with LOCAL_OPTIONS**: Use within functions only
3. **Document clearly**: Anyone reading the code needs to know indexing changed

### Safe Pattern: Local Function Scope

```zsh
#!/bin/zsh

compat_function() {
    emulate -L zsh
    setopt LOCAL_OPTIONS KSH_ARRAYS  # Only affects this function

    local fruits=("apple" "banana" "cherry")
    echo "${fruits[0]}"  # apple (0-based here)
}

# Outside the function, ZSH still uses 1-based
main_fruits=("apple" "banana" "cherry")
echo "${main_fruits[1]}"  # apple (1-based)
```

## Array Syntax Differences

### Declaration

```zsh
# All three syntaxes work in ZSH
arr=("one" "two" "three")
arr=(one two three)
arr[1]=one arr[2]=two arr[3]=three
```

### All Elements

```zsh
fruits=("apple" "banana" "cherry")

# All elements (maintains word boundaries)
echo "${fruits[@]}"   # apple banana cherry

# All elements as single string
echo "${fruits[*]}"   # apple banana cherry

# Array length
echo "${#fruits[@]}"  # 3
```

### Slicing (ZSH Feature)

```zsh
fruits=("apple" "banana" "cherry" "date" "elderberry")

# Elements 2-4 (inclusive, 1-based)
echo "${fruits[2,4]}"    # banana cherry date

# From element 3 to end
echo "${fruits[3,-1]}"   # cherry date elderberry

# Last element
echo "${fruits[-1]}"     # elderberry

# Last 2 elements
echo "${fruits[-2,-1]}"  # date elderberry
```

### String Substring Extraction (1-Based)

**Important:** ZSH uses **1-based indexing** for substring extraction (unlike bash's 0-based):

```zsh
text="Hello World"

# ZSH-native syntax (1-based, consistent with arrays)
echo "${text[1,5]}"      # Hello (characters 1-5)
echo "${text[7,11]}"     # World (characters 7-11)
echo "${text[1,19]}"     # Hello World (first 19 chars, or less if shorter)

# Bash-compatible syntax (0-based, but inconsistent with ZSH arrays)
echo "${text:0:5}"       # Hello (offset 0, length 5)
echo "${text:6:5}"       # World (offset 6, length 5)
```

**Best Practice:** Use ZSH-native `[start,end]` syntax for consistency with array indexing:

```zsh
# ✅ GOOD - Consistent with ZSH array indexing
typeset date="2025-10-20T12:34:56"
echo "${date[1,10]}"     # 2025-10-20 (1-based, like arrays)

# ❌ AVOID - Bash-style, inconsistent with ZSH arrays
echo "${date:0:10}"      # 2025-10-20 (0-based, confusing)
```

**Why prefer ZSH-native syntax:**
- **Consistency:** Arrays use `[1]`, strings should too
- **Clarity:** Same mental model throughout your script
- **ZSH-specific:** If writing ZSH-only code, embrace ZSH idioms

## Portable Array Access (Bash + ZSH)

### Problem: Different Indexing

```zsh
# Won't work consistently across bash and zsh
arr=("first" "second" "third")
echo "${arr[0]}"  # "first" in bash, "" in zsh
echo "${arr[1]}"  # "second" in bash, "first" in zsh
```

### Solution 1: Offset Syntax

```zsh
# Works in both bash and zsh
arr=("first" "second" "third")

# First element (offset 0, length 1)
echo "${arr[@]:0:1}"  # first (both shells)

# Second element
echo "${arr[@]:1:1}"  # second (both shells)

# All elements
echo "${arr[@]}"      # works in both
```

### Solution 2: Detect Shell

```zsh
#!/bin/zsh

if [[ -n "$ZSH_VERSION" ]]; then
    setopt KSH_ARRAYS
fi

# Now array[0] works consistently
arr=("first" "second" "third")
echo "${arr[0]}"  # first (both shells)
```

### Solution 3: Use #!/bin/sh

```sh
#!/bin/sh
# POSIX doesn't define arrays
# Use separate variables or whitespace-separated strings
```

## Iteration Patterns

### Iterate Over Values

```zsh
fruits=("apple" "banana" "cherry")

# Recommended: Use @ for proper word splitting
for fruit in "${fruits[@]}"; do
    echo "Fruit: $fruit"
done
```

### Iterate Over Indices

```zsh
fruits=("apple" "banana" "cherry")

# ZSH way (1-based)
for i in {1..${#fruits[@]}}; do
    echo "Index $i: ${fruits[$i]}"
done

# Alternative using parameter expansion
for i in "${(@k)fruits}"; do
    echo "Index $i: ${fruits[$i]}"
done
```

## Associative Arrays (Dictionaries)

ZSH has powerful associative array support:

```zsh
#!/bin/zsh

# Declare associative array
typeset -A user

# Add key-value pairs
user[name]="Alice"
user[email]="alice@example.com"
user[age]=30

# Access values
echo "${user[name]}"   # Alice

# Iterate over keys
for key in "${(@k)user}"; do
    echo "$key: ${user[$key]}"
done

# Check if key exists
if [[ -v user[name] ]]; then
    echo "Name exists"
fi
```

## Best Practices

### ✅ DO: Embrace 1-Based Indexing for Pure ZSH

```zsh
#!/bin/zsh
arr=("first" "second" "third")
echo "${arr[1]}"  # first
```

### ✅ DO: Use KSH_ARRAYS Only in Local Function Scope

```zsh
compat_func() {
    emulate -L zsh
    setopt LOCAL_OPTIONS KSH_ARRAYS
    # 0-based indexing here
}
```

### ❌ DON'T: Mix Indexing Styles

```zsh
# BAD - confusing!
arr=("a" "b" "c")
echo "${arr[1]}"  # a
setopt KSH_ARRAYS
echo "${arr[1]}"  # b (now different!)
```

### ✅ DO: Use Portable Syntax for Cross-Shell Scripts

```zsh
# Use offset:length instead of subscripts
echo "${arr[@]:0:1}"  # Works in bash and zsh
```

### ✅ DO: Document Indexing Assumptions

```zsh
#!/bin/zsh
# This script uses ZSH's default 1-based array indexing

arr=("first" "second" "third")
first="${arr[1]}"  # Clear: explicitly 1-based
```

## Common Pitfalls

### Pitfall 1: Off-By-One Errors

```zsh
# Coming from bash
arr=("a" "b" "c")
echo "${arr[0]}"  # Expected "a", got ""
echo "${arr[1]}"  # Got "a" - need to adjust mental model
```

### Pitfall 2: Loop Boundaries

```zsh
# Wrong (bash mindset)
for ((i=0; i<${#arr[@]}; i++)); do
    echo "${arr[$i]}"  # Skips first element!
done

# Right (ZSH way)
for ((i=1; i<=${#arr[@]}; i++)); do
    echo "${arr[$i]}"
done

# Better (idiomatic)
for item in "${arr[@]}"; do
    echo "$item"
done
```

### Pitfall 3: Global KSH_ARRAYS

```zsh
# NEVER do this in .zshrc or global scope
setopt KSH_ARRAYS  # Breaks all ZSH tools and scripts!
```

## Migration Guide

### From Bash to ZSH

```zsh
# Bash code
arr=("zero" "one" "two")
echo "${arr[0]}"  # zero

# ZSH equivalent
arr=("zero" "one" "two")
echo "${arr[1]}"  # zero (adjust index)

# OR use compatibility mode
setopt KSH_ARRAYS
echo "${arr[0]}"  # zero (same as bash)
```

### Making Dual-Compatible Code

```zsh
#!/usr/bin/env zsh

# Detect and normalize
if [[ -n "$ZSH_VERSION" ]]; then
    setopt KSH_ARRAYS  # Make ZSH behave like bash
fi

# Now can use 0-based indexing
arr=("zero" "one" "two")
echo "${arr[0]}"  # Works in both
```

## Summary

- **Default ZSH**: 1-based indexing (arr[1] is first element)
- **Compatibility**: Use `setopt KSH_ARRAYS` for 0-based indexing
- **Scope**: Only use KSH_ARRAYS in local function scope
- **Portable**: Use offset syntax `${arr[@]:0:1}` for cross-shell code
- **Best Practice**: Embrace ZSH's 1-based indexing for pure ZSH scripts
