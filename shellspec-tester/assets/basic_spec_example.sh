# Basic ShellSpec Example
# Demonstrates fundamental testing patterns

# shellcheck shell=bash

Describe 'basic_function'
  # Example function to test
  basic_function() {
    echo "Hello, $1!"
    return 0
  }

  It 'outputs greeting with name'
    When call basic_function "World"
    The output should equal "Hello, World!"
  End

  It 'returns success exit code'
    When call basic_function "Test"
    The status should be success
  End

  It 'handles empty argument'
    When call basic_function ""
    The output should equal "Hello, !"
  End
End

Describe 'string_operations'
  # Example function with string manipulation
  string_length() {
    echo "${#1}"
  }

  It 'returns length of string'
    When call string_length "hello"
    The output should equal "5"
  End

  It 'returns zero for empty string'
    When call string_length ""
    The output should equal "0"
  End
End

Describe 'exit_code_testing'
  # Example function with different exit codes
  validate_input() {
    local input="$1"
    if [[ -z "${input}" ]]; then
      echo "Error: Input cannot be empty" >&2
      return 1
    fi
    echo "Valid input: ${input}"
    return 0
  }

  Context 'with valid input'
    It 'succeeds and outputs confirmation'
      When call validate_input "test"
      The output should include "Valid input"
      The status should be success
    End
  End

  Context 'with empty input'
    It 'fails with error message'
      When call validate_input ""
      The stderr should include "Error: Input cannot be empty"
      The status should be failure
    End
  End
End

Describe 'file_operations'
  # Setup and teardown for file tests
  setup() {
    TEST_FILE=$(mktemp)
  }

  cleanup() {
    rm -f "${TEST_FILE}"
  }

  BeforeEach 'setup'
  AfterEach 'cleanup'

  # Function to test
  write_to_file() {
    local content="$1"
    local file="$2"
    echo "${content}" > "${file}"
  }

  It 'creates file with content'
    When call write_to_file "test content" "${TEST_FILE}"
    The file "${TEST_FILE}" should be exist
    The contents of file "${TEST_FILE}" should equal "test content"
  End
End
