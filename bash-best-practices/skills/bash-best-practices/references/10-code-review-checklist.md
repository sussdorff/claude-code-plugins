# Bash Code Review Checklist

Comprehensive checklist for reviewing and writing production-ready Bash scripts.

## Critical Issues (Always Fix)

### Strict Mode

- [ ] Script starts with `#!/usr/bin/env bash`
- [ ] Includes `set -euo pipefail` immediately after shebang
- [ ] No unintentional `set +e` or `set +u` that isn't re-enabled
- [ ] Pipelines checked with `set -o pipefail`

### Variable Quoting

- [ ] All variables quoted: `"$var"` not `$var`
- [ ] Array expansions quoted: `"${arr[@]}"` not `${arr[@]}`
- [ ] Command substitutions quoted: `"$(command)"`
- [ ] Paths with spaces handled correctly

### Error Handling

- [ ] Cleanup function defined and registered: `trap cleanup EXIT`
- [ ] Error trap for debugging: `trap 'echo "Error at line $LINENO" >&2' ERR`
- [ ] Errors written to stderr: `>&2`
- [ ] Exit codes checked for critical operations
- [ ] Temporary files cleaned up on all exit paths

### Variable Scoping

- [ ] All function variables declared with `local`
- [ ] No accidental global variables in functions
- [ ] Declaration and assignment separated to avoid masking failures:
  ```bash
  # ❌ local result=$(command)
  # ✅ local result; result=$(command)
  ```

### Array Handling

- [ ] Arrays use 0-based indexing (not ZSH 1-based)
- [ ] Arrays iterated correctly: `for item in "${arr[@]}"`
- [ ] `mapfile -t` used for command output, not `array=($(command))`

### ShellCheck

- [ ] Script passes ShellCheck with no errors
- [ ] Warnings addressed or suppressed with documentation
- [ ] All suppressions documented with reason

## Important Issues (Usually Fix)

### Script Organization

- [ ] Script has meaningful header comment (purpose, usage)
- [ ] Functions defined before use
- [ ] Main logic in `main()` function
- [ ] Script constants defined with `readonly`

### Function Design

- [ ] Functions have single responsibility
- [ ] Function names use `verb_noun` pattern
- [ ] Parameters passed explicitly, not via global variables
- [ ] Return values via `echo` or exit code, not globals

### Error Messages

- [ ] Error messages include context (filename, line number, what failed)
- [ ] Error messages explain what went wrong and possibly how to fix
- [ ] Consistent error message format

### Path Handling

- [ ] Script directory detected correctly:
  ```bash
  readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  ```
- [ ] Paths built safely (handles trailing slashes)
- [ ] `cd` operations checked: `cd "$dir" || exit`

### Input Validation

- [ ] Required arguments checked
- [ ] File existence checked before reading
- [ ] Directory existence checked before writing
- [ ] User input validated before use

## Style Suggestions (Case-by-Case)

### Naming Conventions

- [ ] Variables: `lower_snake_case`
- [ ] Constants: `UPPER_SNAKE_CASE`
- [ ] Functions: `lower_snake_case`
- [ ] Files: `lower-kebab-case.sh`

### Documentation

- [ ] Complex functions have comment explaining purpose
- [ ] Non-obvious code has explanatory comments
- [ ] Usage information in header or `--help` option

### Code Style

- [ ] Consistent indentation (2 or 4 spaces)
- [ ] Opening brace on same line: `function_name() {`
- [ ] Closing brace on own line: `}`
- [ ] One command per line
- [ ] Logical grouping with blank lines

### Modern Bash Features

- [ ] Use `[[` instead of `[` for conditionals
- [ ] Use `$(command)` instead of backticks
- [ ] Use `mapfile` or `readarray` for reading files
- [ ] Use process substitution where appropriate: `<(command)`

## Security Checklist

### Input Handling

- [ ] User input never passed directly to `eval`
- [ ] User input never used in command construction without validation
- [ ] File paths validated (no `../` injection)
- [ ] User input sanitized before logging

### Command Execution

- [ ] No use of `eval` with untrusted input
- [ ] Commands use explicit paths or are validated
- [ ] File operations use absolute paths where critical
- [ ] Temporary files created with `mktemp`

### Secrets Management

- [ ] No hardcoded passwords or API keys
- [ ] Sensitive data not echoed to logs
- [ ] Credentials read from environment or secure files
- [ ] Temporary files with secrets have restrictive permissions

## Cross-Platform Compatibility

### Portability

- [ ] Script works on both Linux and macOS
- [ ] No GNU-specific features without fallbacks
- [ ] Date commands use portable format
- [ ] `sed` and `awk` use portable syntax

### Tool Availability

- [ ] Required external tools checked: `command -v tool`
- [ ] Graceful degradation if optional tools missing
- [ ] Error messages if required tools unavailable

## Performance Considerations

### Efficiency

- [ ] No unnecessary subshells
- [ ] No repeated command executions in loops
- [ ] Large file processing uses streaming, not loading entire file
- [ ] External commands minimized (use Bash built-ins)

### Resource Management

- [ ] No memory leaks (arrays cleared after use)
- [ ] File descriptors closed properly
- [ ] Background jobs cleaned up
- [ ] Loops have reasonable termination conditions

## Testing Considerations

### Testability

- [ ] Functions are small and testable
- [ ] Side effects minimized
- [ ] Dependencies can be mocked
- [ ] Exit codes meaningful

### Test Coverage

- [ ] Script tested with valid input
- [ ] Script tested with invalid input
- [ ] Error conditions tested
- [ ] Edge cases considered

## Specific Pattern Checks

### Array Operations

```bash
# ✅ Correct patterns
arr=("one" "two" "three")
for item in "${arr[@]}"; do echo "$item"; done
arr+=("four")
echo "${#arr[@]}"  # Length

# ❌ Wrong patterns
for item in ${arr[@]}; do echo "$item"; done  # Unquoted
arr[$i]="value"  # Without checking bounds
```

### Command Substitution

```bash
# ✅ Correct
local result
result=$(command) || {
    echo "Command failed" >&2
    exit 1
}

# ❌ Wrong
local result=$(command)  # Masks failure
```

### Conditionals

```bash
# ✅ Correct
if [[ -f "$file" ]]; then
    cat "$file"
fi

if [[ "$var" == "value" ]]; then
    echo "Match"
fi

# ❌ Wrong
if [ $var == "value" ]; then  # Unquoted, wrong operator
    echo "Match"
fi
```

### Loops

```bash
# ✅ Correct
while IFS= read -r line; do
    echo "$line"
done < file.txt

# ❌ Wrong
for line in $(cat file.txt); do  # Word splitting
    echo "$line"
done
```

## Automation Checklist

### CI/CD Integration

- [ ] Script tested in CI/CD pipeline
- [ ] Shell Check runs on every commit
- [ ] Tests run automatically
- [ ] Coverage reported

### Deployment

- [ ] Script works in target environment
- [ ] Dependencies documented
- [ ] Installation tested
- [ ] Rollback procedure documented

## Review Process

### Pre-Review

1. Run ShellCheck: `shellcheck script.sh`
2. Run script with strict mode
3. Test with edge cases
4. Generate function metadata: `bash analyze-shell-functions.sh`

### During Review

1. Check critical issues first
2. Look for security vulnerabilities
3. Verify error handling
4. Test quoted variables with spaces
5. Confirm cleanup on all exit paths

### Post-Review

1. Regenerate extract.json after changes
2. Re-run ShellCheck
3. Update tests
4. Document any exceptions

## Common Anti-Patterns to Avoid

### Anti-Pattern 1: Silent Failures

```bash
# ❌ Wrong
command_that_might_fail
echo "Success"

# ✅ Correct
if ! command_that_might_fail; then
    echo "Error: Command failed" >&2
    exit 1
fi
```

### Anti-Pattern 2: Unquoted Variables

```bash
# ❌ Wrong
rm $temp_file

# ✅ Correct
rm "$temp_file"
```

### Anti-Pattern 3: Global Variables in Functions

```bash
# ❌ Wrong
process_file() {
    result="value"  # Global!
}

# ✅ Correct
process_file() {
    local result="value"
    echo "$result"
}
```

### Anti-Pattern 4: Not Cleaning Up

```bash
# ❌ Wrong
temp=$(mktemp)
# ... use temp ...
# No cleanup if script fails!

# ✅ Correct
temp=$(mktemp)
trap 'rm -f "$temp"' EXIT
# ... use temp ...
```

## Quick Review Commands

```bash
# Lint all scripts
find . -name "*.sh" -exec shellcheck {} \;

# Check for common issues
grep -n 'set.*-e' *.sh  # Verify strict mode
grep -n '\$[a-zA-Z_]' *.sh | grep -v '"'  # Find unquoted vars
grep -n 'local.*\$(' *.sh  # Find declaration+assignment

# Verify metadata is up to date
bash analyze-shell-functions.sh --path . --output extract.json
```

## Summary

**Must fix before merge**:
- ShellCheck errors
- Unquoted variables
- Missing strict mode
- No error handling
- Global variable leakage

**Should fix before merge**:
- ShellCheck warnings
- Missing cleanup
- Poor error messages
- No input validation

**Nice to have**:
- Consistent style
- Good documentation
- Test coverage

**Review workflow**:
1. Run ShellCheck
2. Check critical issues
3. Test with edge cases
4. Regenerate metadata
5. Approve or request changes
