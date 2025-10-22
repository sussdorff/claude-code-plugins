# Common Bash Pitfalls

Frequent mistakes and how to avoid them.

## Pitfall 1: Unquoted Variable Expansions

**Problem**: Unquoted variables undergo word splitting and glob expansion.

```bash
# ❌ WRONG - word splitting and globbing
file="my file.txt"
touch $file  # Creates "my" and "file.txt"

# ❌ WRONG - glob expansion
files="*.txt"
rm $files  # Expands to all .txt files in current directory!

# ✅ CORRECT - always quote
touch "$file"  # Creates "my file.txt"
rm "$files"    # Removes file literally named "*.txt"
```

**Rule**: Always quote variable expansions unless intentionally performing word splitting.

## Pitfall 2: Not Using Strict Mode

**Problem**: Scripts continue executing after errors, leading to undefined behavior.

```bash
# ❌ WRONG - fails silently
#!/usr/bin/env bash
result=$(failing_command)
echo "Success"  # Prints even though command failed

# ✅ CORRECT - fails loudly
#!/usr/bin/env bash
set -euo pipefail
result=$(failing_command)  # Script exits here
```

**Always use**: `set -euo pipefail` at the top of scripts.

## Pitfall 3: Global Variable Leakage

**Problem**: Variables leak into global scope, causing unexpected side effects.

```bash
# ❌ WRONG - accidental global
my_function() {
    result="value"  # Global!
}

result="original"
my_function
echo "$result"  # Prints "value" - unexpected!

# ✅ CORRECT - explicit scope
my_function() {
    local result="value"  # Local to function
}

result="original"
my_function
echo "$result"  # Prints "original" - as expected
```

**Rule**: Always use `local` or `declare` for function variables.

## Pitfall 4: Incorrect Array Iteration

**Problem**: Unquoted array expansions break on whitespace.

```bash
# ❌ WRONG - breaks on spaces and globs
files=("file 1.txt" "file 2.txt")
for item in ${files[@]}; do
    echo "$item"  # Prints "file", "1.txt", "file", "2.txt"
done

# ✅ CORRECT - proper quoting
for item in "${files[@]}"; do
    echo "$item"  # Prints "file 1.txt", "file 2.txt"
done
```

**Rule**: Always quote array expansions: `"${array[@]}"`.

## Pitfall 5: Using [ Instead of [[

**Problem**: `[` is an external command with quirky behavior.

```bash
# ❌ WRONG - word splitting issues
var=""
if [ $var = "value" ]; then  # Syntax error when var is empty!
    echo "match"
fi

# ❌ WRONG - no regex support
if [ "$string" =~ ^[0-9]+$ ]; then  # =~ doesn't work with [
    echo "number"
fi

# ✅ CORRECT - [[ is safer
if [[ $var = "value" ]]; then  # Works with empty var
    echo "match"
fi

# ✅ CORRECT - [[ supports regex
if [[ $string =~ ^[0-9]+$ ]]; then
    echo "number"
fi
```

**Rule**: Prefer `[[` over `[` in Bash scripts.

## Pitfall 6: Testing $? Incorrectly

**Problem**: `$?` gets overwritten by every command.

```bash
# ❌ WRONG - $? gets overwritten
command
if [[ -n "$var" ]]; then  # This sets $? !
    if [[ $? -eq 0 ]]; then  # Wrong $?
        echo "Success"
    fi
fi

# ✅ CORRECT - capture immediately
command
status=$?
if [[ -n "$var" ]]; then
    if [[ $status -eq 0 ]]; then
        echo "Success"
    fi
fi

# ✅ BETTER - use direct testing
if command; then
    echo "Success"
fi
```

**Rule**: Capture `$?` immediately or use direct command testing.

## Pitfall 7: Unsafe cd Operations

**Problem**: `cd` might fail, but script continues in wrong directory.

```bash
# ❌ WRONG - dangerous if cd fails
cd /some/directory
rm -rf *  # Might delete everything in current directory!

# ✅ CORRECT - fail if cd fails
cd /some/directory || exit 1
rm -rf *

# ✅ BETTER - with strict mode
set -e
cd /some/directory  # Script exits if this fails
rm -rf *

# ✅ BEST - subshell for safety
(cd /some/directory && rm -rf *)  # Doesn't affect parent shell
```

**Rule**: Always check `cd` return value or use strict mode.

## Pitfall 8: Masking Return Values with local

**Problem**: `local var=$(command)` masks command's return value.

```bash
# ❌ WRONG - masks return value
my_function() {
    local result=$(failing_command)  # Always returns 0!
    echo "$result"
}

# ✅ CORRECT - declare and assign separately
my_function() {
    local result
    result=$(failing_command)  # Preserves return value
    echo "$result"
}
```

**Rule**: Declare and assign separately when return value matters.

## Pitfall 9: Forgetting to Quote Command Substitutions

**Problem**: Command substitutions undergo word splitting.

```bash
# ❌ WRONG - word splitting
files=$(ls *.txt)
for file in $files; do  # Breaks on filenames with spaces
    echo "$file"
done

# ✅ CORRECT - quote or use array
mapfile -t files < <(find . -name "*.txt")
for file in "${files[@]}"; do
    echo "$file"
done
```

**Rule**: Quote command substitutions or use arrays.

## Pitfall 10: Not Handling Spaces in Filenames

**Problem**: Many operations break when filenames contain spaces.

```bash
# ❌ WRONG - breaks on spaces
for file in $(ls); do  # DON'T parse ls output!
    rm "$file"
done

# ✅ CORRECT - use glob patterns
for file in *; do
    rm "$file"
done

# ✅ BETTER - use find with null separator
find . -type f -name "*.tmp" -print0 | xargs -0 rm

# ✅ BEST - use find with exec
find . -type f -name "*.tmp" -exec rm {} +
```

**Rule**: Never parse `ls` output; use globs or `find`.

## Pitfall 11: Incorrect String Comparison

**Problem**: Using `-eq` instead of `=` for strings.

```bash
# ❌ WRONG - -eq is for numbers
if [[ "$status" -eq "active" ]]; then  # Treats strings as numbers
    echo "active"
fi

# ✅ CORRECT - = for strings
if [[ "$status" = "active" ]]; then
    echo "active"
fi

# ✅ ALSO CORRECT - == works too
if [[ "$status" == "active" ]]; then
    echo "active"
fi
```

**Rule**: Use `=` or `==` for strings, `-eq` for numbers.

## Pitfall 12: Not Handling Errors in Pipelines

**Problem**: Without `pipefail`, pipeline succeeds if last command succeeds.

```bash
# ❌ WRONG - ignores grep failure
grep "pattern" file.txt | sort | head -10
# Succeeds even if grep fails!

# ✅ CORRECT - pipefail catches failures
set -o pipefail
grep "pattern" file.txt | sort | head -10
# Fails if any command fails
```

**Rule**: Always use `set -o pipefail` with pipelines.

## Pitfall 13: Assuming Bash is at /bin/bash

**Problem**: Bash location varies across systems.

```bash
# ❌ WRONG - assumes /bin/bash
#!/bin/bash  # Might be old version on macOS

# ✅ CORRECT - uses PATH lookup
#!/usr/bin/env bash  # Finds bash via PATH
```

**Rule**: Use `#!/usr/bin/env bash` for portability.

## Pitfall 14: Not Validating Input

**Problem**: Scripts fail cryptically with unexpected input.

```bash
# ❌ WRONG - no validation
divide() {
    echo $(($1 / $2))  # Fails with non-numbers or zero
}

# ✅ CORRECT - validate input
divide() {
    local a="$1"
    local b="$2"

    # Check arguments provided
    if [[ $# -ne 2 ]]; then
        echo "Error: Two arguments required" >&2
        return 1
    fi

    # Check numeric
    if [[ ! "$a" =~ ^-?[0-9]+$ ]] || [[ ! "$b" =~ ^-?[0-9]+$ ]]; then
        echo "Error: Arguments must be numbers" >&2
        return 1
    fi

    # Check division by zero
    if [[ "$b" -eq 0 ]]; then
        echo "Error: Division by zero" >&2
        return 1
    fi

    echo $((a / b))
}
```

**Rule**: Always validate input before using it.

## Pitfall 15: Using Bash for Complex JSON Processing

**Problem**: Bash is not designed for structured data manipulation.

```bash
# ❌ WRONG - fragile JSON parsing
json='{"name":"John","age":30}'
name=$(echo "$json" | sed 's/.*"name":"\([^"]*\)".*/\1/')

# ✅ CORRECT - use jq
name=$(echo "$json" | jq -r '.name')
```

**Rule**: Use `jq` for JSON, `yq` for YAML, `xmlstarlet` for XML.

## Related References

- [02-strict-mode.md](02-strict-mode.md) - Strict mode patterns
- [06-error-handling.md](06-error-handling.md) - Error handling strategies
- [07-quoting-and-expansion.md](07-quoting-and-expansion.md) - Quoting rules
- [04-arrays.md](04-arrays.md) - Array operations
- [10-code-review-checklist.md](10-code-review-checklist.md) - Review checklist
