# Path Manipulation in Bash

Safe and portable patterns for working with file paths.

## Script Path Detection

### Get Script Directory

```bash
#!/usr/bin/env bash

# Recommended: Resolves symlinks
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Alternative: Doesn't resolve symlinks (faster)
readonly SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

# Use SCRIPT_DIR for relative paths
readonly CONFIG_FILE="${SCRIPT_DIR}/config.conf"
```

### Get Script Name

```bash
#!/usr/bin/env bash

# Just the filename
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

# Without extension
readonly SCRIPT_NAME_NO_EXT="$(basename "${BASH_SOURCE[0]}" .sh)"
```

### Executed vs Sourced

```bash
#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Script is being executed"
else
    echo "Script is being sourced"
fi
```

## Common Path Operations

### dirname - Get Parent Directory

```bash
path="/usr/local/bin/script.sh"

# Get directory part
dir="$(dirname "$path")"  # /usr/local/bin

# Parent of current directory
parent="$(dirname "$PWD")"
```

### basename - Get Filename

```bash
path="/usr/local/bin/script.sh"

# Get filename
name="$(basename "$path")"  # script.sh

# Remove extension
name_no_ext="$(basename "$path" .sh)"  # script
```

### realpath - Resolve Absolute Path

```bash
# Convert relative to absolute
abs_path="$(realpath relative/path/file.txt)"

# Resolve symlinks
real_path="$(realpath symlink.txt)"

# Check if realpath exists
if command -v realpath &> /dev/null; then
    abs_path="$(realpath "$file")"
else
    # Fallback
    abs_path="$(cd "$(dirname "$file")" && pwd)/$(basename "$file")"
fi
```

## Building Paths Safely

### Concatenate Path Components

```bash
# ✅ GOOD - Handles trailing slashes
base_dir="/usr/local"
sub_dir="bin"
full_path="${base_dir}/${sub_dir}"

# ✅ BETTER - Remove trailing slash first
base_dir="/usr/local/"
sub_dir="bin"
full_path="${base_dir%/}/${sub_dir}"  # /usr/local/bin

# ✅ BEST - Use function
join_path() {
    local base="${1%/}"
    local sub="$2"
    echo "${base}/${sub}"
}

full_path="$(join_path "/usr/local/" "bin")"
```

### Handle Spaces in Paths

```bash
# Always quote paths
dir="/path/with spaces"

# ✅ CORRECT
cd "$dir"
ls "$dir"
cp "$file" "$dir/"

# ❌ WRONG
cd $dir  # Fails!
```

## Path Validation

### Check if Path Exists

```bash
path="/some/path"

# File or directory exists
if [[ -e "$path" ]]; then
    echo "Path exists"
fi

# Is a file
if [[ -f "$path" ]]; then
    echo "Is a file"
fi

# Is a directory
if [[ -d "$path" ]]; then
    echo "Is a directory"
fi

# Is a symlink
if [[ -L "$path" ]]; then
    echo "Is a symlink"
fi
```

### Check Path Permissions

```bash
file="/path/to/file"

# Readable
if [[ -r "$file" ]]; then
    echo "Can read"
fi

# Writable
if [[ -w "$file" ]]; then
    echo "Can write"
fi

# Executable
if [[ -x "$file" ]]; then
    echo "Can execute"
fi
```

## Path Transformation

### Remove File Extension

```bash
filename="document.tar.gz"

# Remove last extension
echo "${filename%.*}"  # document.tar

# Remove all extensions
echo "${filename%%.*}"  # document
```

### Get File Extension

```bash
filename="document.tar.gz"

# Get last extension
echo "${filename##*.}"  # gz

# Get all extensions
echo "${filename#*.}"  # tar.gz
```

### Change File Extension

```bash
filename="document.txt"

# Replace extension
new_name="${filename%.txt}.md"  # document.md
```

## Temporary Files and Directories

### Create Temporary File

```bash
# Secure temporary file
temp_file="$(mktemp)"
echo "data" > "$temp_file"

# Clean up
trap 'rm -f "$temp_file"' EXIT

# With custom template
temp_file="$(mktemp /tmp/myapp.XXXXXX)"

# In system temp directory
temp_file="$(mktemp -t myapp.XXXXXX)"
```

### Create Temporary Directory

```bash
# Secure temporary directory
temp_dir="$(mktemp -d)"
echo "data" > "${temp_dir}/file.txt"

# Clean up
trap 'rm -rf "$temp_dir"' EXIT

# With custom template
temp_dir="$(mktemp -d -t myapp.XXXXXX)"
```

## Cross-Platform Considerations

### macOS vs Linux Differences

```bash
# realpath might not exist on macOS
if command -v realpath &> /dev/null; then
    abs_path="$(realpath "$file")"
else
    # Fallback for macOS
    abs_path="$(cd "$(dirname "$file")" && pwd)/$(basename "$file")"
fi

# mktemp syntax differs
# macOS: mktemp -t prefix
# Linux: mktemp -t prefix.XXXXXX or mktemp --tmpdir=DIR

# Portable:
temp_file="$(mktemp "${TMPDIR:-/tmp}/myapp.XXXXXX")"
```

## Common Patterns

### Pattern 1: Find Project Root

```bash
#!/usr/bin/env bash

find_project_root() {
    local dir="$PWD"

    while [[ "$dir" != "/" ]]; do
        if [[ -f "${dir}/.git/config" ]] || [[ -f "${dir}/package.json" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done

    return 1
}

PROJECT_ROOT="$(find_project_root)"
```

### Pattern 2: Relative Path from Absolute

```bash
# Convert absolute path to relative
# (requires realpath or Python)

if command -v realpath &> /dev/null; then
    rel_path="$(realpath --relative-to="$base_dir" "$target_path")"
else
    # Fallback using Python
    rel_path="$(python3 -c "import os.path; print(os.path.relpath('$target_path', '$base_dir'))")"
fi
```

### Pattern 3: Normalize Path

```bash
# Remove . and .. from path
normalize_path() {
    local path="$1"

    # Use realpath if available
    if command -v realpath &> /dev/null; then
        realpath -m "$path"  # -m: don't require existence
        return
    fi

    # Fallback: Use cd
    if [[ -e "$path" ]]; then
        (cd "$(dirname "$path")" && pwd)/$(basename "$path")
    else
        echo "$path"  # Can't normalize non-existent path
    fi
}
```

## Summary

**Essential patterns**:
```bash
# Script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

# Path operations
dir="$(dirname "$path")"
name="$(basename "$path")"
abs="$(realpath "$path")"  # If available

# Temporary files
temp="$(mktemp)"
trap 'rm -f "$temp"' EXIT

# Always quote paths
cd "$dir"
ls "$file"
```
