# Common Testing Patterns with ShellSpec

Collection of proven patterns for testing Bash scripts effectively.

## Testing Functions with Parameters

### Single Parameter

```bash
Describe 'greet'
  greet() {
    echo "Hello, $1!"
  }

  It 'greets with provided name'
    When call greet "Alice"
    The output should equal "Hello, Alice!"
  End

  It 'handles empty parameter'
    When call greet ""
    The output should equal "Hello, !"
  End
End
```

### Multiple Parameters

```bash
Describe 'add'
  add() {
    echo $(( $1 + $2 ))
  }

  It 'adds two numbers'
    When call add 5 3
    The output should equal "8"
  End

  It 'handles negative numbers'
    When call add -5 3
    The output should equal "-2"
  End

  It 'handles zero'
    When call add 0 0
    The output should equal "0"
  End
End
```

### Variable Number of Parameters

```bash
Describe 'sum_all'
  sum_all() {
    local total=0
    for num in "$@"; do
      ((total += num))
    done
    echo "${total}"
  }

  It 'sums multiple numbers'
    When call sum_all 1 2 3 4 5
    The output should equal "15"
  End

  It 'handles single number'
    When call sum_all 42
    The output should equal "42"
  End

  It 'returns zero for no arguments'
    When call sum_all
    The output should equal "0"
  End
End
```

## Testing Error Conditions

### Error Detection

```bash
Describe 'validate_file'
  validate_file() {
    local file="$1"

    if [[ ! -f "${file}" ]]; then
      echo "Error: File not found: ${file}" >&2
      return 1
    fi

    if [[ ! -r "${file}" ]]; then
      echo "Error: File not readable: ${file}" >&2
      return 2
    fi

    echo "File is valid"
    return 0
  }

  Context 'with valid file'
    setup() {
      TEST_FILE=$(mktemp)
    }

    cleanup() {
      rm -f "${TEST_FILE}"
    }

    BeforeEach 'setup'
    AfterEach 'cleanup'

    It 'validates successfully'
      When call validate_file "${TEST_FILE}"
      The output should equal "File is valid"
      The status should be success
    End
  End

  Context 'with missing file'
    It 'returns error code 1'
      When call validate_file "/nonexistent"
      The stderr should include "File not found"
      The status should equal 1
    End
  End

  Context 'with unreadable file'
    setup() {
      TEST_FILE=$(mktemp)
      chmod -r "${TEST_FILE}"
    }

    cleanup() {
      rm -f "${TEST_FILE}"
    }

    BeforeEach 'setup'
    AfterEach 'cleanup'

    It 'returns error code 2'
      When call validate_file "${TEST_FILE}"
      The stderr should include "File not readable"
      The status should equal 2
    End
  End
End
```

### Exception Handling

```bash
Describe 'safe_division'
  safe_division() {
    local numerator="$1"
    local denominator="$2"

    if (( denominator == 0 )); then
      echo "Error: Division by zero" >&2
      return 1
    fi

    echo $(( numerator / denominator ))
  }

  It 'divides normally'
    When call safe_division 10 2
    The output should equal "5"
  End

  It 'handles division by zero'
    When call safe_division 10 0
    The stderr should include "Division by zero"
    The status should be failure
  End
End
```

## Testing File Operations

### File Creation

```bash
Describe 'create_config'
  create_config() {
    local config_file="$1"

    cat > "${config_file}" <<EOF
# Configuration
API_KEY=secret
DEBUG=true
EOF
  }

  setup() {
    TEST_DIR=$(mktemp -d)
    CONFIG_FILE="${TEST_DIR}/config.txt"
  }

  cleanup() {
    rm -rf "${TEST_DIR}"
  }

  BeforeEach 'setup'
  AfterEach 'cleanup'

  It 'creates config file'
    When call create_config "${CONFIG_FILE}"
    The file "${CONFIG_FILE}" should be exist
  End

  It 'contains expected content'
    create_config "${CONFIG_FILE}"
    The contents of file "${CONFIG_FILE}" should include "API_KEY=secret"
  End

  It 'creates valid configuration'
    create_config "${CONFIG_FILE}"
    The contents of file "${CONFIG_FILE}" should include "DEBUG=true"
  End
End
```

### File Reading

```bash
Describe 'read_config'
  read_config() {
    local config_file="$1"
    local key="$2"

    if [[ ! -f "${config_file}" ]]; then
      return 1
    fi

    grep "^${key}=" "${config_file}" | cut -d= -f2
  }

  setup() {
    TEST_FILE=$(mktemp)
    cat > "${TEST_FILE}" <<EOF
API_KEY=secret123
DEBUG=true
PORT=8080
EOF
  }

  cleanup() {
    rm -f "${TEST_FILE}"
  }

  BeforeEach 'setup'
  AfterEach 'cleanup'

  It 'reads API key'
    When call read_config "${TEST_FILE}" "API_KEY"
    The output should equal "secret123"
  End

  It 'reads PORT'
    When call read_config "${TEST_FILE}" "PORT"
    The output should equal "8080"
  End

  It 'returns error for missing file'
    When call read_config "/nonexistent" "API_KEY"
    The status should be failure
  End
End
```

### File Modification

```bash
Describe 'update_config'
  update_config() {
    local config_file="$1"
    local key="$2"
    local value="$3"

    if [[ -f "${config_file}" ]]; then
      sed -i.bak "s/^${key}=.*/${key}=${value}/" "${config_file}"
      rm -f "${config_file}.bak"
    fi
  }

  setup() {
    TEST_FILE=$(mktemp)
    echo "PORT=8080" > "${TEST_FILE}"
  }

  cleanup() {
    rm -f "${TEST_FILE}" "${TEST_FILE}.bak"
  }

  BeforeEach 'setup'
  AfterEach 'cleanup'

  It 'updates PORT value'
    update_config "${TEST_FILE}" "PORT" "9090"
    The contents of file "${TEST_FILE}" should equal "PORT=9090"
  End
End
```

## Testing stdout and stderr Separately

### Separate Streams

```bash
Describe 'process_with_logging'
  process_with_logging() {
    local level="$1"
    local message="$2"

    # Log to stderr
    echo "[${level}] ${message}" >&2

    # Output to stdout
    if [[ "${level}" == "ERROR" ]]; then
      return 1
    else
      echo "Processing complete"
      return 0
    fi
  }

  It 'outputs to stdout on success'
    When call process_with_logging "INFO" "test"
    The output should equal "Processing complete"
    The stderr should include "[INFO] test"
    The status should be success
  End

  It 'fails on error level'
    When call process_with_logging "ERROR" "failure"
    The stderr should include "[ERROR] failure"
    The status should be failure
  End
End
```

### Testing Only stderr

```bash
Describe 'log_error'
  log_error() {
    echo "ERROR: $*" >&2
  }

  It 'logs to stderr only'
    When call log_error "Something went wrong"
    The stderr should equal "ERROR: Something went wrong"
    The output should equal ""
  End
End
```

## Data-Driven (Parameterized) Tests

### Testing Multiple Inputs

```bash
Describe 'is_even'
  is_even() {
    (( $1 % 2 == 0 ))
  }

  Parameters
    0    success
    2    success
    4    success
    100  success
    1    failure
    3    failure
    99   failure
  End

  Example "number $1 should be $2"
    When call is_even "$1"
    The status should be "$2"
  End
End
```

### Testing Email Validation

```bash
Describe 'validate_email'
  validate_email() {
    [[ "$1" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]
  }

  Parameters
    "user@example.com"          success
    "test.user@example.com"     success
    "user+tag@example.com"      success
    "invalid.email"             failure
    "@example.com"              failure
    "user@"                     failure
    "user@domain"               failure
  End

  Example "validates email: $1"
    When call validate_email "$1"
    The status should be "$2"
  End
End
```

### Matrix Testing

```bash
Describe 'permission_check'
  check_permission() {
    local user="$1"
    local role="$2"
    local action="$3"

    if [[ "${role}" == "admin" ]]; then
      return 0
    elif [[ "${role}" == "user" && "${action}" == "read" ]]; then
      return 0
    else
      return 1
    fi
  }

  Parameters:matrix
    alice bob charlie
    admin user guest
    read write delete
  End

  # Generates combinations like:
  # alice admin read
  # alice admin write
  # alice user read
  # etc.

  Example "user=$1 role=$2 action=$3"
    When call check_permission "$1" "$2" "$3"
    # Test expectations based on parameters
  End
End
```

## Testing with Temporary Files

### Single Temp File

```bash
Describe 'process_file'
  setup() {
    TEST_FILE=$(mktemp)
    echo "test data" > "${TEST_FILE}"
  }

  cleanup() {
    rm -f "${TEST_FILE}"
  }

  BeforeEach 'setup'
  AfterEach 'cleanup'

  It 'processes file'
    When call process_file "${TEST_FILE}"
    The status should be success
  End
End
```

### Temp Directory

```bash
Describe 'batch_process'
  setup() {
    TEST_DIR=$(mktemp -d)
    echo "file1" > "${TEST_DIR}/file1.txt"
    echo "file2" > "${TEST_DIR}/file2.txt"
  }

  cleanup() {
    rm -rf "${TEST_DIR}"
  }

  BeforeEach 'setup'
  AfterEach 'cleanup'

  It 'processes all files in directory'
    When call batch_process "${TEST_DIR}"
    The status should be success
  End
End
```

## Testing Configuration Loading

### Environment Variables

```bash
Describe 'get_database_url'
  get_database_url() {
    local env="${APP_ENV:-development}"

    case "${env}" in
      production)
        echo "postgres://prod.example.com/db"
        ;;
      staging)
        echo "postgres://staging.example.com/db"
        ;;
      *)
        echo "postgres://localhost/dev_db"
        ;;
    esac
  }

  Context 'in production environment'
    It 'returns production URL'
      APP_ENV=production
      When call get_database_url
      The output should include "prod.example.com"
    End
  End

  Context 'in development environment'
    It 'returns local URL'
      unset APP_ENV
      When call get_database_url
      The output should include "localhost"
    End
  End
End
```

### Config File Loading

```bash
Describe 'load_config'
  load_config() {
    local config_file="${1:-config.ini}"

    if [[ -f "${config_file}" ]]; then
      source "${config_file}"
    else
      return 1
    fi
  }

  setup() {
    CONFIG_FILE=$(mktemp)
    cat > "${CONFIG_FILE}" <<'EOF'
API_KEY="secret123"
DEBUG=true
PORT=8080
EOF
  }

  cleanup() {
    rm -f "${CONFIG_FILE}"
  }

  BeforeEach 'setup'
  AfterEach 'cleanup'

  It 'loads configuration variables'
    When call load_config "${CONFIG_FILE}"
    The status should be success
    The variable API_KEY should equal "secret123"
  End
End
```

## Testing String Operations

### String Transformation

```bash
Describe 'to_uppercase'
  to_uppercase() {
    echo "$1" | tr '[:lower:]' '[:upper:]'
  }

  It 'converts lowercase to uppercase'
    When call to_uppercase "hello"
    The output should equal "HELLO"
  End

  It 'handles mixed case'
    When call to_uppercase "Hello World"
    The output should equal "HELLO WORLD"
  End

  It 'preserves uppercase'
    When call to_uppercase "ALREADY"
    The output should equal "ALREADY"
  End
End
```

### String Parsing

```bash
Describe 'parse_version'
  parse_version() {
    local version="$1"
    local major minor patch

    IFS='.' read -r major minor patch <<< "${version}"
    echo "Major: ${major}, Minor: ${minor}, Patch: ${patch}"
  }

  It 'parses semantic version'
    When call parse_version "1.2.3"
    The output should equal "Major: 1, Minor: 2, Patch: 3"
  End
End
```

## Testing JSON Processing

### JSON Output

```bash
Describe 'generate_json'
  generate_json() {
    local name="$1"
    local age="$2"

    cat <<EOF
{
  "name": "${name}",
  "age": ${age}
}
EOF
  }

  It 'generates valid JSON'
    When call generate_json "Alice" 30
    The output should include '"name": "Alice"'
    The output should include '"age": 30'
  End

  It 'can be parsed with jq'
    result=$(generate_json "Bob" 25)
    name=$(echo "${result}" | jq -r '.name')
    The variable name should equal "Bob"
  End
End
```

### JSON Parsing

```bash
Describe 'extract_field'
  extract_field() {
    local json="$1"
    local field="$2"

    echo "${json}" | jq -r ".${field}"
  }

  It 'extracts field from JSON'
    json='{"name":"Alice","age":30}'
    When call extract_field "${json}" "name"
    The output should equal "Alice"
  End
End
```

## Testing Array Operations

### Array Processing

```bash
Describe 'array_sum'
  array_sum() {
    local total=0
    local -a array=("$@")

    for num in "${array[@]}"; do
      ((total += num))
    done

    echo "${total}"
  }

  It 'sums array elements'
    When call array_sum 1 2 3 4 5
    The output should equal "15"
  End

  It 'handles single element'
    When call array_sum 42
    The output should equal "42"
  End

  It 'handles empty array'
    When call array_sum
    The output should equal "0"
  End
End
```

## Testing Long-Running Operations

### Timeout Handling

```bash
Describe 'wait_for_service'
  wait_for_service() {
    local timeout=5
    local elapsed=0

    while ! service_is_ready; do
      sleep 1
      ((elapsed++))

      if (( elapsed >= timeout )); then
        echo "Timeout waiting for service" >&2
        return 1
      fi
    done

    return 0
  }

  Context 'when service starts quickly'
    # Mock service_is_ready to return success
    service_is_ready() {
      return 0
    }

    It 'succeeds immediately'
      When call wait_for_service
      The status should be success
    End
  End

  Context 'when service never starts'
    # Mock service_is_ready to always fail
    service_is_ready() {
      return 1
    }

    It 'times out after 5 seconds'
      When call wait_for_service
      The stderr should include "Timeout"
      The status should be failure
    End
  End
End
```

## Best Practices

1. **Test one behavior per example** - Focused tests are easier to debug
2. **Use descriptive names** - Test name should explain what's being tested
3. **Test edge cases** - Empty input, maximum values, boundary conditions
4. **Mock external dependencies** - Tests should be fast and reliable
5. **Use fixtures for complex data** - Keep tests readable
6. **Test both success and failure** - Error paths are critical
7. **Keep tests independent** - No shared state between tests

## Next Steps

- Read `04-mocking-and-stubbing.md` for isolation patterns
- Read `06-tdd-workflow.md` for test-first development
- Check `assets/advanced_spec_example.sh` for more examples
