# ZSH Code Review Checklist

This document defines what the Claude Code agent checks when reviewing ZSH scripts.

## When Code Review Happens

The agent automatically reviews ZSH scripts when:
- You ask to "review this script"
- You ask to "check for bugs"
- You request "apply zsh best practices"
- Writing new ZSH scripts
- Modifying existing ZSH scripts

## Critical Issues (Always Fix)

### 1. Global Variable Leakage

**What to check:**
Variables created without `typeset` or `local` leak into global scope.

```zsh
# ❌ BAD - Creates global variable
my_function() {
    result="value"  # Oops, global!
}

# ✅ GOOD - Properly scoped
my_function() {
    typeset result="value"  # Local to function
}
```

**Detection:** Look for assignments in functions without prior `typeset`/`local` declaration.

### 2. Arithmetic Increment with NO_UNSET

**What to check:**
`(( var++ ))` fails when `setopt NO_UNSET` is enabled.

```zsh
# ❌ BAD - Fails with NO_UNSET
typeset -i counter=0
(( counter++ ))  # Script exits here!

# ✅ GOOD - Works with NO_UNSET
typeset -i counter=0
counter=$((counter + 1))
```

**Detection:** Look for `(( var++ ))` or `(( var-- ))` patterns when `NO_UNSET` is set.

**Reference:** [05-strict-mode-and-options.md:243-302](05-strict-mode-and-options.md)

### 3. Incorrect Array Append

**What to check:**
`arr+=elem` doesn't work consistently; must use `arr+=(elem)`.

```zsh
# ❌ BAD - Unreliable
typeset -a items
items+=new_item

# ✅ GOOD - Always works
typeset -a items
items+=(new_item)
```

**Detection:** Look for `array+=value` without parentheses.

### 4. Unquoted Variable Expansions

**What to check:**
Unquoted variables in dangerous contexts can cause word splitting issues.

```zsh
# ❌ BAD - Will break with spaces in filename
file="my file.txt"
rm $file  # Tries to remove "my" and "file.txt"

# ✅ GOOD - Quotes protect from splitting
rm "$file"  # Removes "my file.txt"
```

**Detection:** Look for unquoted `$var` in:
- Command arguments
- Test conditions
- Array assignments

**Exception:** Word splitting is intentional with `${=var}` flag.

### 5. 0-Based Array Indexing

**What to check:**
ZSH uses 1-based indexing by default (unlike Bash).

```zsh
# ❌ BAD - Bash thinking
typeset -a items=(first second third)
echo "${items[0]}"  # Empty in ZSH!

# ✅ GOOD - ZSH indexing
echo "${items[1]}"  # "first"
```

**Detection:** Look for `array[0]` access patterns.

**Note:** Don't suggest fixing if script uses `setopt KSH_ARRAYS`.

### 6. Reserved/Read-Only Variable Names

**What to check:**
ZSH has special read-only variables that cannot be assigned in strict mode.

```zsh
# ❌ BAD - Using reserved variable name
check_status() {
    typeset status=$(git status)  # Error: read-only variable!
}

# ✅ GOOD - Use different name
check_status() {
    typeset git_status=$(git status)  # Works fine
}
```

**Common reserved variables:**
- `status` - Exit status of last pipeline
- `pipestatus` - Array of exit statuses for each command in pipeline
- `ERRNO` - Last system error number
- `signals` - Array of signal names
- `galiases`, `dis_aliases`, `dis_functions`, etc.

**Detection:** Look for `typeset status=`, `typeset pipestatus=`, or other common reserved names.

**Why it matters:** In strict mode (`emulate -LR zsh` + `NO_UNSET`), assigning to read-only variables causes immediate script failure.

**Reference:** Use `set | grep -E '^(readonly|special)'` to see all read-only variables.

## Important Issues (Usually Fix)

### 7. Missing Recommended Setopts

**What to check:**
Scripts should set recommended options for safety and consistency.

```zsh
# ✅ GOOD - Recommended options
emulate -LR zsh
setopt ERR_EXIT ERR_RETURN NO_UNSET PIPE_FAIL
setopt extendedglob warncreateglobal typesetsilent noshortloops nopromptsubst
```

**Detection:** Check for missing:
- `extendedglob` - Extended pattern matching
- `warncreateglobal` - Warn on accidental globals
- `typesetsilent` - Suppress typeset output
- `noshortloops` - Disable ambiguous short syntax
- `nopromptsubst` - Prevent prompt expansion in strings

### 8. Autoload Without -U Flag

**What to check:**
`autoload` should use `-U` to prevent alias expansion issues.

```zsh
# ❌ SUBOPTIMAL
autoload my_function

# ✅ BETTER
autoload -Uz my_function  # -U no aliases, -z ZSH style
```

**Detection:** Look for `autoload` without `-U` flag.

### 9. zparseopts Without -F Flag

**What to check:**
`zparseopts` should use `-F` to catch typos in options.

```zsh
# ❌ MISSING TYPO DETECTION
zparseopts -D -E args -- -verbose v -debug d

# ✅ WITH TYPO DETECTION
zparseopts -D -E -F args -- -verbose v -debug d
```

**Detection:** Look for `zparseopts` without `-F` flag.

## Style Suggestions (Review Case-by-Case)

### 10. Variable Declaration Patterns

**Prefer explicit types:**
```zsh
# ✅ GOOD - Clear intent
typeset -i counter=0
typeset -r CONST="value"
typeset -a items=()
typeset -A config=()
```

### 11. Script Metadata Pattern

**Recommend this pattern:**
```zsh
# ✅ GOOD - Works when sourced
typeset -r SCRIPT_DIR="${${(%):-%x}:A:h}"
typeset -r SCRIPT_NAME="${${(%):-%x}:t}"
```

**Don't complain about alternatives** - there are many valid patterns.

### 12. Cleanup Handlers

**Recommend cleanup pattern:**
```zsh
cleanup() {
    [[ -n "${TmpDir:-}" && -d "$TmpDir" ]] && rm -rf "$TmpDir"
}
trap cleanup EXIT INT TERM
```

## What NOT to Check

### ❌ Don't Be Opinionated About:

1. **$0 assignment patterns** - Many valid approaches exist
2. **emulate -o vs setopt** - Both work fine
3. **Naming conventions** - Unless clearly inconsistent within the codebase
4. **Comment style** - Personal preference
5. **Function vs script structure** - Context-dependent

## Review Output Format

When reviewing, provide:

1. **Issue category** (Critical / Important / Style)
2. **Line number** (when applicable)
3. **What's wrong** (brief description)
4. **Why it matters** (explain the bug/risk)
5. **How to fix** (concrete code suggestion)

### Example Output

```
Critical Issues:
- Line 42: Global variable leakage
  Variable 'result' assigned without typeset/local
  → This pollutes global scope and can cause bugs
  → Fix: Add 'typeset result' before assignment

Important Issues:
- Line 10: Missing recommended setopts
  Script missing 'warncreateglobal' option
  → Won't warn about accidental global variables
  → Fix: Add 'setopt warncreateglobal' after emulate

Style Suggestions:
- Line 5: Consider explicit type declaration
  Current: COUNTER=0
  → Not clear this is an integer
  → Suggest: typeset -i COUNTER=0
```

## Quick Reference

**Critical (always fix):**
- Global variable leakage
- `(( var++ ))` with NO_UNSET
- Wrong array append syntax
- Unquoted expansions
- 0-based array indexing
- Reserved/read-only variable names (`status`, `pipestatus`, etc.)

**Important (usually fix):**
- Missing recommended setopts
- `autoload` without `-U`
- `zparseopts` without `-F`

**Style (case-by-case):**
- Explicit type declarations
- Script metadata patterns
- Cleanup handlers
