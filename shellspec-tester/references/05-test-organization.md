# Test Organization and Project Structure

Guide to organizing ShellSpec tests for maintainable and scalable test suites.

## Directory Structure Patterns

### Pattern 1: Mirror Source Structure

Recommended for most projects - spec files mirror source structure:

```
project/
├── scripts/
│   ├── backup.sh
│   ├── deploy.sh
│   └── lib/
│       ├── database.sh
│       └── utils.sh
├── spec/
│   ├── spec_helper.sh
│   ├── backup_spec.sh
│   ├── deploy_spec.sh
│   └── lib/
│       ├── database_spec.sh
│       └── utils_spec.sh
└── .shellspec
```

### Pattern 2: Flat Spec Directory

Simple for small projects:

```
project/
├── scripts/
│   ├── script1.sh
│   ├── script2.sh
│   └── script3.sh
├── spec/
│   ├── spec_helper.sh
│   ├── script1_spec.sh
│   ├── script2_spec.sh
│   └── script3_spec.sh
└── .shellspec
```

### Pattern 3: Test Categories

Group by test type:

```
project/
├── scripts/
│   └── app.sh
├── spec/
│   ├── spec_helper.sh
│   ├── unit/
│   │   ├── functions_spec.sh
│   │   └── utils_spec.sh
│   ├── integration/
│   │   ├── workflow_spec.sh
│   │   └── pipeline_spec.sh
│   └── e2e/
│       └── complete_flow_spec.sh
└── .shellspec
```

Configure multiple spec directories:

```bash
# .shellspec
--spec-dir spec/unit
--spec-dir spec/integration
--spec-dir spec/e2e
```

### Pattern 4: Feature-Based

Organize by features:

```
project/
├── scripts/
├── spec/
│   ├── spec_helper.sh
│   ├── authentication/
│   │   ├── login_spec.sh
│   │   ├── logout_spec.sh
│   │   └── password_reset_spec.sh
│   ├── user_management/
│   │   ├── create_user_spec.sh
│   │   └── delete_user_spec.sh
│   └── reporting/
│       └── generate_report_spec.sh
└── .shellspec
```

## spec_helper.sh Organization

### Basic spec_helper.sh

```bash
# spec/spec_helper.sh

# Project root
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# Add scripts to PATH
SCRIPT_DIR="${PROJECT_ROOT}/scripts"
export PATH="${SCRIPT_DIR}:${PATH}"

# Load all script files
for script in "${SCRIPT_DIR}"/*.sh; do
  source "${script}"
done
```

### Advanced spec_helper.sh

```bash
# spec/spec_helper.sh

#==============================================================================
# Environment Setup
#==============================================================================

# Strict mode
set -euo pipefail

# Project paths
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SCRIPT_DIR="${PROJECT_ROOT}/scripts"
SPEC_DIR="${PROJECT_ROOT}/spec"
FIXTURES_DIR="${SPEC_DIR}/fixtures"

export PROJECT_ROOT SCRIPT_DIR SPEC_DIR FIXTURES_DIR

# Add scripts to PATH
export PATH="${SCRIPT_DIR}:${SCRIPT_DIR}/lib:${PATH}"

#==============================================================================
# Load Application Code
#==============================================================================

# Source library functions
source "${SCRIPT_DIR}/lib/database.sh"
source "${SCRIPT_DIR}/lib/utils.sh"

# Source main scripts
source "${SCRIPT_DIR}/backup.sh"
source "${SCRIPT_DIR}/deploy.sh"

#==============================================================================
# Test Helpers
#==============================================================================

# Create temporary directory for tests
setup_test_temp() {
  TEST_TEMP_DIR=$(mktemp -d)
  export TEST_TEMP_DIR
}

# Clean up temporary directory
cleanup_test_temp() {
  if [[ -n "${TEST_TEMP_DIR:-}" && -d "${TEST_TEMP_DIR}" ]]; then
    rm -rf "${TEST_TEMP_DIR}"
  fi
}

# Create test file with content
create_test_file() {
  local filename="$1"
  local content="$2"
  echo "${content}" > "${TEST_TEMP_DIR}/${filename}"
}

# Assert file contains expected content
assert_file_contains() {
  local filename="$1"
  local expected="$2"
  grep -q "${expected}" "${TEST_TEMP_DIR}/${filename}"
}

#==============================================================================
# Test Fixtures
#==============================================================================

# Load fixture file
load_fixture() {
  local fixture_name="$1"
  cat "${FIXTURES_DIR}/${fixture_name}"
}

# Copy fixture to temp directory
copy_fixture() {
  local fixture_name="$1"
  local dest="${TEST_TEMP_DIR}/${2:-${fixture_name}}"
  cp "${FIXTURES_DIR}/${fixture_name}" "${dest}"
}

#==============================================================================
# Mock Helpers
#==============================================================================

# Track mock calls
MOCK_CALLS=()

# Reset mock state
reset_mocks() {
  MOCK_CALLS=()
}

# Record mock call
record_mock_call() {
  local func_name="$1"
  shift
  MOCK_CALLS+=("${func_name} $*")
}

# Verify mock was called
assert_mock_called() {
  local expected="$1"
  local found=false

  for call in "${MOCK_CALLS[@]}"; do
    if [[ "${call}" == "${expected}" ]]; then
      found=true
      break
    fi
  done

  ${found}
}

#==============================================================================
# Configuration for Tests
#==============================================================================

# Override config values for testing
export APP_ENV=test
export LOG_LEVEL=error
export DATABASE_URL=sqlite::memory:

# Disable interactive prompts
export NONINTERACTIVE=1
```

## Supporting Files Organization

### Fixtures Directory

Store test data files:

```
spec/
├── fixtures/
│   ├── sample_config.yml
│   ├── test_data.json
│   ├── mock_api_response.xml
│   └── users.csv
└── spec_helper.sh
```

Usage in tests:

```bash
It 'processes config file'
  config=$(load_fixture "sample_config.yml")
  When call process_config "${config}"
  The status should be success
End
```

### Support Directory

Shared test utilities:

```
spec/
├── support/
│   ├── spec_helper.sh        # Main helper
│   ├── custom_matchers.sh    # Custom assertions
│   ├── database_helpers.sh   # DB test utilities
│   └── mock_helpers.sh       # Mocking utilities
├── fixtures/
└── *_spec.sh
```

Load in .shellspec:

```bash
--require spec_helper
--require support/custom_matchers
--require support/database_helpers
```

## Shared Examples

### Define Shared Examples

Create reusable test patterns:

```bash
# spec/support/shared_examples.sh

# Shared: standard validation behavior
shared_validates_input() {
  local func="$1"

  It 'rejects empty input'
    When call "${func}" ""
    The status should be failure
    The stderr should include "Error"
  End

  It 'accepts valid input'
    When call "${func}" "valid_input"
    The status should be success
  End
}

# Shared: file creation behavior
shared_creates_file() {
  local func="$1"
  local expected_file="$2"

  It 'creates expected file'
    When call "${func}"
    The file "${expected_file}" should be exist
  End

  It 'creates non-empty file'
    When call "${func}"
    The file "${expected_file}" should not be empty
  End
}
```

### Use Shared Examples

```bash
# spec/validation_spec.sh

Describe 'username validation'
  Include shared_validates_input validate_username
End

Describe 'password validation'
  Include shared_validates_input validate_password
End

Describe 'email validation'
  Include shared_validates_input validate_email
End
```

## Custom Matchers

### Define Custom Matchers

```bash
# spec/support/custom_matchers.sh

# Custom matcher: valid JSON
%const JSON_PATTERN: '^[\[\{].*[\]\}]$'

be_valid_json() {
  local actual="$1"

  # Try to parse with jq
  if echo "${actual}" | jq . >/dev/null 2>&1; then
    return 0
  else
    return 1
  fi
}

# Custom matcher: valid email
be_valid_email() {
  local email="$1"
  [[ "${email}" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]
}

# Custom matcher: ISO 8601 date
be_iso8601_date() {
  local date="$1"
  [[ "${date}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z?$ ]]
}
```

### Use Custom Matchers

```bash
It 'returns valid JSON'
  When call get_user_data
  The output should be_valid_json
End

It 'validates email format'
  email="user@example.com"
  The variable email should be_valid_email
End

It 'generates ISO 8601 timestamp'
  timestamp=$(generate_timestamp)
  The variable timestamp should be_iso8601_date
End
```

## Test Data Management

### Inline Test Data

```bash
It 'processes CSV data'
  data=$(cat <<'EOF'
name,age,city
Alice,30,London
Bob,25,Paris
EOF
  )

  When call process_csv "${data}"
  The output should include "Alice"
End
```

### Fixture Files

```bash
# spec/fixtures/users.csv
name,age,city
Alice,30,London
Bob,25,Paris
Charlie,35,Berlin

# spec/users_spec.sh
It 'processes user data'
  When call process_csv "$(load_fixture users.csv)"
  The line 1 of output should include "Alice"
End
```

### Generated Test Data

```bash
# spec/support/test_data_generators.sh

generate_random_user() {
  local id=$((RANDOM % 1000))
  echo "user_${id},${id}@test.com"
}

generate_test_database() {
  local temp_db="${TEST_TEMP_DIR}/test.db"
  sqlite3 "${temp_db}" <<EOF
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
INSERT INTO users (name) VALUES ('Alice'), ('Bob');
EOF
  echo "${temp_db}"
}
```

## Running Subsets of Tests

### By File Pattern

```bash
# Run all unit tests
shellspec spec/unit/

# Run specific test file
shellspec spec/backup_spec.sh

# Run multiple files
shellspec spec/backup_spec.sh spec/deploy_spec.sh
```

### By Example Pattern

```bash
# Run tests matching "backup"
shellspec --example "backup"

# Run tests matching "error handling"
shellspec --example "error handling"
```

### By Tag

```bash
# spec/backup_spec.sh
Describe 'backup' :slow
  It 'creates full backup'
    # slow test
  End
End

Describe 'backup' :fast
  It 'validates config'
    # fast test
  End
End

# Run only fast tests
shellspec --tag fast

# Run slow tests
shellspec --tag slow

# Skip slow tests
shellspec --tag ~slow
```

## Parallel Test Execution

### Configure Parallel Jobs

```bash
# .shellspec
--jobs 4
```

Or via command line:

```bash
shellspec --jobs 4
```

### Ensure Test Independence

Tests must not depend on execution order:

```bash
# Bad - depends on other tests
It 'creates user'
  create_user "alice"
End

It 'deletes user'
  delete_user "alice"  # Depends on previous test!
End

# Good - independent tests
It 'creates user'
  create_user "alice"
  cleanup_user "alice"
End

It 'deletes user'
  create_user "bob"
  delete_user "bob"
  # Verify deletion
End
```

### Use BeforeEach/AfterEach

```bash
Describe 'database operations'
  BeforeEach 'setup_clean_database'
  AfterEach 'teardown_database'

  It 'test 1'
    # Fresh database
  End

  It 'test 2'
    # Fresh database (independent from test 1)
  End
End
```

## Large Test Suite Organization

### Example Project Structure

```
project/
├── scripts/
│   ├── bin/
│   │   ├── backup
│   │   └── deploy
│   └── lib/
│       ├── core/
│       │   ├── config.sh
│       │   └── logging.sh
│       ├── backup/
│       │   ├── local.sh
│       │   └── remote.sh
│       └── deploy/
│           ├── docker.sh
│           └── kubernetes.sh
├── spec/
│   ├── support/
│   │   ├── spec_helper.sh
│   │   ├── shared_examples.sh
│   │   ├── custom_matchers.sh
│   │   └── test_data_generators.sh
│   ├── fixtures/
│   │   ├── configs/
│   │   ├── data/
│   │   └── mocks/
│   ├── unit/
│   │   ├── core/
│   │   │   ├── config_spec.sh
│   │   │   └── logging_spec.sh
│   │   ├── backup/
│   │   │   ├── local_spec.sh
│   │   │   └── remote_spec.sh
│   │   └── deploy/
│   │       ├── docker_spec.sh
│   │       └── kubernetes_spec.sh
│   ├── integration/
│   │   ├── backup_workflow_spec.sh
│   │   └── deploy_workflow_spec.sh
│   └── e2e/
│       └── full_pipeline_spec.sh
├── .shellspec
└── README.md
```

### Multi-Level spec_helper Pattern

```bash
# spec/support/spec_helper.sh (main)
source "${SPEC_DIR}/support/custom_matchers.sh"
source "${SPEC_DIR}/support/shared_examples.sh"

# spec/unit/spec_helper.sh (unit-specific)
source "${SPEC_DIR}/support/spec_helper.sh"
# Unit-specific setup

# spec/integration/spec_helper.sh (integration-specific)
source "${SPEC_DIR}/support/spec_helper.sh"
# Integration-specific setup (e.g., database)
```

## Best Practices

1. **Mirror source structure** - Easy to find related tests
2. **Use spec_helper.sh** - Centralize common setup
3. **Keep fixtures organized** - Separate directory for test data
4. **Create shared examples** - DRY principle for tests
5. **Tag tests appropriately** - Enable selective runs (:slow, :integration)
6. **Ensure test independence** - Tests should not depend on each other
7. **Use descriptive names** - Clear file and test names
8. **Document organization** - README explaining structure

## Next Steps

- Read `06-tdd-workflow.md` for development workflow
- Read `08-common-patterns.md` for testing patterns
- Read `09-ci-integration.md` for automated testing
