# Advanced ShellSpec Example
# Demonstrates advanced testing patterns: mocking, data-driven tests, stderr/stdout

# shellcheck shell=bash
# shellcheck disable=SC2329  # Mock functions are invoked by ShellSpec framework

Describe 'data_driven_testing'
  # Function to test - validates email format
  validate_email() {
    local email="$1"
    if [[ "${email}" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
      echo "Valid email"
      return 0
    else
      echo "Invalid email" >&2
      return 1
    fi
  }

  # Parameterized tests using Examples
  Parameters
    "user@example.com"          success
    "test.user+tag@domain.co"   success
    "invalid.email"             failure
    "@no-local-part.com"        failure
    "no-at-sign.com"            failure
    "user@"                     failure
  End

  Example "validates email: $1 (expect: $2)"
    When call validate_email "$1"
    The status should be "$2"
  End
End

Describe 'testing_stderr_and_stdout'
  # Function that outputs to both stdout and stderr
  process_with_logging() {
    local level="$1"
    local message="$2"

    case "${level}" in
      info)
        echo "INFO: ${message}"
        return 0
        ;;
      error)
        echo "ERROR: ${message}" >&2
        return 1
        ;;
      both)
        echo "Processing: ${message}"
        echo "DEBUG: Processing ${message}" >&2
        return 0
        ;;
      *)
        echo "Unknown level: ${level}" >&2
        return 2
        ;;
    esac
  }

  It 'outputs to stdout for info level'
    When call process_with_logging "info" "test message"
    The output should equal "INFO: test message"
    The stderr should equal ""
    The status should be success
  End

  It 'outputs to stderr for error level'
    When call process_with_logging "error" "error message"
    The stderr should equal "ERROR: error message"
    The output should equal ""
    The status should be failure
  End

  It 'outputs to both stdout and stderr'
    When call process_with_logging "both" "dual message"
    The output should include "Processing: dual message"
    The stderr should include "DEBUG: Processing dual message"
    The status should be success
  End
End

Describe 'mocking_external_commands'
  # Function that depends on external command
  check_disk_space() {
    local threshold="$1"
    local usage
    usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

    if [[ "${usage}" -gt "${threshold}" ]]; then
      echo "Disk usage ${usage}% exceeds threshold ${threshold}%"
      return 1
    else
      echo "Disk usage ${usage}% is within threshold"
      return 0
    fi
  }

  Context 'when disk usage is low'
    # Mock df command to return low usage
    df() {
      cat <<EOF
Filesystem     Size   Used  Avail Capacity  iused     ifree %iused  Mounted on
/dev/disk1    500G   100G   400G    20%    1000000  9000000   10%   /
EOF
    }

    It 'reports usage within threshold'
      When call check_disk_space 50
      The output should include "is within threshold"
      The status should be success
    End
  End

  Context 'when disk usage is high'
    # Mock df command to return high usage
    df() {
      cat <<EOF
Filesystem     Size   Used  Avail Capacity  iused     ifree %iused  Mounted on
/dev/disk1    500G   450G    50G    90%    1000000  9000000   10%   /
EOF
    }

    It 'reports usage exceeds threshold'
      When call check_disk_space 80
      The output should include "exceeds threshold"
      The status should be failure
    End
  End
End

Describe 'testing_with_fixtures'
  # Setup complex test fixtures
  setup_fixtures() {
    FIXTURE_DIR=$(mktemp -d)

    # Create test directory structure
    mkdir -p "${FIXTURE_DIR}/data/input"
    mkdir -p "${FIXTURE_DIR}/data/output"

    # Create test files
    echo "test data 1" > "${FIXTURE_DIR}/data/input/file1.txt"
    echo "test data 2" > "${FIXTURE_DIR}/data/input/file2.txt"
  }

  cleanup_fixtures() {
    rm -rf "${FIXTURE_DIR}"
  }

  BeforeEach 'setup_fixtures'
  AfterEach 'cleanup_fixtures'

  # Function to test
  process_files() {
    local input_dir="$1"
    local output_dir="$2"

    for file in "${input_dir}"/*.txt; do
      local basename
      basename=$(basename "${file}")
      tr '[:lower:]' '[:upper:]' < "${file}" > "${output_dir}/${basename}"
    done
  }

  It 'processes all input files'
    When call process_files "${FIXTURE_DIR}/data/input" "${FIXTURE_DIR}/data/output"
    The file "${FIXTURE_DIR}/data/output/file1.txt" should be exist
    The file "${FIXTURE_DIR}/data/output/file2.txt" should be exist
  End

  It 'converts content to uppercase'
    When call process_files "${FIXTURE_DIR}/data/input" "${FIXTURE_DIR}/data/output"
    The contents of file "${FIXTURE_DIR}/data/output/file1.txt" should equal "TEST DATA 1"
  End
End

Describe 'pending_and_skip_tests'
  # Pending test - marked as TODO
  It 'will be implemented later'
    Pending "Feature not implemented yet"
  End

  # Skip test - temporarily disabled
  It 'is temporarily disabled'
    Skip "Skipping due to known issue #123"
  End

  # Skip entire context
  Context 'experimental feature'
    Skip "Entire context skipped until feature is ready"

    It 'has some test'
      # This won't run
    End
  End
End
