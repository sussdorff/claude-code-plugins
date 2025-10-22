# ShellSpec Test Structure

Complete guide to organizing tests with describe blocks, hooks, and test lifecycle.

## Basic Test Structure

### Describe Blocks

Group related tests together:

```bash
Describe 'function_name'
  It 'does something'
    # Test code
  End

  It 'handles errors'
    # Test code
  End
End
```

Example:

```bash
Describe 'backup_database'
  backup_database() {
    echo "Backing up database..."
    return 0
  }

  It 'outputs status message'
    When call backup_database
    The output should include "Backing up"
  End

  It 'succeeds'
    When call backup_database
    The status should be success
  End
End
```

### It Blocks (Examples)

Individual test cases:

```bash
It 'describes what it tests'
  # Arrange
  input="test"

  # Act
  When call process_input "${input}"

  # Assert
  The output should equal "processed: test"
End
```

Alternative keywords (aliases):
- `Specify` - alias for `It`
- `Example` - alias for `It`

```bash
Specify 'same as It'
  # Test code
End

Example 'also same as It'
  # Test code
End
```

## Nested Structure

### Context Blocks

Create sub-groups within describe blocks:

```bash
Describe 'user_authentication'
  Context 'with valid credentials'
    It 'allows login'
      # Test code
    End

    It 'returns success'
      # Test code
    End
  End

  Context 'with invalid credentials'
    It 'denies login'
      # Test code
    End

    It 'returns error'
      # Test code
    End
  End
End
```

`Context` is an alias for `Describe` - use whichever reads better.

### Deeply Nested Structure

```bash
Describe 'payment processing'
  Context 'credit card payments'
    Context 'with valid card'
      It 'processes successfully'
      End

      It 'sends confirmation email'
      End
    End

    Context 'with expired card'
      It 'rejects payment'
      End

      It 'shows error message'
      End
    End
  End

  Context 'PayPal payments'
    It 'redirects to PayPal'
    End
  End
End
```

## Setup and Teardown Hooks

### BeforeEach / AfterEach

Run code before/after each test:

```bash
Describe 'file operations'
  setup() {
    TEST_FILE=$(mktemp)
  }

  cleanup() {
    rm -f "${TEST_FILE}"
  }

  BeforeEach 'setup'
  AfterEach 'cleanup'

  It 'creates file'
    When call touch "${TEST_FILE}"
    The file "${TEST_FILE}" should be exist
  End

  It 'writes to file'
    When call echo "content" > "${TEST_FILE}"
    The contents of file "${TEST_FILE}" should equal "content"
  End
End
```

### BeforeAll / AfterAll

Run once before/after all tests in a block:

```bash
Describe 'database tests'
  setup_database() {
    echo "Creating test database..."
    createdb test_db
  }

  teardown_database() {
    echo "Dropping test database..."
    dropdb test_db
  }

  BeforeAll 'setup_database'
  AfterAll 'teardown_database'

  It 'connects to database'
    # Test with test_db
  End

  It 'queries database'
    # Test with test_db
  End
End
```

### Before / After

General hooks (same as BeforeEach/AfterEach):

```bash
Before 'setup'    # Same as BeforeEach
After 'cleanup'   # Same as AfterEach
```

### Hook Execution Order

```bash
Describe 'hook order'
  BeforeAll 'global_setup'    # 1. Runs once before all
  BeforeEach 'test_setup'     # 2. Runs before each test
  AfterEach 'test_cleanup'    # 3. Runs after each test
  AfterAll 'global_cleanup'   # 4. Runs once after all

  It 'test 1'                 # 2 → test → 3
  End

  It 'test 2'                 # 2 → test → 3
  End
End

# Execution:
# 1. global_setup
# 2. test_setup → test 1 → test_cleanup
# 2. test_setup → test 2 → test_cleanup
# 4. global_cleanup
```

## Test Control Flow

### Pending Tests

Mark tests as TODO (not yet implemented):

```bash
It 'will be implemented later'
  Pending "Need to implement feature X first"
End
```

Output:
```
* will be implemented later (PENDING: Need to implement feature X first)
```

### Skipped Tests

Temporarily disable tests:

```bash
It 'is temporarily disabled'
  Skip "Skipping until bug #123 is fixed"
End
```

Alternative syntax:

```bash
It 'is temporarily disabled'
  Skip if "command not available" ! command -v required_cmd &>/dev/null
  # Test code only runs if condition is false
End
```

### Skip Entire Blocks

```bash
Describe 'experimental feature'
  Skip "Feature not ready for testing"

  It 'test 1'
    # Won't run
  End

  It 'test 2'
    # Won't run
  End
End
```

### Conditional Skip

Skip based on condition:

```bash
Describe 'macOS-specific tests'
  Skip if "Not on macOS" ! [[ "$(uname)" == "Darwin" ]]

  It 'uses macOS command'
    When call sw_vers
    The status should be success
  End
End
```

### Focus on Specific Tests

Run only specific tests (for development):

```bash
Describe 'my tests'
  fit 'focused test'  # Only this runs
    # Test code
  End

  It 'skipped test'   # This is skipped
    # Test code
  End
End
```

Or focus on entire describe block:

```bash
fdescribe 'focused block'  # Only this block runs
  It 'test 1'
  End

  It 'test 2'
  End
End

Describe 'skipped block'   # This block is skipped
  It 'test 3'
  End
End
```

**Warning**: Remove `fit`/`fdescribe` before committing - they're for local development only.

## When Blocks (Call/Run)

### When call

Execute function in current shell:

```bash
It 'calls function'
  my_function() {
    echo "output"
    return 0
  }

  When call my_function "arg1" "arg2"
  The output should equal "output"
  The status should be success
End
```

### When run

Execute in subshell (isolated environment):

```bash
It 'runs command'
  When run bash -c 'echo "test"'
  The output should equal "test"
End
```

Use `run` for:
- Testing commands (not functions)
- Isolating side effects
- Testing scripts as executables

### Difference: call vs run

```bash
# call - function runs in current shell
When call my_function
# - Can access current variables
# - Changes to variables persist
# - Faster

# run - command runs in subshell
When run my_command
# - Isolated environment
# - Changes don't persist
# - Slower but safer
```

## Parameterized Tests

### Using Parameters

Run same test with different inputs:

```bash
Describe 'validation'
  validate_email() {
    [[ "$1" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]
  }

  Parameters
    "valid@example.com"     success
    "also.valid@test.com"   success
    "invalid.email"         failure
    "@no-local.com"         failure
  End

  Example "email $1 should be $2"
    When call validate_email "$1"
    The status should be "$2"
  End
End
```

Output:
```
email valid@example.com should be success
email also.valid@test.com should be success
email invalid.email should be failure
email @no-local.com should be failure
```

### Parameters with Multiple Values

```bash
Parameters
  "input1"  "arg2"  "expected_output"
  "input2"  "arg2"  "another_output"
End

Example "testing $1 with $2"
  When call my_function "$1" "$2"
  The output should equal "$3"
End
```

### Matrix Parameters

```bash
Parameters:matrix
  alice bob charlie
  admin user guest
End

# Generates all combinations:
# alice admin
# alice user
# alice guest
# bob admin
# bob user
# ...
```

## Shared Examples

Reuse test logic across different contexts:

```bash
# Define shared examples
has_standard_validation() {
  It 'rejects empty input'
    When call "$1" ""
    The status should be failure
  End

  It 'accepts valid input'
    When call "$1" "valid"
    The status should be success
  End
}

# Use shared examples
Describe 'username validation'
  Include has_standard_validation validate_username
End

Describe 'password validation'
  Include has_standard_validation validate_password
End
```

## Test File Organization

### Single Spec File

```bash
# user_spec.sh

Describe 'user management'
  Describe 'create_user'
    It 'creates user successfully'
    End
  End

  Describe 'delete_user'
    It 'deletes user successfully'
    End
  End
End
```

### Multiple Describe Blocks per File

```bash
# utils_spec.sh

Describe 'string_utils'
  It 'trims whitespace'
  End
End

Describe 'array_utils'
  It 'joins array elements'
  End
End

Describe 'math_utils'
  It 'calculates sum'
  End
End
```

### Spec File Naming

**Convention**: `<name>_spec.sh`

```bash
# Good
backup_spec.sh
user_management_spec.sh
utils_spec.sh

# Bad - won't be auto-discovered
test_backup.sh
backup.test.sh
backup_test.sh
```

## Best Practices

### 1. Use Descriptive Names

```bash
# Good - describes behavior
It 'returns error when file does not exist'
It 'creates backup with timestamp in filename'

# Bad - vague
It 'works correctly'
It 'test case 1'
```

### 2. One Assertion per Example (when possible)

```bash
# Good - focused
It 'outputs success message'
  When call backup_database
  The output should include "Success"
End

It 'returns success code'
  When call backup_database
  The status should be success
End

# Acceptable - related assertions
It 'validates output fully'
  When call backup_database
  The output should start with "Backup:"
  The output should include "database"
  The status should be success
End
```

### 3. Use Contexts for Different Scenarios

```bash
Describe 'process_file'
  Context 'when file exists'
    It 'processes successfully'
    End
  End

  Context 'when file is missing'
    It 'returns error'
    End
  End

  Context 'when file is not readable'
    It 'shows permission error'
    End
  End
End
```

### 4. Group Related Tests

```bash
Describe 'authentication module'
  Describe 'login'
    It 'accepts valid credentials'
    End
  End

  Describe 'logout'
    It 'clears session'
    End
  End

  Describe 'password_reset'
    It 'sends reset email'
    End
  End
End
```

### 5. Use Hooks for Common Setup

```bash
Describe 'database operations'
  # DRY - Don't Repeat Yourself
  BeforeEach 'create_test_database'
  AfterEach 'cleanup_test_database'

  It 'test 1'
    # Database ready
  End

  It 'test 2'
    # Database ready
  End
End
```

## Complete Example

```bash
Describe 'backup system'
  # Setup
  setup() {
    BACKUP_DIR=$(mktemp -d)
    export BACKUP_DIR
  }

  cleanup() {
    rm -rf "${BACKUP_DIR}"
  }

  BeforeEach 'setup'
  AfterEach 'cleanup'

  # Function to test
  create_backup() {
    local source="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/backup_${timestamp}.tar.gz"

    if [[ ! -d "${source}" ]]; then
      echo "Error: Source directory not found" >&2
      return 1
    fi

    tar -czf "${backup_file}" "${source}" 2>/dev/null
    echo "Backup created: ${backup_file}"
    return 0
  }

  Context 'with valid source directory'
    It 'creates backup file'
      mkdir -p /tmp/test_source
      When call create_backup /tmp/test_source
      The output should include "Backup created:"
      The status should be success
    End

    It 'backup file exists'
      mkdir -p /tmp/test_source
      create_backup /tmp/test_source > /dev/null
      The file "${BACKUP_DIR}"/backup_*.tar.gz should be exist
    End
  End

  Context 'with missing source directory'
    It 'returns error'
      When call create_backup /nonexistent
      The stderr should include "Source directory not found"
      The status should be failure
    End
  End
End
```

## Next Steps

- Read `02-assertions.md` for assertion types
- Read `04-mocking-and-stubbing.md` for isolation
- Read `05-test-organization.md` for larger projects
- Check `assets/basic_spec_example.sh` for structure examples
