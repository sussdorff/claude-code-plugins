# Quoting and Word Splitting in Bash

Understanding when and how to quote variables to prevent bugs.

## The Golden Rule

**Always quote variables unless you have a specific reason not to.**

```bash
# ✅ ALWAYS DO THIS
echo "$var"
ls "$directory"
cp "$source" "$destination"

# ❌ RARELY DO THIS (only when you want word splitting)
echo $var
```

## Why Quoting Matters

### Word Splitting

```bash
file="my document.txt"

# ❌ Without quotes (word splitting occurs)
cat $file
# Bash sees: cat my document.txt
# Error: cat: my: No such file or directory

# ✅ With quotes (no word splitting)
cat "$file"
# Bash sees: cat "my document.txt"
# Works correctly
```

### Glob Expansion

```bash
pattern="*.txt"

# ❌ Without quotes (glob expansion)
echo $pattern
# Output: file1.txt file2.txt file3.txt (all .txt files)

# ✅ With quotes (literal string)
echo "$pattern"
# Output: *.txt
```

## Types of Quotes

### Double Quotes: "..." (Variable Expansion)

```bash
name="Alice"

# Variables expand inside double quotes
echo "Hello, $name"  # Hello, Alice

# Command substitution works
echo "Today is $(date)"

# Arithmetic expansion works
echo "Result: $((2 + 2))"
```

### Single Quotes: '...' (Literal String)

```bash
name="Alice"

# NO expansion inside single quotes
echo 'Hello, $name'  # Hello, $name (literal)

# Command substitution doesn't work
echo 'Today is $(date)'  # Today is $(date) (literal)
```

### No Quotes: Word Splitting + Glob Expansion

```bash
# Unquoted = word splitting + glob expansion
var="a b c"
echo $var  # Three arguments: a, b, c

# Dangerous!
rm $var  # Tries to remove files named a, b, and c
```

## When to Quote

### Always Quote These

```bash
# ✅ File paths
cp "$source" "$destination"

# ✅ User input
echo "You entered: $user_input"

# ✅ Command substitution
result="$(command)"

# ✅ Variables with spaces
directory="/path/with spaces"
cd "$directory"

# ✅ Array elements
for item in "${array[@]}"; do
    echo "$item"
done
```

### Rarely Leave Unquoted

```bash
# Only when you explicitly want word splitting
flags="-v -x -a"
# WRONG: command $flags
# RIGHT: Use array instead
flags=(-v -x -a)
command "${flags[@]}"
```

## Array Quoting

### The Critical Difference

```bash
arr=("file one.txt" "file two.txt")

# ✅ CORRECT: "${arr[@]}" - Each element separate
for file in "${arr[@]}"; do
    echo "$file"
done
# Output:
# file one.txt
# file two.txt

# ❌ WRONG: ${arr[@]} - Word splitting breaks elements
for file in ${arr[@]}; do
    echo "$file"
done
# Output:
# file
# one.txt
# file
# two.txt

# "${arr[*]}" - Single string (all elements joined)
echo "${arr[*]}"
# Output: file one.txt file two.txt
```

## Special Cases

### Empty Variables

```bash
# ❌ With set -u, this fails if var is unset
echo "$var"

# ✅ Provide default if unset
echo "${var:-default}"

# ✅ Test if set first
if [[ -n "${var:-}" ]]; then
    echo "$var"
fi
```

### Variable in String

```bash
name="Alice"

# ✅ Variable in string
echo "Hello, $name!"  # Hello, Alice!

# ✅ Separate variable from text
echo "${name}_suffix"  # Alice_suffix

# ❌ Without braces (ambiguous)
echo "$name_suffix"  # (looks for $name_suffix variable)
```

### Preserving Whitespace

```bash
# Preserve newlines
text="line1
line2
line3"

# ✅ Quotes preserve newlines
echo "$text"
# Output:
# line1
# line2
# line3

# ❌ Without quotes, newlines become spaces
echo $text
# Output: line1 line2 line3
```

## Parameter Expansion with Quotes

### Default Values

```bash
# Use default if unset or empty
echo "${var:-default}"

# Assign default if unset
: "${var:=default}"

# Error if unset
echo "${var:?Variable is required}"

# Alternative if set
echo "${var:+alternative}"
```

### String Operations

```bash
filename="document.txt"

# Remove suffix
echo "${filename%.txt}"  # document

# Remove prefix
path="/usr/local/bin/app"
echo "${path##*/}"  # app

# Replace
echo "${filename/txt/md}"  # document.md
```

## Common Pitfalls

### Pitfall 1: Forgetting Quotes with User Input

```bash
#!/usr/bin/env bash

# ❌ DANGEROUS
read -p "Enter filename: " filename
cat $filename  # Vulnerable to injection!

# ✅ SAFE
read -r -p "Enter filename: " filename
cat "$filename"
```

### Pitfall 2: Quotes in Conditionals

```bash
# ✅ [[ ]] - Quotes optional but recommended
if [[ $var == "value" ]]; then
    echo "Match"
fi

# ⚠️  [ ] - Quotes REQUIRED
if [ "$var" = "value" ]; then
    echo "Match"
fi

# ❌ [ ] without quotes - BREAKS
var=""
if [ $var = "value" ]; then  # Syntax error!
    echo "Match"
fi
```

### Pitfall 3: Command Arguments

```bash
# ❌ WRONG
args="--option value"
command $args  # Becomes: command --option value (OK)

args="--option 'value with spaces'"
command $args  # Becomes: command --option 'value with spaces' (quotes literal!)

# ✅ CORRECT - Use array
args=(--option "value with spaces")
command "${args[@]}"  # Correct word splitting
```

## Advanced Quoting

### Escaping Special Characters

```bash
# Backslash escapes single character
echo "Quote: \" and dollar: \$"

# Or use single quotes
echo 'Quote: " and dollar: $'
```

### ANSI-C Quoting: $'...'

```bash
# Interpret escape sequences
echo $'Line 1\nLine 2\tTabbed'

# Hex and octal
echo $'\x41'  # A
echo $'\101'  # A
```

### Locale-Aware: $"..."

```bash
# Allows translation
echo $"Welcome"  # Can be translated by gettext
```

## Quoting Checklist

- [ ] All variables quoted: `"$var"`
- [ ] Arrays quoted: `"${arr[@]}"`
- [ ] Command substitution quoted: `"$(command)"`
- [ ] Paths with spaces quoted
- [ ] User input always quoted
- [ ] Use `[[ ]]` instead of `[ ]` for better quoting behavior
- [ ] Test with spaces in variables: `var="a b c"`
- [ ] Test with empty variables: `var=""`

## Summary

**Simple rules**:
1. **Always quote variables**: `"$var"`
2. **Always quote arrays**: `"${arr[@]}"`
3. **Use double quotes for expansion**: `"$var"`
4. **Use single quotes for literals**: `'$var'`
5. **Test with spaces**: `var="a b c"`

**Common pattern**:
```bash
#!/usr/bin/env bash
set -euo pipefail

file="$1"

if [[ -f "$file" ]]; then
    content="$(cat "$file")"
    echo "File contents: $content"
fi
```
