# Spec Helper - Common Setup for All Tests
# This file is loaded before each spec file via the .shellspec configuration

# shellcheck shell=bash
# shellcheck disable=SC2148

#===============================================================================
# PATH SETUP - Ensure scripts under test are accessible
#===============================================================================

# Add project scripts directory to PATH so functions can be sourced
# Adjust this path based on your project structure
SCRIPT_DIR="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}/scripts"
export PATH="${SCRIPT_DIR}:${PATH}"

#===============================================================================
# TEST FIXTURES - Set up test data and temporary directories
#===============================================================================

# Create temporary directory for test fixtures
setup_test_fixtures() {
  TEST_TEMP_DIR=$(mktemp -d)
  export TEST_TEMP_DIR
}

# Clean up test fixtures after tests
cleanup_test_fixtures() {
  if [[ -n "${TEST_TEMP_DIR}" && -d "${TEST_TEMP_DIR}" ]]; then
    rm -rf "${TEST_TEMP_DIR}"
  fi
}

#===============================================================================
# HELPER FUNCTIONS - Utilities for tests
#===============================================================================

# Create a test file with content
create_test_file() {
  local filename="$1"
  local content="$2"
  echo "${content}" > "${TEST_TEMP_DIR}/${filename}"
}

# Assert file exists with expected content
assert_file_contains() {
  local filename="$1"
  local expected="$2"
  grep -q "${expected}" "${TEST_TEMP_DIR}/${filename}"
}

#===============================================================================
# MOCKING SETUP - Common mocked commands
#===============================================================================

# Example: Mock a command that doesn't exist in test environment
# Uncomment and customize as needed:
#
# mock_external_command() {
#   # Create a mock implementation
#   eval "
#   external_command() {
#     echo 'mocked output'
#     return 0
#   }
#   "
# }

#===============================================================================
# LOAD FUNCTIONS UNDER TEST
#===============================================================================

# Source the functions/scripts you want to test
# Adjust paths based on your project structure
# Example:
# source "${SCRIPT_DIR}/backup_functions.sh"
# source "${SCRIPT_DIR}/utility_functions.sh"
