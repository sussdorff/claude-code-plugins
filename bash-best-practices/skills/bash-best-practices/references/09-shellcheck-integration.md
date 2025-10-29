# ShellCheck Integration

Advanced guide for using ShellCheck effectively with Bash scripts.

## ShellCheck Basics

ShellCheck is a static analysis tool for shell scripts that catches common errors, style issues, and potential bugs.

**Website**: https://www.shellcheck.net/

### Installation

```bash
# macOS
brew install shellcheck

# Linux (Debian/Ubuntu)
sudo apt-get install shellcheck

# Linux (Red Hat/Fedora)
sudo dnf install shellcheck

# From source
git clone https://github.com/koalaman/shellcheck
cd shellcheck
cabal install
```

### Basic Usage

```bash
# Check single file
shellcheck script.sh

# Check multiple files
shellcheck script1.sh script2.sh

# Check all .sh files
shellcheck *.sh

# Check with specific shell dialect
shellcheck --shell=bash script.sh
```

## Understanding ShellCheck Output

### Output Format

```
script.sh:10:5: warning: [SC2086] Double quote to prevent globbing and word splitting.
  |
  | cat $file
  |     ^-- SC2086: Double quote to prevent globbing and word splitting.
```

**Components**:
- `script.sh:10:5`: File, line, column
- `warning`: Severity level
- `[SC2086]`: Error code
- Message: What's wrong and how to fix

### Severity Levels

- **error**: Critical issues that will cause problems
- **warning**: Likely bugs or bad practices
- **info**: Suggestions for improvement
- **style**: Code style recommendations

## Common ShellCheck Warnings

### SC2086: Double quote to prevent globbing

```bash
# ❌ ShellCheck warning
file="my file.txt"
cat $file

# ✅ Fixed
cat "$file"
```

### SC2155: Declare and assign separately

```bash
# ❌ ShellCheck warning
local result=$(command)

# ✅ Fixed
local result
result=$(command)
```

### SC2164: Use 'cd ... || exit' in case cd fails

```bash
# ❌ ShellCheck warning
cd /some/directory
rm -rf *

# ✅ Fixed
cd /some/directory || exit
rm -rf *
```

### SC2046: Quote to prevent word splitting

```bash
# ❌ ShellCheck warning
rm $(find . -name "*.tmp")

# ✅ Fixed
find . -name "*.tmp" -delete
# Or
find . -name "*.tmp" -print0 | xargs -0 rm
```

### SC2034: Variable appears unused

```bash
# ❌ ShellCheck warning
my_var="value"  # Never used

# ✅ Fixed
my_var="value"
echo "$my_var"

# Or remove if truly unused
```

## Configuration

### Using .shellcheckrc

Create `.shellcheckrc` in project root:

```bash
# Specify shell dialect
shell=bash

# Disable specific warnings
disable=SC1090  # Can't follow non-constant source
disable=SC1091  # Not following sourced file

# Enable optional checks
enable=quote-safe-variables

# Set source path
source-path=SCRIPTDIR
```

### Per-File Configuration

```bash
#!/usr/bin/env bash
# shellcheck disable=SC2034  # Variable used in eval context
# shellcheck disable=SC2086  # Intentional word splitting

my_var="value"
```

### Inline Directives

```bash
# Disable for single line
# shellcheck disable=SC2086
echo $intentionally_unquoted

# Disable for block
# shellcheck disable=SC2086
{
    echo $var1
    echo $var2
}
# shellcheck enable=SC2086
```

## CLI Options

### Output Formats

```bash
# GCC-style (default)
shellcheck --format=gcc script.sh

# JSON (for tooling)
shellcheck --format=json script.sh

# CheckStyle XML
shellcheck --format=checkstyle script.sh

# Diff format (for auto-fixing)
shellcheck --format=diff script.sh | patch -p1
```

### Severity Filtering

```bash
# Only show errors
shellcheck --severity=error script.sh

# Show errors and warnings
shellcheck --severity=warning script.sh

# Show all (including info and style)
shellcheck script.sh
```

### Shell Dialect

```bash
# Bash (default)
shellcheck --shell=bash script.sh

# POSIX sh
shellcheck --shell=sh script.sh

# Dash
shellcheck --shell=dash script.sh
```

## Integration into Workflow

### Pre-Commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/usr/bin/env bash

# Find all .sh files being committed
files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.sh$')

if [[ -n "$files" ]]; then
    echo "Running ShellCheck on modified scripts..."

    if ! shellcheck $files; then
        echo "ShellCheck failed. Commit aborted."
        exit 1
    fi
fi
```

### Makefile Integration

```makefile
.PHONY: lint
lint:
	@shellcheck --severity=warning *.sh

.PHONY: lint-all
lint-all:
	@find . -name "*.sh" -exec shellcheck {} \;
```

### Combined with Function Analyzer

```bash
#!/usr/bin/env bash
# Run both ShellCheck and function analyzer

# Step 1: Lint
shellcheck --severity=warning *.sh || {
    echo "ShellCheck failed"
    exit 1
}

# Step 2: Generate metadata
bash analyze-shell-functions.sh --path . --output extract.json

echo "Linting and indexing complete"
```

## Suppression Guidelines

### When to Suppress

1. **False positives**: ShellCheck incorrectly flags valid code
2. **Intentional patterns**: Code intentionally uses flagged pattern
3. **External code**: Generated or vendored code you don't control
4. **Platform-specific**: Code that works on target platform despite warning

### When NOT to Suppress

1. **Don't understand warning**: Research it first
2. **Too many warnings**: Fix the code, don't suppress
3. **Style preference**: Follow ShellCheck's recommendations
4. **Convenience**: Suppressing is not a shortcut for writing better code

### Documentation Required

Always document suppressions:

```bash
# shellcheck disable=SC2086  # Intentional word splitting for flags
IFS=',' read -ra ITEMS <<< "$CSV"

# shellcheck disable=SC1090  # Config file path determined at runtime
source "$config_file"
```

## Advanced Usage

### Checking Specific Error Codes

```bash
# Check only for specific issue
shellcheck --include=SC2086 script.sh

# Exclude specific issues
shellcheck --exclude=SC1090,SC1091 script.sh
```

### External Sources

```bash
# Specify source path for followed files
shellcheck --source-path=lib:vendor script.sh
```

### Wiki Links

```bash
# Include wiki links in output
shellcheck --wiki-link-count=3 script.sh
```

## CI/CD Integration

### GitHub Actions

```yaml
name: ShellCheck

on: [push, pull_request]

jobs:
  shellcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run ShellCheck
        uses: ludeeus/action-shellcheck@master
        with:
          severity: warning
```

### GitLab CI

```yaml
shellcheck:
  image: koalaman/shellcheck-alpine:latest
  script:
    - shellcheck --severity=warning **/*.sh
```

## Best Practices

1. **Run ShellCheck on all scripts**
   ```bash
   find . -name "*.sh" -exec shellcheck {} \;
   ```

2. **Fix errors before warnings**
   ```bash
   shellcheck --severity=error *.sh
   ```

3. **Use .shellcheckrc for project-wide config**
   - Consistent rules across project
   - Document exceptions

4. **Combine with function analyzer**
   - Lint → Index → Discover → Extract workflow

5. **Integrate into CI/CD**
   - Fail builds on errors
   - Warning on warnings

6. **Document all suppressions**
   - Why the warning is suppressed
   - Why the code is correct

## Summary

**Essential workflow**:
```bash
# 1. Run ShellCheck
shellcheck --severity=warning *.sh

# 2. Fix errors and warnings

# 3. Regenerate metadata
bash analyze-shell-functions.sh --path . --output extract.json

# 4. Commit
```

**Key practices**:
- Always run ShellCheck before committing
- Fix errors immediately
- Address warnings when possible
- Document all suppressions
- Use .shellcheckrc for project config
- Integrate into CI/CD pipeline
