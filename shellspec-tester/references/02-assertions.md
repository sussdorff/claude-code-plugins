# ShellSpec Assertions Reference

Complete guide to all assertion types in ShellSpec for verifying test expectations.

## Basic Assertion Syntax

```bash
The <subject> should <matcher> <expected>
```

Components:
- **The**: Starts an assertion
- **subject**: What to test (output, status, variable, file, etc.)
- **should**: Expectation type (or `should not` for negation)
- **matcher**: Comparison operator (equal, match, include, etc.)
- **expected**: Expected value

## Subject Types

### Output Assertions

Test standard output from commands:

```bash
It 'outputs greeting'
  greet() { echo "Hello, World!"; }
  When call greet
  The output should equal "Hello, World!"
End
```

### Error Output Assertions

Test standard error:

```bash
It 'outputs error to stderr'
  error_func() { echo "Error occurred" >&2; }
  When call error_func
  The stderr should include "Error"
End
```

### Combined Output

Test combined stdout and stderr:

```bash
The entire output should include "something"
```

### Status (Exit Code) Assertions

Test exit codes:

```bash
It 'returns success'
  When call true
  The status should be success  # Exit code 0
End

It 'returns failure'
  When call false
  The status should be failure  # Exit code non-zero
End

It 'returns specific exit code'
  When call exit 42
  The status should equal 42
End
```

Predefined status values:
- `success` → 0
- `failure` → non-zero (typically 1)

### Variable Assertions

Test variable values:

```bash
It 'sets variable correctly'
  name="Alice"
  The variable name should equal "Alice"
End

It 'checks variable is set'
  value="something"
  The variable value should be defined
End

It 'checks variable is unset'
  The variable undefined_var should be undefined
End
```

### File Assertions

Test file properties:

```bash
# File existence
The file "/path/to/file" should be exist
The file "/path/to/file" should not be exist

# File type
The file "/path/to/file" should be file
The file "/path/to/dir" should be directory
The file "/path/to/link" should be symlink

# File permissions
The file "/path/to/script" should be executable
The file "/path/to/config" should be readable
The file "/path/to/data" should be writable

# File contents
The contents of file "/path/to/file" should equal "expected content"
The contents of file "/path/to/file" should include "partial"

# File size
The file "/path/to/file" should be empty
The file "/path/to/file" should not be empty
```

### Line Count Assertions

Test number of output lines:

```bash
It 'outputs 3 lines'
  list_items() {
    echo "item1"
    echo "item2"
    echo "item3"
  }
  When call list_items
  The lines of output should equal 3
End
```

### Word Count Assertions

Test number of words in output:

```bash
It 'outputs 5 words'
  When call echo "one two three four five"
  The words of output should equal 5
End
```

## Matcher Types

### Equality Matchers

#### equal

Exact string match:

```bash
The output should equal "exact match"
The status should equal 0
```

#### be

Alias for `equal`:

```bash
The status should be 0
The output should be "exact"
```

### Comparison Matchers

#### Numeric Comparisons

```bash
# Greater than
The value x should be greater than 5
# or
The value x should be gt 5

# Greater than or equal
The value x should be greater than or equal 10
# or
The value x should be ge 10

# Less than
The value x should be less than 20
# or
The value x should be lt 20

# Less than or equal
The value x should be less than or equal 15
# or
The value x should be le 15
```

Example:

```bash
It 'validates range'
  count=10
  The variable count should be gt 5
  The variable count should be lt 20
End
```

### Pattern Matchers

#### match

Regular expression matching:

```bash
The output should match pattern '^[0-9]+$'
The output should match pattern 'ERROR:.*failed'
```

Examples:

```bash
It 'matches email pattern'
  email="user@example.com"
  The variable email should match pattern '^[^@]+@[^@]+\.[^@]+$'
End

It 'matches semantic version'
  version="1.2.3"
  The variable version should match pattern '^[0-9]+\.[0-9]+\.[0-9]+$'
End
```

#### include

Substring matching:

```bash
The output should include "substring"
The output should not include "unwanted"
```

Examples:

```bash
It 'contains success message'
  When call echo "Operation completed successfully"
  The output should include "successfully"
End
```

#### start with

String prefix matching:

```bash
The output should start with "Prefix"
```

Example:

```bash
It 'starts with log level'
  When call echo "INFO: Process started"
  The output should start with "INFO:"
End
```

#### end with

String suffix matching:

```bash
The output should end with "suffix"
```

Example:

```bash
It 'ends with file extension'
  filename="document.pdf"
  The variable filename should end with ".pdf"
End
```

### Validation Matchers

#### be valid

Check if subject is valid (non-empty, non-zero):

```bash
The value x should be valid        # x is not empty/null
The value x should not be valid    # x is empty/null
```

#### be defined/undefined

Check if variable is defined:

```bash
The variable VAR should be defined
The variable UNSET should be undefined
```

#### be present/blank

Check for presence of content:

```bash
The output should be present   # Has content
The output should be blank     # Empty or whitespace only
```

### Predefined Value Matchers

#### be success/failure

Exit code matchers:

```bash
The status should be success    # Exit code 0
The status should be failure    # Exit code non-zero
```

#### be empty

File/output emptiness:

```bash
The file "path" should be empty
The output should be empty
```

#### be true/false

Boolean-style checks (for compatibility):

```bash
# Note: ShellSpec doesn't have native boolean type
# Use exit codes or variable checks instead
```

## Negation

Use `should not` to negate any matcher:

```bash
The output should not equal "wrong"
The output should not include "error"
The status should not be failure
The file "/tmp/file" should not be exist
```

## Multiple Assertions

Multiple assertions per example:

```bash
It 'validates output fully'
  When call echo "Success: Operation completed"
  The output should start with "Success:"
  The output should include "Operation"
  The output should end with "completed"
  The status should be success
End
```

## Line-Specific Assertions

Test specific lines of output:

```bash
It 'checks individual lines'
  list_files() {
    echo "file1.txt"
    echo "file2.txt"
    echo "file3.txt"
  }

  When call list_files
  The line 1 of output should equal "file1.txt"
  The line 2 of output should equal "file2.txt"
  The line 3 of output should equal "file3.txt"
End
```

## Advanced Assertion Patterns

### Testing JSON Output

```bash
It 'validates JSON structure'
  get_json() {
    echo '{"name":"Alice","age":30}'
  }

  When call get_json
  The output should match pattern '\{"name":"[^"]+","age":[0-9]+\}'
  The output should include '"name":"Alice"'
End
```

Better approach with jq (if available):

```bash
It 'validates JSON with jq'
  get_json() {
    echo '{"name":"Alice","age":30}'
  }

  When call get_json
  The output should be valid json

  # Extract and test specific fields
  name=$(get_json | jq -r '.name')
  The variable name should equal "Alice"
End
```

### Testing Multiline Output

```bash
It 'checks multiline output'
  generate_report() {
    cat << EOF
Report Title
============
Line 1: Status OK
Line 2: Count 42
EOF
  }

  When call generate_report
  The line 1 of output should equal "Report Title"
  The line 3 of output should include "Status OK"
  The lines of output should equal 4
End
```

### Testing CSV/Tabular Data

```bash
It 'validates CSV row'
  get_csv_row() {
    echo "Alice,30,Engineer"
  }

  When call get_csv_row
  The output should match pattern '^[^,]+,[0-9]+,[^,]+$'

  # Split and test fields
  IFS=',' read -r name age role <<< "$(get_csv_row)"
  The variable name should equal "Alice"
  The variable age should equal "30"
End
```

### Testing Error Messages

```bash
It 'shows helpful error'
  validate_input() {
    [[ -z "$1" ]] && {
      echo "Error: Argument required" >&2
      echo "Usage: command <argument>" >&2
      return 1
    }
  }

  When call validate_input ""
  The stderr should start with "Error:"
  The stderr should include "Argument required"
  The stderr should include "Usage:"
  The status should be failure
End
```

## Custom Assertion Messages

Add descriptive context to assertions:

```bash
It 'validates with custom message'
  result=42

  # Clear intent with variable name
  The variable result should equal 42

  # Even clearer with descriptive names
  expected_answer=42
  The variable result should equal "$expected_answer"
End
```

## Common Assertion Patterns

### Validate Command Output

```bash
The output should equal "expected"
The output should include "substring"
The output should match pattern "regex"
The output should be blank
The lines of output should equal 5
```

### Validate Exit Codes

```bash
The status should be success
The status should be failure
The status should equal 2
```

### Validate Files

```bash
The file "path" should be exist
The file "path" should be file
The file "path" should be readable
The contents of file "path" should equal "content"
```

### Validate Variables

```bash
The variable VAR should be defined
The variable VAR should equal "value"
The variable COUNT should be gt 0
```

## Troubleshooting Assertions

### Assertion Fails with "not equal"

**Check** for:
- Trailing newlines in output
- Leading/trailing whitespace
- Character encoding issues

**Solution**: Use `include` instead of `equal` for substring matching:

```bash
# Instead of:
The output should equal "text"

# Try:
The output should include "text"
```

### Regex Pattern Not Matching

**Remember**: ShellSpec uses POSIX ERE (Extended Regular Expression):

```bash
# Good
The output should match pattern '^[0-9]+$'

# Bad (using PCRE syntax)
The output should match pattern '^\d+$'
```

### Status Assertion Fails

**Check** that command is being called correctly:

```bash
# Correct
When call my_function

# Incorrect - runs in subshell, status not captured
When run my_function
```

## Next Steps

- Read `03-test-structure.md` for organizing assertions
- Read `08-common-patterns.md` for assertion patterns
- Check `assets/basic_spec_example.sh` for examples
