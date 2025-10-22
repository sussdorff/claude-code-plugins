# Mocking and Stubbing in ShellSpec

Complete guide to isolating tests using mocks and stubs for external dependencies.

## Why Mock?

Mocking allows you to:
- **Isolate tests** - Test one function without depending on others
- **Control behavior** - Make external commands return specific values
- **Test error conditions** - Simulate failures without breaking real systems
- **Speed up tests** - Avoid slow external calls
- **Test offline** - Don't depend on network or external services

## Basic Function Mocking

### Simple Function Override

Replace a function with a mock version:

```bash
Describe 'greet_user'
  # Function under test
  greet_user() {
    local username
    username=$(get_current_user)
    echo "Hello, ${username}!"
  }

  # Original function we want to mock
  get_current_user() {
    whoami  # Expensive or environment-dependent
  }

  Context 'with mocked user'
    # Override the function
    get_current_user() {
      echo "testuser"
    }

    It 'greets the user'
      When call greet_user
      The output should equal "Hello, testuser!"
    End
  End
End
```

### Mock Within Test

```bash
It 'uses mocked value'
  # Define mock in the test itself
  expensive_calculation() {
    echo "42"  # Instead of actual calculation
  }

  When call my_function
  The output should include "42"
End
```

## Command Mocking

### Mock External Commands

Override system commands:

```bash
Describe 'check_disk_space'
  check_disk_space() {
    local usage
    usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

    if (( usage > 80 )); then
      echo "Disk space critical: ${usage}%"
      return 1
    fi
    return 0
  }

  Context 'when disk is full'
    # Mock df command
    df() {
      cat <<EOF
Filesystem     Size   Used  Avail Capacity  Mounted on
/dev/disk1    500G   450G    50G    90%    /
EOF
    }

    It 'reports critical disk space'
      When call check_disk_space
      The output should include "Disk space critical: 90%"
      The status should be failure
    End
  End

  Context 'when disk has space'
    df() {
      cat <<EOF
Filesystem     Size   Used  Avail Capacity  Mounted on
/dev/disk1    500G   100G   400G    20%    /
EOF
    }

    It 'reports normal disk space'
      When call check_disk_space
      The status should be success
    End
  End
End
```

### Mock with Different Return Codes

```bash
Describe 'backup_to_remote'
  backup_to_remote() {
    if rsync -av /data remote:/backup; then
      echo "Backup successful"
      return 0
    else
      echo "Backup failed" >&2
      return 1
    fi
  }

  Context 'when rsync succeeds'
    rsync() {
      echo "sending incremental file list"
      return 0
    }

    It 'reports success'
      When call backup_to_remote
      The output should include "Backup successful"
      The status should be success
    End
  End

  Context 'when rsync fails'
    rsync() {
      echo "rsync: connection failed" >&2
      return 1
    }

    It 'reports failure'
      When call backup_to_remote
      The stderr should include "Backup failed"
      The status should be failure
    End
  End
End
```

## Conditional Mocking

### Mock Based on Arguments

```bash
Describe 'api_client'
  fetch_data() {
    local endpoint="$1"
    curl -s "https://api.example.com/${endpoint}"
  }

  # Mock curl to return different data based on endpoint
  curl() {
    case "$*" in
      *users*)
        echo '{"users": ["alice", "bob"]}'
        ;;
      *posts*)
        echo '{"posts": [1, 2, 3]}'
        ;;
      *)
        echo '{"error": "not found"}'
        return 1
        ;;
    esac
  }

  It 'fetches users'
    When call fetch_data "users"
    The output should include '"users"'
  End

  It 'fetches posts'
    When call fetch_data "posts"
    The output should include '"posts"'
  End

  It 'handles unknown endpoint'
    When call fetch_data "unknown"
    The output should include '"error"'
    The status should be failure
  End
End
```

### Mock Based on Environment

```bash
Describe 'deploy_application'
  deploy() {
    if [[ "${ENV}" == "production" ]]; then
      deploy_to_production
    else
      deploy_to_staging
    fi
  }

  Context 'deploying to production'
    ENV="production"

    deploy_to_production() {
      echo "Deployed to production"
    }

    deploy_to_staging() {
      echo "This should not be called"
      return 1
    }

    It 'calls production deployment'
      When call deploy
      The output should include "Deployed to production"
    End
  End
End
```

## State Verification

### Track Mock Calls

```bash
Describe 'notification system'
  # Track mock state
  setup_mock() {
    MOCK_CALLED=false
    MOCK_CALL_COUNT=0
    MOCK_ARGS=""
  }

  BeforeEach 'setup_mock'

  send_alert() {
    local message="$1"
    notify_user "Alert: ${message}"
  }

  # Mock with state tracking
  notify_user() {
    MOCK_CALLED=true
    ((MOCK_CALL_COUNT++))
    MOCK_ARGS="$*"
  }

  It 'calls notification function'
    When call send_alert "Server down"
    The variable MOCK_CALLED should equal true
  End

  It 'calls notification once'
    When call send_alert "Test"
    The variable MOCK_CALL_COUNT should equal 1
  End

  It 'passes correct message'
    When call send_alert "Error occurred"
    The variable MOCK_ARGS should include "Alert: Error occurred"
  End
End
```

### Verify Argument Values

```bash
Describe 'logging system'
  LOGGED_MESSAGES=()

  log_message() {
    LOGGED_MESSAGES+=("$*")
  }

  process_data() {
    log_message "Starting process"
    # ... do work ...
    log_message "Process complete"
  }

  It 'logs start message'
    When call process_data
    The value "${LOGGED_MESSAGES[0]}" should equal "Starting process"
  End

  It 'logs completion message'
    When call process_data
    The value "${LOGGED_MESSAGES[1]}" should equal "Process complete"
  End

  It 'logs two messages'
    When call process_data
    The value "${#LOGGED_MESSAGES[@]}" should equal 2
  End
End
```

## Advanced Mocking Patterns

### Mock File Operations

```bash
Describe 'configuration loader'
  load_config() {
    local config_file="$1"

    if [[ ! -f "${config_file}" ]]; then
      echo "Config not found" >&2
      return 1
    fi

    grep "^API_KEY=" "${config_file}" | cut -d= -f2
  }

  Context 'when config exists'
    # Mock file existence check
    test() {
      if [[ "$1" == "-f" ]]; then
        return 0  # File exists
      fi
    }

    # Mock grep
    grep() {
      if [[ "$1" == "^API_KEY=" ]]; then
        echo "API_KEY=secret123"
      fi
    }

    # Mock cut
    cut() {
      echo "secret123"
    }

    It 'extracts API key'
      When call load_config "/etc/app/config"
      The output should equal "secret123"
    End
  End

  Context 'when config missing'
    test() {
      if [[ "$1" == "-f" ]]; then
        return 1  # File doesn't exist
      fi
    }

    It 'returns error'
      When call load_config "/etc/app/config"
      The stderr should include "Config not found"
      The status should be failure
    End
  End
End
```

### Mock Date/Time

```bash
Describe 'timestamp functions'
  generate_filename() {
    local prefix="$1"
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    echo "${prefix}_${timestamp}.log"
  }

  Context 'with fixed timestamp'
    date() {
      if [[ "$*" == "+%Y%m%d_%H%M%S" ]]; then
        echo "20240115_143022"
      fi
    }

    It 'generates consistent filename'
      When call generate_filename "backup"
      The output should equal "backup_20240115_143022.log"
    End
  End
End
```

### Mock Network Calls

```bash
Describe 'weather service'
  get_weather() {
    local city="$1"
    local response
    response=$(curl -s "https://api.weather.com/current?city=${city}")
    echo "${response}" | jq -r '.temperature'
  }

  Context 'with successful API response'
    curl() {
      echo '{"temperature": "22°C", "condition": "sunny"}'
    }

    jq() {
      echo "22°C"
    }

    It 'returns temperature'
      When call get_weather "London"
      The output should equal "22°C"
    End
  End

  Context 'with API failure'
    curl() {
      return 1
    }

    It 'handles connection error'
      When call get_weather "London"
      The status should be failure
    End
  End
End
```

### Mock Random Values

```bash
Describe 'random_functions'
  generate_id() {
    echo "user_$(( RANDOM % 1000 ))"
  }

  Context 'with seeded random'
    # Mock RANDOM variable
    RANDOM=42

    It 'generates predictable ID'
      When call generate_id
      The output should equal "user_42"
    End
  End
End
```

## Partial Mocking

Mock only specific behavior while keeping rest intact:

```bash
Describe 'complex_function'
  # Original function with multiple steps
  process_pipeline() {
    local data
    data=$(fetch_data)        # Mock this
    data=$(transform_data "${data}")  # Keep original
    save_data "${data}"       # Mock this
  }

  # Keep original transform
  transform_data() {
    echo "$1" | tr '[:lower:]' '[:upper:]'
  }

  Context 'with mocked I/O'
    # Mock input
    fetch_data() {
      echo "test data"
    }

    # Mock output
    SAVED_DATA=""
    save_data() {
      SAVED_DATA="$1"
    }

    # transform_data remains original

    It 'transforms data correctly'
      When call process_pipeline
      The variable SAVED_DATA should equal "TEST DATA"
    End
  End
End
```

## Mock Cleanup

### Scope Mocks to Context

```bash
Describe 'scoped mocks'
  original_function() {
    echo "original"
  }

  Context 'first context'
    # Mock only applies within this context
    original_function() {
      echo "mocked in context 1"
    }

    It 'uses mock'
      When call original_function
      The output should equal "mocked in context 1"
    End
  End

  Context 'second context'
    # Different mock
    original_function() {
      echo "mocked in context 2"
    }

    It 'uses different mock'
      When call original_function
      The output should equal "mocked in context 2"
    End
  End
End
```

### Reset Mocks Between Tests

```bash
Describe 'mock reset'
  reset_mocks() {
    # Clear tracked state
    MOCK_CALLED=false
    MOCK_CALL_COUNT=0
    unset -f my_function  # Remove mock function
  }

  BeforeEach 'reset_mocks'

  It 'test 1'
    my_function() { echo "mock 1"; }
    # ...
  End

  It 'test 2'
    # Clean slate, previous mock is gone
    my_function() { echo "mock 2"; }
    # ...
  End
End
```

## Testing with Real Dependencies

### Mix Real and Mock

```bash
Describe 'integration_test'
  Context 'with real database but mocked email'
    # Use real database connection
    # (No mock for db_connect)

    # Mock email service
    send_email() {
      echo "Email mocked: $*"
      return 0
    }

    It 'processes order'
      When call process_order 123
      # Real DB operations tested
      # Email sending mocked
    End
  End
End
```

## Common Mocking Pitfalls

### Pitfall 1: Mock Not in Scope

```bash
# Wrong - mock defined outside test
curl() { echo "mocked"; }

It 'test'
  When call my_function
  # my_function might not see the mock
End

# Right - mock inside context
Context 'with mocked curl'
  curl() { echo "mocked"; }

  It 'test'
    When call my_function
  End
End
```

### Pitfall 2: Forgetting to Return

```bash
# Wrong - no return code
curl() {
  echo "mocked response"
  # Missing return code!
}

# Right - explicit return
curl() {
  echo "mocked response"
  return 0
}
```

### Pitfall 3: Over-Mocking

```bash
# Wrong - mocking the function under test
It 'validates user'
  validate_user() {
    return 0  # Mocking what we're testing!
  }

  When call validate_user
  The status should be success  # This test is useless
End

# Right - mock dependencies, test real function
It 'validates user'
  # Mock dependency
  check_database() {
    return 0
  }

  # Test real validate_user function
  When call validate_user "alice"
  The status should be success
End
```

## Best Practices

1. **Mock at boundaries** - Mock I/O, network, filesystem, external commands
2. **Keep mocks simple** - Return minimal valid data
3. **Verify behavior** - Track that mocks were called correctly
4. **Use real code when possible** - Only mock what's necessary
5. **Reset between tests** - Don't let mock state leak between tests
6. **Test both success and failure** - Mock error conditions
7. **Document mocks** - Comment why you're mocking

## Next Steps

- Read `08-common-patterns.md` for mocking patterns
- Read `10-troubleshooting.md` for mock debugging
- Check `assets/mock_spec_example.sh` for comprehensive examples
