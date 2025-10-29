# Arrays in Bash

Complete guide to Bash array operations, iteration, and common pitfalls.

## Array Basics

### Creating Arrays

```bash
# Empty array
arr=()

# Array with values
arr=("first" "second" "third")

# Single element (note: still an array)
arr=("single")

# Array from command output
arr=($(ls *.txt))  # Warning: Word splitting issues

# Safe: Use mapfile (Bash 4+)
mapfile -t arr < <(ls *.txt)
```

### Array Indexing (0-Based)

```bash
arr=("a" "b" "c")

echo "${arr[0]}"  # a (first element)
echo "${arr[1]}"  # b (second element)
echo "${arr[2]}"  # c (third element)
echo "${arr[3]}"  # (empty - out of bounds)
```

**Remember**: Bash uses 0-based indexing (unlike ZSH which is 1-based).

## Accessing Arrays

### Get Single Element

```bash
arr=("apple" "banana" "cherry")

# Access by index
echo "${arr[0]}"  # apple
echo "${arr[2]}"  # cherry

# Last element
echo "${arr[-1]}"  # cherry (Bash 4.3+)
echo "${arr[@]: -1}"  # cherry (portable)
```

### Get All Elements

```bash
arr=("one" "two" "three")

# All elements (quoted - preserves spaces)
echo "${arr[@]}"  # one two three

# All elements as single string
echo "${arr[*]}"  # one two three

# Difference matters in loops!
```

### Array Length

```bash
arr=("a" "b" "c")

# Number of elements
echo "${#arr[@]}"  # 3

# Length of specific element
echo "${#arr[0]}"  # 1 (length of "a")
```

### Array Indices

```bash
arr=("a" "b" "c")

# Get all indices
echo "${!arr[@]}"  # 0 1 2

# Useful for sparse arrays
unset 'arr[1]'
echo "${!arr[@]}"  # 0 2
```

## Modifying Arrays

### Append Elements

```bash
arr=("first")

# Append single element
arr+=("second")

# Append multiple elements
arr+=("third" "fourth")

echo "${arr[@]}"  # first second third fourth
```

### Prepend Elements

```bash
arr=("second" "third")

# Prepend
arr=("first" "${arr[@]}")

echo "${arr[@]}"  # first second third
```

### Remove Elements

```bash
arr=("a" "b" "c" "d")

# Remove by index
unset 'arr[2]'  # Removes "c"

# Array is now sparse
echo "${arr[@]}"  # a b d
echo "${!arr[@]}"  # 0 1 3 (index 2 missing)
```

### Replace Element

```bash
arr=("a" "b" "c")

# Replace by index
arr[1]="B"

echo "${arr[@]}"  # a B c
```

### Clear Array

```bash
arr=("a" "b" "c")

# Remove all elements
arr=()

# Or
unset arr
```

## Iterating Over Arrays

### The Correct Way (Quoted)

```bash
arr=("file one.txt" "file two.txt" "file three.txt")

# ✅ CORRECT - Preserves spaces
for item in "${arr[@]}"; do
    echo "Processing: $item"
done

# Output:
# Processing: file one.txt
# Processing: file two.txt
# Processing: file three.txt
```

### The Wrong Way (Unquoted)

```bash
arr=("file one.txt" "file two.txt")

# ❌ WRONG - Word splitting breaks items
for item in ${arr[@]}; do
    echo "Processing: $item"
done

# Output:
# Processing: file
# Processing: one.txt
# Processing: file
# Processing: two.txt
```

### Iterate with Index

```bash
arr=("a" "b" "c")

for i in "${!arr[@]}"; do
    echo "Index $i: ${arr[$i]}"
done

# Output:
# Index 0: a
# Index 1: b
# Index 2: c
```

### While Loop with Arrays

```bash
arr=("first" "second" "third")

i=0
while [[ $i -lt ${#arr[@]} ]]; do
    echo "${arr[$i]}"
    ((i++))
done
```

## Array Slicing

### Extract Subarray

```bash
arr=("a" "b" "c" "d" "e")

# Syntax: ${arr[@]:start:length}

# From index 1, take 3 elements
echo "${arr[@]:1:3}"  # b c d

# From index 2 to end
echo "${arr[@]:2}"  # c d e

# Last 2 elements
echo "${arr[@]: -2}"  # d e (note the space before -)
```

## Associative Arrays (Bash 4.0+)

### Creating Associative Arrays

```bash
# Declare associative array
declare -A config

# Assign values
config[host]="localhost"
config[port]="5432"
config[database]="mydb"
```

### Accessing Associative Arrays

```bash
declare -A config=(
    [host]="localhost"
    [port]="5432"
)

# Get value
echo "${config[host]}"  # localhost

# All keys
echo "${!config[@]}"  # host port

# All values
echo "${config[@]}"  # localhost 5432

# Check if key exists
if [[ -n "${config[host]+x}" ]]; then
    echo "host is set"
fi
```

### Iterating Over Associative Arrays

```bash
declare -A config=(
    [host]="localhost"
    [port]="5432"
    [database]="mydb"
)

# Iterate over keys and values
for key in "${!config[@]}"; do
    echo "$key = ${config[$key]}"
done
```

## Common Patterns

### Pattern 1: Array from File Lines

```bash
# Read file into array (one line per element)
mapfile -t lines < file.txt

# Or (older bash)
while IFS= read -r line; do
    lines+=("$line")
done < file.txt
```

### Pattern 2: Array from Command Output

```bash
# Safe way with mapfile
mapfile -t files < <(find . -name "*.txt")

# Or with readarray (same as mapfile)
readarray -t files < <(find . -name "*.txt")
```

### Pattern 3: Check if Array Contains Value

```bash
array=("apple" "banana" "cherry")
search="banana"

found=false
for item in "${array[@]}"; do
    if [[ "$item" == "$search" ]]; then
        found=true
        break
    fi
done

if [[ "$found" == true ]]; then
    echo "Found!"
fi
```

### Pattern 4: Remove Duplicates

```bash
arr=("a" "b" "a" "c" "b")

# Using associative array
declare -A seen
unique=()

for item in "${arr[@]}"; do
    if [[ -z "${seen[$item]+x}" ]]; then
        unique+=("$item")
        seen[$item]=1
    fi
done

echo "${unique[@]}"  # a b c
```

### Pattern 5: Sort Array

```bash
arr=("cherry" "apple" "banana")

# Sort using process substitution and mapfile
mapfile -t sorted < <(printf '%s\n' "${arr[@]}" | sort)

echo "${sorted[@]}"  # apple banana cherry
```

### Pattern 6: Join Array Elements

```bash
arr=("a" "b" "c")

# Join with delimiter
IFS=","
joined="${arr[*]}"  # Note: * not @
IFS=$' \t\n'  # Reset IFS

echo "$joined"  # a,b,c
```

## Common Pitfalls

### Pitfall 1: Unquoted Array Expansion

```bash
arr=("file one.txt" "file two.txt")

# ❌ WRONG
cp ${arr[@]} /backup/

# ✅ CORRECT
cp "${arr[@]}" /backup/
```

### Pitfall 2: Using ${arr} Instead of ${arr[0]}

```bash
arr=("first" "second" "third")

# ${arr} only gives first element!
echo "$arr"      # first
echo "${arr[0]}" # first (explicit)
echo "${arr[@]}" # first second third (all elements)
```

### Pitfall 3: Array from $(command) Without Mapfile

```bash
# ❌ WRONG - Word splitting issues
files=($(ls *.txt))

# ✅ CORRECT - No word splitting
mapfile -t files < <(ls *.txt)

# Or use globbing directly
files=(*.txt)
```

### Pitfall 4: Modifying Array in Loop

```bash
arr=("a" "b" "c")

# ❌ WRONG - Modifying array while iterating
for i in "${!arr[@]}"; do
    unset 'arr[$i]'  # Creates sparse array
done

# ✅ CORRECT - Create new array
new_arr=()
for item in "${arr[@]}"; do
    if [[ "$item" != "b" ]]; then
        new_arr+=("$item")
    fi
done
arr=("${new_arr[@]}")
```

### Pitfall 5: Forgetting -t with Mapfile

```bash
# ❌ WRONG - Includes newlines
mapfile files < <(find . -name "*.txt")

# ✅ CORRECT - Strips newlines
mapfile -t files < <(find . -name "*.txt")
```

## Array Safety Checklist

When working with arrays:

- [ ] Always quote array expansions: `"${arr[@]}"`
- [ ] Use `mapfile -t` for command output
- [ ] Check array length before accessing: `${#arr[@]}`
- [ ] Use indices for sparse arrays: `"${!arr[@]}"`
- [ ] Reset IFS after using it: `IFS=$' \t\n'`
- [ ] Declare associative arrays: `declare -A`
- [ ] Test with spaces in array elements

## Summary

**Key patterns**:
```bash
# Create
arr=("one" "two" "three")

# Access all
"${arr[@]}"

# Length
${#arr[@]}

# Iterate
for item in "${arr[@]}"; do
    echo "$item"
done

# Append
arr+=("four")

# From command
mapfile -t arr < <(command)
```

**Remember**: Always quote `"${arr[@]}"` to preserve elements with spaces.
