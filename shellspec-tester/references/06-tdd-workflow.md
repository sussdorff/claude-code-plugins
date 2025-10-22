# Test-Driven Development (TDD) Workflow with ShellSpec

Complete guide to practicing TDD when developing Bash scripts with ShellSpec.

## TDD Fundamentals

### The TDD Cycle: Red-Green-Refactor

```
┌─────────────┐
│    RED      │  Write failing test first
│  (Test)     │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│   GREEN     │  Write minimal code to pass
│  (Code)     │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│  REFACTOR   │  Improve code while keeping tests green
│  (Improve)  │
└─────┬───────┘
      │
      └──────► Repeat
```

### TDD Principles

1. **Write tests first** - Before any production code
2. **Write minimal code** - Just enough to pass the test
3. **Refactor with confidence** - Tests protect against regression
4. **One test at a time** - Focus on one behavior
5. **Keep tests fast** - Quick feedback loop

## RED: Write Failing Test First

### Step 1: Describe the Behavior

Start with what the function should do:

```bash
# spec/backup_spec.sh

Describe 'create_backup'
  It 'creates backup file with timestamp'
    When call create_backup "/data"
    The output should include "Backup created:"
    The status should be success
  End
End
```

### Step 2: Run Test (Should Fail)

```bash
shellspec spec/backup_spec.sh
```

Expected output:

```
create_backup
  creates backup file with timestamp (FAILED - 1)

Failures:

  1) create_backup creates backup file with timestamp
     When call create_backup

     1.1) The function "create_backup" is not defined

Finished in 0.02 seconds
1 example, 1 failure
```

**This failure is good!** It confirms:
- Test is running
- Function doesn't exist yet
- We know what to implement next

### Step 3: Verify Test Logic

Before implementing, ensure test would pass with correct implementation:

```bash
# Temporary mock to verify test
create_backup() {
  echo "Backup created: /backups/backup_20240115.tar.gz"
  return 0
}

# Run test - should pass
shellspec spec/backup_spec.sh
```

If test passes with mock, remove mock and proceed to GREEN.

## GREEN: Make Test Pass

### Step 4: Write Minimal Implementation

Write simplest code to pass the test:

```bash
# scripts/backup.sh

create_backup() {
  local source="$1"
  echo "Backup created: /backups/backup_20240115.tar.gz"
  return 0
}
```

Yes, this is hardcoded and wrong - but it passes the test!

### Step 5: Run Test (Should Pass)

```bash
shellspec spec/backup_spec.sh
```

Output:

```
create_backup
  creates backup file with timestamp

Finished in 0.03 seconds
1 example, 0 failures
```

✅ **GREEN!** Test passes.

### Step 6: Add More Specific Tests

The current implementation is too simple. Add tests for edge cases:

```bash
Describe 'create_backup'
  setup() {
    BACKUP_DIR=$(mktemp -d)
    export BACKUP_DIR
  }

  cleanup() {
    rm -rf "${BACKUP_DIR}"
  }

  BeforeEach 'setup'
  AfterEach 'cleanup'

  It 'creates backup file with timestamp'
    When call create_backup "/data"
    The output should include "Backup created:"
    The status should be success
  End

  It 'creates actual backup file'
    create_backup "/data" >/dev/null
    The file "${BACKUP_DIR}"/backup_*.tar.gz should be exist
  End

  It 'returns error for missing directory'
    When call create_backup "/nonexistent"
    The stderr should include "Error"
    The status should be failure
  End
End
```

Run tests - some will fail. Good! Now implement properly:

```bash
# scripts/backup.sh

create_backup() {
  local source="$1"
  local timestamp=$(date +%Y%m%d_%H%M%S)
  local backup_file="${BACKUP_DIR}/backup_${timestamp}.tar.gz"

  if [[ ! -d "${source}" ]]; then
    echo "Error: Source directory not found: ${source}" >&2
    return 1
  fi

  tar -czf "${backup_file}" "${source}" 2>/dev/null || {
    echo "Error: Failed to create backup" >&2
    return 1
  }

  echo "Backup created: ${backup_file}"
  return 0
}
```

Run tests again:

```bash
shellspec spec/backup_spec.sh
```

All tests should pass now! ✅

## REFACTOR: Improve Code

### Step 7: Refactor While Green

Now that tests pass, improve the code:

```bash
# scripts/backup.sh

# Constants
readonly DEFAULT_BACKUP_DIR="/var/backups"

# Refactored with better error handling
create_backup() {
  local source="$1"
  local backup_dir="${BACKUP_DIR:-${DEFAULT_BACKUP_DIR}}"
  local timestamp
  timestamp=$(date +%Y%m%d_%H%M%S)
  local backup_file="${backup_dir}/backup_${timestamp}.tar.gz"

  # Validation
  validate_source_directory "${source}" || return $?

  # Create backup directory if needed
  ensure_backup_directory_exists "${backup_dir}" || return $?

  # Create backup
  create_tar_archive "${source}" "${backup_file}" || return $?

  # Report success
  report_success "${backup_file}"
}

validate_source_directory() {
  local source="$1"

  if [[ ! -d "${source}" ]]; then
    echo "Error: Source directory not found: ${source}" >&2
    return 1
  fi
}

ensure_backup_directory_exists() {
  local backup_dir="$1"

  if [[ ! -d "${backup_dir}" ]]; then
    mkdir -p "${backup_dir}" 2>/dev/null || {
      echo "Error: Cannot create backup directory: ${backup_dir}" >&2
      return 1
    }
  fi
}

create_tar_archive() {
  local source="$1"
  local output="$2"

  tar -czf "${output}" "${source}" 2>/dev/null || {
    echo "Error: Failed to create backup archive" >&2
    return 1
  }
}

report_success() {
  local backup_file="$1"
  echo "Backup created: ${backup_file}"
}
```

### Step 8: Run Tests After Refactoring

```bash
shellspec spec/backup_spec.sh
```

All tests should still pass! ✅

If any test fails, revert changes and try again.

## Practical TDD Example: Complete Feature

### Feature: User Input Validation

**Requirement**: Validate email addresses

#### Iteration 1: Basic Validation

**RED**: Write first test

```bash
# spec/validation_spec.sh

Describe 'validate_email'
  It 'accepts valid email'
    When call validate_email "user@example.com"
    The status should be success
  End
End
```

Run: ❌ Fails (function doesn't exist)

**GREEN**: Minimal implementation

```bash
# scripts/validation.sh

validate_email() {
  return 0  # Always succeeds
}
```

Run: ✅ Passes

#### Iteration 2: Reject Invalid Emails

**RED**: Add failing test

```bash
It 'rejects email without @'
  When call validate_email "invalid.email"
  The status should be failure
End
```

Run: ❌ Fails (function always returns success)

**GREEN**: Implement basic validation

```bash
validate_email() {
  local email="$1"

  if [[ "${email}" == *@* ]]; then
    return 0
  else
    return 1
  fi
}
```

Run: ✅ Both tests pass

#### Iteration 3: Stricter Validation

**RED**: Add more tests

```bash
It 'rejects email without domain'
  When call validate_email "user@"
  The status should be failure
End

It 'rejects email without local part'
  When call validate_email "@example.com"
  The status should be failure
End

It 'accepts email with subdomain'
  When call validate_email "user@mail.example.com"
  The status should be success
End
```

Run: ❌ Some fail

**GREEN**: Improve implementation

```bash
validate_email() {
  local email="$1"

  # Must match: local@domain.tld
  if [[ "${email}" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    return 0
  else
    return 1
  fi
}
```

Run: ✅ All tests pass

**REFACTOR**: Add helpful error messages

```bash
validate_email() {
  local email="$1"

  if [[ -z "${email}" ]]; then
    echo "Error: Email address cannot be empty" >&2
    return 1
  fi

  if [[ ! "${email}" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    echo "Error: Invalid email format: ${email}" >&2
    return 1
  fi

  return 0
}
```

Update tests to check error messages:

```bash
It 'shows helpful error for invalid format'
  When call validate_email "invalid.email"
  The stderr should include "Invalid email format"
  The status should be failure
End
```

Run: ✅ All tests still pass

## TDD Best Practices

### 1. Test Behavior, Not Implementation

```bash
# Bad - tests implementation details
It 'uses regex pattern for validation'
  # This test is too coupled to implementation
End

# Good - tests behavior
It 'accepts valid email addresses'
  When call validate_email "user@example.com"
  The status should be success
End
```

### 2. Write One Failing Test at a Time

```bash
# Bad - too many failing tests
It 'test 1'
End
It 'test 2'
End
It 'test 3'
End
# All fail - overwhelming

# Good - one at a time
It 'test 1'
End
# Make this pass first, then add test 2
```

### 3. Keep Tests Fast

```bash
# Bad - slow test
It 'processes large file'
  # Creates 1GB file
  # Takes 30 seconds
End

# Good - fast test with small data
It 'processes file correctly'
  # Uses 1KB test file
  # Takes 0.1 seconds
End
```

### 4. Test Edge Cases

```bash
Describe 'divide'
  It 'divides positive numbers'
    # Normal case
  End

  It 'handles division by zero'
    # Edge case
  End

  It 'handles negative numbers'
    # Edge case
  End

  It 'handles zero dividend'
    # Edge case
  End
End
```

### 5. Use Descriptive Test Names

```bash
# Bad
It 'test1'
End

# Good
It 'returns error when input file does not exist'
End
```

## TDD Anti-Patterns to Avoid

### 1. Writing Tests After Code

```bash
# Anti-pattern: "Test-After Development"
# 1. Write function
# 2. Then write tests

# Correct: Test-Driven Development
# 1. Write test
# 2. Then write function
```

### 2. Making Tests Pass by Changing Tests

```bash
# Anti-pattern
It 'should return "hello"'
  When call my_function
  The output should equal "goodbye"  # Changed test to match wrong output!
End

# Correct: Fix implementation, not tests
```

### 3. Testing Too Much in One Test

```bash
# Anti-pattern
It 'does everything'
  # Tests 10 different behaviors
  # Hard to debug when it fails
End

# Correct: One test per behavior
```

### 4. Skipping Refactor Step

```bash
# Anti-pattern: Leave code messy after making tests pass
# Never refactor → technical debt accumulates

# Correct: Always refactor when tests are green
```

## TDD Workflow Cheat Sheet

```bash
# 1. RED - Write failing test
$ shellspec spec/new_feature_spec.sh
# Expected: 1 example, 1 failure

# 2. GREEN - Make it pass (minimal code)
$ shellspec spec/new_feature_spec.sh
# Expected: 1 example, 0 failures

# 3. REFACTOR - Improve code
$ shellspec spec/new_feature_spec.sh
# Expected: Still 0 failures

# 4. Repeat for next behavior
```

## Practicing TDD

### Kata: FizzBuzz

Practice TDD with classic FizzBuzz:

```bash
# spec/fizzbuzz_spec.sh

Describe 'fizzbuzz'
  # Test 1: Numbers not divisible by 3 or 5
  It 'returns number for 1'
    When call fizzbuzz 1
    The output should equal "1"
  End

  # Implement, make pass

  # Test 2: Divisible by 3
  It 'returns "Fizz" for 3'
    When call fizzbuzz 3
    The output should equal "Fizz"
  End

  # Implement, make pass

  # Test 3: Divisible by 5
  It 'returns "Buzz" for 5'
    When call fizzbuzz 5
    The output should equal "Buzz"
  End

  # Implement, make pass

  # Test 4: Divisible by both
  It 'returns "FizzBuzz" for 15'
    When call fizzbuzz 15
    The output should equal "FizzBuzz"
  End

  # Implement, make pass
End
```

Work through this step-by-step, following RED-GREEN-REFACTOR.

## Benefits of TDD

1. **Better design** - Forces you to think about interface first
2. **Confidence** - Tests protect against regressions
3. **Documentation** - Tests document expected behavior
4. **Faster debugging** - Failing test points to exact issue
5. **Less debugging time** - Catch bugs early
6. **Refactor safely** - Tests enable fearless refactoring

## Next Steps

- Read `07-coverage.md` for ensuring test completeness
- Read `08-common-patterns.md` for testing patterns
- Practice with kata exercises
- Apply TDD to your next feature
