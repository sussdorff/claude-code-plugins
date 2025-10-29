# Word Splitting and Quoting in ZSH

## The Major Difference from Bash

**Critical:** By default, ZSH does NOT perform word splitting on unquoted parameter expansions.

### Bash Behavior (Default Word Splitting)

```bash
#!/bin/bash
var="foo bar baz"
for word in $var; do
    echo "$word"
done
# Output:
# foo
# bar
# baz
```

### ZSH Behavior (No Word Splitting by Default)

```zsh
#!/bin/zsh
var="foo bar baz"
for word in $var; do
    echo "$word"
done
# Output:
# foo bar baz
```

## Benefits of ZSH's Approach

1. **Less Error-Prone**: No need to quote variables constantly
2. **More Predictable**: Variables remain intact unless explicitly split
3. **Closer to Other Languages**: Behaves like most programming languages

## Enabling Word Splitting

### Option 1: Global Setting (Not Recommended for Scripts)

```zsh
setopt SH_WORD_SPLIT  # Enable bash-like word splitting globally
```

⚠️ **Warning**: Never add this to `.zshrc` - it breaks ZSH assumptions

### Option 2: Per-Variable Expansion (Recommended)

```zsh
var="foo bar baz"
for word in ${=var}; do  # Note the = flag
    echo "$word"
done
# Output:
# foo
# bar
# baz
```

### Option 3: Local Function Setting

```zsh
process_with_splitting() {
    emulate -L zsh
    setopt LOCAL_OPTIONS SH_WORD_SPLIT

    local var="foo bar baz"
    for word in $var; do
        echo "$word"
    done
}
```

## Command Substitution Exception

ZSH **does** split the results of unquoted command substitution:

```zsh
# This WILL split
for file in $(ls); do
    echo "$file"
done

# Better alternative using arrays
files=($(ls))
for file in "${files[@]}"; do
    echo "$file"
done
```

## IFS Configuration

Word splitting boundaries are controlled by the `IFS` variable:

```zsh
# Default IFS contains: space, tab, newline
IFS=$' \t\n'

# Custom delimiter
IFS=:
var="foo:bar:baz"
for word in ${=var}; do
    echo "$word"
done
```

## Best Practices

### ✅ DO: Rely on ZSH's Default Behavior

```zsh
# No quotes needed for variables
filename="my file.txt"
touch "$filename"  # Still quote for safety
```

### ✅ DO: Use ${=var} When Splitting is Intentional

```zsh
options="--verbose --debug --color"
command ${=options} file.txt
```

### ❌ DON'T: Set SH_WORD_SPLIT Globally

```zsh
# BAD - breaks ZSH conventions
setopt SH_WORD_SPLIT
```

### ✅ DO: Use Arrays for Multiple Values

```zsh
# Better than relying on word splitting
files=("file1.txt" "file with spaces.txt" "file3.txt")
for file in "${files[@]}"; do
    echo "$file"
done
```

## Bash Compatibility Mode

If writing a script that must work in both bash and zsh:

```zsh
#!/bin/zsh
# Detect ZSH and enable bash compatibility
if [[ -n "$ZSH_VERSION" ]]; then
    emulate -LR sh
fi
```

## Parameter Expansion Flags

ZSH provides explicit control over expansion behavior:

```zsh
var="foo  bar  baz"

# No splitting, no globbing
echo $var          # foo  bar  baz

# Split on IFS
echo ${=var}       # foo bar baz

# Split and glob
echo ${~=var}      # foo bar baz (with globbing if patterns match)

# Quote explicitly (same as default in ZSH)
echo "${var}"      # foo  bar  baz
```

## Migration from Bash

When migrating bash scripts to ZSH:

1. **Test word splitting**: Check if `$var` needs `${=var}`
2. **Review loops**: Verify `for` loops handle multi-word items correctly
3. **Check command substitutions**: These still split in ZSH
4. **Consider arrays**: ZSH arrays are more powerful than bash

## Summary

- **Default**: ZSH does not split unquoted variables
- **Explicit**: Use `${=var}` when splitting is needed
- **Safe**: This makes ZSH less error-prone than bash
- **Compatible**: Use `emulate sh` for bash-compatible scripts
