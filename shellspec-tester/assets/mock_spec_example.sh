# Mocking and Stubbing Comprehensive Examples
# Demonstrates various mocking techniques in ShellSpec

# shellcheck shell=bash
# shellcheck disable=SC2329  # Mock functions are invoked by ShellSpec framework

Describe 'simple_function_mocking'
  # Original function we want to mock
  get_current_user() {
    whoami
  }

  # Function that uses the command we'll mock
  create_user_greeting() {
    local user
    user=$(get_current_user)
    echo "Welcome, ${user}!"
  }

  Context 'with mocked user'
    # Mock the function to return specific value
    get_current_user() {
      echo "testuser"
    }

    It 'uses mocked username'
      When call create_user_greeting
      The output should equal "Welcome, testuser!"
    End
  End
End

Describe 'command_mocking_with_exit_codes'
  # Function that depends on curl command
  fetch_api_data() {
    local url="$1"
    local response

    if ! response=$(curl -s "${url}"); then
      echo "Failed to fetch data" >&2
      return 1
    fi

    echo "${response}"
    return 0
  }

  Context 'when API call succeeds'
    # Mock curl to return success
    curl() {
      if [[ "$*" == *"-s http://api.example.com/data"* ]]; then
        echo '{"status": "ok", "data": [1,2,3]}'
        return 0
      fi
    }

    It 'returns API response'
      When call fetch_api_data "http://api.example.com/data"
      The output should include '"status": "ok"'
      The status should be success
    End
  End

  Context 'when API call fails'
    # Mock curl to return failure
    curl() {
      return 1
    }

    It 'handles connection error'
      When call fetch_api_data "http://api.example.com/data"
      The stderr should include "Failed to fetch data"
      The status should be failure
    End
  End
End

Describe 'conditional_mocking'
  # Function that calls different commands based on OS
  get_os_info() {
    if command -v sw_vers &>/dev/null; then
      sw_vers -productVersion
    elif command -v lsb_release &>/dev/null; then
      lsb_release -r -s
    else
      echo "Unknown OS"
    fi
  }

  Context 'on macOS'
    # Mock macOS commands
    command() {
      if [[ "$1" == "-v" && "$2" == "sw_vers" ]]; then
        return 0
      else
        return 1
      fi
    }

    sw_vers() {
      if [[ "$1" == "-productVersion" ]]; then
        echo "14.0"
      fi
    }

    It 'returns macOS version'
      When call get_os_info
      The output should equal "14.0"
    End
  End

  Context 'on Linux'
    # Mock Linux commands
    command() {
      if [[ "$1" == "-v" && "$2" == "lsb_release" ]]; then
        return 0
      else
        return 1
      fi
    }

    lsb_release() {
      if [[ "$*" == "-r -s" ]]; then
        echo "22.04"
      fi
    }

    It 'returns Linux version'
      When call get_os_info
      The output should equal "22.04"
    End
  End
End

Describe 'mocking_with_state_verification'
  # Track whether mock was called
  # shellcheck disable=SC2034  # Variables used by ShellSpec assertions below
  MOCK_CALLED=false
  MOCK_CALL_COUNT=0
  MOCK_LAST_ARGS=""

  # Function that calls external service
  send_notification() {
    local message="$1"
    notify-send "App" "${message}"
  }

  # Mock with state tracking
  notify-send() {
    # shellcheck disable=SC2034  # Variables used by ShellSpec assertions
    MOCK_CALLED=true
    # shellcheck disable=SC2034  # Variables used by ShellSpec assertions
    ((MOCK_CALL_COUNT++))
    # shellcheck disable=SC2034  # Variables used by ShellSpec assertions
    MOCK_LAST_ARGS="$*"
    return 0
  }

  BeforeEach 'reset_mock_state() { MOCK_CALLED=false; MOCK_CALL_COUNT=0; MOCK_LAST_ARGS=""; }'

  It 'calls notification service'
    When call send_notification "Test message"
    The variable MOCK_CALLED should equal true
    The variable MOCK_CALL_COUNT should equal 1
  End

  It 'passes correct arguments'
    When call send_notification "Hello World"
    The variable MOCK_LAST_ARGS should include "Hello World"
  End
End

Describe 'mocking_file_operations'
  # Function that reads configuration file
  load_config() {
    local config_file="$1"
    local value

    if [[ ! -f "${config_file}" ]]; then
      echo "Config file not found" >&2
      return 1
    fi

    value=$(grep "^API_KEY=" "${config_file}" | cut -d= -f2)
    echo "${value}"
  }

  Context 'with valid config file'
    # Mock file test and grep
    test() {
      if [[ "$1" == "-f" ]]; then
        return 0  # File exists
      fi
    }

    grep() {
      if [[ "$1" == "^API_KEY=" ]]; then
        echo "API_KEY=secret123"
      fi
    }

    cut() {
      if [[ "$*" == "-d= -f2" ]]; then
        echo "secret123"
      fi
    }

    It 'loads API key from config'
      When call load_config "/etc/app/config"
      The output should equal "secret123"
      The status should be success
    End
  End

  Context 'with missing config file'
    # Mock file test to fail
    test() {
      if [[ "$1" == "-f" ]]; then
        return 1  # File doesn't exist
      fi
    }

    It 'reports missing config file'
      When call load_config "/etc/app/config"
      The stderr should include "Config file not found"
      The status should be failure
    End
  End
End

Describe 'mocking_environment_variables'
  # Function that depends on environment
  get_database_url() {
    local env="${APP_ENV:-development}"

    case "${env}" in
      production)
        echo "postgres://prod.example.com/db"
        ;;
      staging)
        echo "postgres://staging.example.com/db"
        ;;
      development)
        echo "postgres://localhost/dev_db"
        ;;
      *)
        echo "Unknown environment: ${env}" >&2
        return 1
        ;;
    esac
  }

  Parameters
    "production"   "postgres://prod.example.com/db"
    "staging"      "postgres://staging.example.com/db"
    "development"  "postgres://localhost/dev_db"
  End

  Example "returns correct URL for environment: $1"
    APP_ENV="$1"
    When call get_database_url
    The output should equal "$2"
  End
End

Describe 'mocking_date_and_time'
  # Function that generates timestamped filename
  create_backup_filename() {
    local prefix="$1"
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    echo "${prefix}_${timestamp}.tar.gz"
  }

  Context 'with fixed timestamp'
    # Mock date command
    date() {
      if [[ "$*" == "+%Y%m%d_%H%M%S" ]]; then
        echo "20240115_143022"
      fi
    }

    It 'generates filename with timestamp'
      When call create_backup_filename "database"
      The output should equal "database_20240115_143022.tar.gz"
    End
  End
End
