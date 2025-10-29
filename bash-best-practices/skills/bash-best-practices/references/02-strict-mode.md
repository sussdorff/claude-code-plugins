# Bash Strict Mode

Understanding `set -euo pipefail` and error-resistant scripting.

## What is Strict Mode?

**Strict mode** makes Bash fail fast and loud when errors occur, preventing silent failures and cascading bugs.

**The standard pattern**:
```bash
#!/usr/bin/env bash
set -euo pipefail
```

This single line transforms Bash from "permissive and dangerous" to "strict and safe."

## The Three Flags

### Flag 1: `set -e` (Exit on Error)

**What it does**: Exit immediately if any command fails (returns non-zero).

```bash
#!/usr/bin/env bash
set -e

# Without set -e:
false
echo "This would print"  # Prints!

# With set -e:
false
echo "This never prints"  # Script exits at false
```

**Why it matters**:

```bash
# ❌ Without set -e (dangerous)
#!/usr/bin/env bash
cd /important/directory
rm -rf *  # If cd failed, deletes current directory!

# ✅ With set -e (safe)
#!/usr/bin/env bash
set -e
cd /important/directory  # Script exits here if it fails
rm -rf *  # Only runs if cd succeeded
```

**Exceptions** (commands that don't trigger exit):

```bash
# 1. Commands in if/while/until conditions
if false; then  # Doesn't exit
    echo "Won't print"
fi

# 2. Commands with || or &&
false || echo "Handled"  # Doesn't exit

# 3. Commands whose return value is explicitly tested
false
echo $?  # Doesn't exit, just prints 1

# 4. Commands in pipelines (unless -o pipefail is set)
false | true  # Doesn't exit (without pipefail)
```

### Flag 2: `set -u` (Error on Undefined Variables)

**What it does**: Treat unset variables as errors.

```bash
#!/usr/bin/env bash
set -u

# Without set -u:
echo "$undefined_var"  # Prints empty string (silent bug!)

# With set -u:
echo "$undefined_var"  # ERROR: unbound variable
```

**Why it matters**:

```bash
# ❌ Without set -u (catastrophic)
#!/usr/bin/env bash
rm -rf /$undefined_path/*  # Becomes: rm -rf /*

# ✅ With set -u (safe)
#!/usr/bin/env bash
set -u
rm -rf /$undefined_path/*  # ERROR: unbound variable (script exits)
```

**Safe patterns with set -u**:

```bash
# Check if variable is set
if [[ -n "${var:-}" ]]; then
    echo "var is set to: $var"
fi

# Provide default value
target_dir="${TARGET_DIR:-/tmp}"

# Test for unset explicitly
if [[ -z "${var+x}" ]]; then
    echo "var is unset"
else
    echo "var is set to: $var"
fi
```

### Flag 3: `set -o pipefail` (Fail on Pipeline Errors)

**What it does**: Return value of a pipeline is the status of the last command to exit with a non-zero status (or zero if all succeed).

```bash
#!/usr/bin/env bash
set -o pipefail

# Without pipefail:
false | true
echo $?  # Prints: 0 (only checks last command)

# With pipefail:
false | true
echo $?  # Prints: 1 (checks all commands)
```

**Why it matters**:

```bash
# ❌ Without pipefail (silent failure)
#!/usr/bin/env bash
set -e

curl https://api.example.com/data | jq '.results[]'
# If curl fails, jq sees empty input, returns 0
# Script continues (data loss)!

# ✅ With pipefail (fails properly)
#!/usr/bin/env bash
set -eo pipefail

curl https://api.example.com/data | jq '.results[]'
# If curl fails, entire pipeline fails
# Script exits (data loss prevented)
```

## Complete Strict Mode Pattern

```bash
#!/usr/bin/env bash
set -euo pipefail

# Optional: Enhanced error reporting
trap 'echo "Error: Command failed at line $LINENO" >&2' ERR

# Your script here
```

## When to Use Each Flag

| Flag | When to Use | When to Skip |
|------|-------------|--------------|
| `-e` | Always (production scripts) | Never skip |
| `-u` | Always (production scripts) | Interactive scripts with optional vars |
| `-o pipefail` | Always (production scripts) | Pipelines where partial success is OK |

**Default recommendation**: Always use all three.

## Advanced: `set -E` (Inherit ERR Trap)

**What it does**: ERR trap is inherited by shell functions, command substitutions, and subshells.

```bash
#!/usr/bin/env bash
set -eEuo pipefail

trap 'echo "Error in ${FUNCNAME[0]:-main} at line $LINENO" >&2' ERR

my_function() {
    # ERR trap applies here too (because of -E)
    false  # Triggers trap
}

my_function
```

**When to use**: When you want consistent error reporting in functions.

## Common Pitfalls with Strict Mode

### Pitfall 1: Forgot to Handle Expected Failures

```bash
#!/usr/bin/env bash
set -euo pipefail

# ❌ Script exits if file doesn't exist
if [[ -f "$config_file" ]]; then
    source "$config_file"
fi

# ✅ Correct: Test works with -e
if [[ -f "$config_file" ]]; then
    source "$config_file"
else
    echo "No config file, using defaults"
fi
```

### Pitfall 2: Unintentional set -e Bypass

```bash
#!/usr/bin/env bash
set -euo pipefail

# ❌ -e doesn't apply to condition
if important_command; then
    echo "Success"
fi
# If important_command fails, script continues!

# ✅ Correct: Run outside condition, check explicitly
important_command
if [[ $? -eq 0 ]]; then
    echo "Success"
fi

# ✅ Better: Let it fail, handle with || or trap
important_command || {
    echo "Error: Command failed" >&2
    exit 1
}
```

### Pitfall 3: Unset Variable with Default

```bash
#!/usr/bin/env bash
set -euo pipefail

# ❌ Fails with "unbound variable"
if [[ "$optional_var" == "value" ]]; then
    echo "Match"
fi

# ✅ Correct: Provide default
if [[ "${optional_var:-}" == "value" ]]; then
    echo "Match"
fi
```

### Pitfall 4: Pipeline with Expected Failures

```bash
#!/usr/bin/env bash
set -euo pipefail

# ❌ Fails if grep finds nothing
cat file.txt | grep "pattern" | wc -l

# ✅ Option 1: Disable pipefail temporarily
set +o pipefail
count=$(cat file.txt | grep "pattern" | wc -l)
set -o pipefail

# ✅ Option 2: Handle grep's return code
count=$(grep -c "pattern" file.txt || true)

# ✅ Option 3: Use || with explicit check
if grep -q "pattern" file.txt; then
    count=$(grep -c "pattern" file.txt)
else
    count=0
fi
```

## Temporarily Disabling Strict Mode

Sometimes you need to temporarily disable flags:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Temporarily disable -e for a section
set +e
optional_command  # Won't exit if it fails
result=$?
set -e

if [[ $result -eq 0 ]]; then
    echo "Optional command succeeded"
else
    echo "Optional command failed (OK)"
fi

# Temporarily disable -u to check if var is set
set +u
if [[ -z "$maybe_unset" ]]; then
    echo "Variable is unset or empty"
fi
set -u
```

**Rule**: Always re-enable immediately after the exception.

## Strict Mode Variations

### Paranoid Mode (Maximum Safety)

```bash
#!/usr/bin/env bash
set -eEuo pipefail
IFS=$'\n\t'  # Strict word splitting

trap 'echo "Error at $BASH_SOURCE:$LINENO" >&2' ERR
```

**What `IFS=$'\n\t'` does**: Only split on newlines and tabs, not spaces.

### Relaxed Mode (Interactive Scripts)

```bash
#!/usr/bin/env bash
set -eo pipefail
# Note: -u omitted for interactive scripts
```

### Debug Mode

```bash
#!/usr/bin/env bash
set -euxo pipefail  # Added -x for tracing

# Every command is printed before execution
```

## Testing with Strict Mode

### Verify Strict Mode is Active

```bash
#!/usr/bin/env bash
set -euo pipefail

# Check if flags are set
if [[ $- == *e* ]]; then echo "errexit is set"; fi
if [[ $- == *u* ]]; then echo "nounset is set"; fi
if [[ -o pipefail ]]; then echo "pipefail is set"; fi
```

### Test Script Handles Errors

```bash
#!/usr/bin/env bash
set -euo pipefail

# Function that might fail
risky_operation() {
    # Simulate failure
    return 1
}

# Test: Does script exit?
risky_operation  # Should cause script to exit

# This line should never execute
echo "ERROR: Strict mode failed to catch error!"
```

## Real-World Examples

### Example 1: Database Backup Script

```bash
#!/usr/bin/env bash
set -euo pipefail

readonly DB_NAME="myapp"
readonly BACKUP_DIR="/backups"
readonly DATE=$(date +%Y%m%d)

# Any of these commands fail → script exits → no partial backup
pg_dump "$DB_NAME" > "${BACKUP_DIR}/backup-${DATE}.sql"
gzip "${BACKUP_DIR}/backup-${DATE}.sql"
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed successfully"
```

### Example 2: Deployment Script

```bash
#!/usr/bin/env bash
set -eEuo pipefail

trap 'echo "Deployment failed at line $LINENO" >&2; exit 1' ERR

readonly APP_DIR="/var/www/app"
readonly BACKUP_DIR="/var/backups/app"

# Backup current version
cp -r "$APP_DIR" "${BACKUP_DIR}/backup-$(date +%s)"

# Deploy new version (fails fast if any step breaks)
git fetch origin
git checkout main
git pull origin main
npm install
npm run build
systemctl restart app

echo "Deployment completed successfully"
```

### Example 3: Data Processing Pipeline

```bash
#!/usr/bin/env bash
set -euo pipefail

readonly INPUT_FILE="$1"
readonly OUTPUT_FILE="$2"

# Pipeline: Any command fails → entire script fails
cat "$INPUT_FILE" |
    grep -v "^#" |
    sort -u |
    awk '{print $1,$3}' |
    sed 's/foo/bar/g' \
    > "$OUTPUT_FILE"

echo "Processing completed: $(wc -l < "$OUTPUT_FILE") lines"
```

## Strict Mode Checklist

Use this checklist for all production scripts:

- [ ] Script starts with `#!/usr/bin/env bash`
- [ ] Includes `set -euo pipefail` immediately after shebang
- [ ] All variables quoted: `"$var"` not `$var`
- [ ] Undefined variables handled with `${var:-default}`
- [ ] Expected failures use `command || true` or `if command; then`
- [ ] Cleanup trap registered: `trap cleanup EXIT`
- [ ] Error trap for debugging: `trap 'echo "Error at line $LINENO" >&2' ERR`
- [ ] Tested with intentional failures to verify error handling
- [ ] Passes ShellCheck with no errors

## Summary

**Always start scripts with**:
```bash
#!/usr/bin/env bash
set -euo pipefail
```

**What it prevents**:
- Silent failures (`-e`)
- Typo bugs (`-u`)
- Pipeline hiding errors (`-o pipefail`)

**When to deviate**: Rarely. Document why if you do.

**Remember**: Strict mode isn't optional for production scripts—it's mandatory.
