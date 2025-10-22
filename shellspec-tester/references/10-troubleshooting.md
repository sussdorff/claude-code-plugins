# Troubleshooting ShellSpec

Common issues, solutions, and debugging techniques for ShellSpec tests.

## Installation Issues

### "shellspec: command not found"

**Symptom**:
```bash
$ shellspec
bash: shellspec: command not found
```

**Solutions**:

1. **Add to PATH**:
```bash
export PATH="${HOME}/.local/lib/shellspec:${PATH}"
```

Add to `~/.bashrc` or `~/.zshrc` to persist.

2. **Use full path**:
```bash
${HOME}/.local/lib/shellspec/shellspec
```

3. **Create symlink**:
```bash
sudo ln -s ${HOME}/.local/lib/shellspec/shellspec /usr/local/bin/shellspec
```

### "Permission denied" when running shellspec

**Symptom**:
```bash
$ shellspec
bash: ./shellspec: Permission denied
```

**Solution**:
```bash
chmod +x ~/.local/lib/shellspec/shellspec
```

### Kcov not found

**Symptom**:
```bash
$ shellspec --kcov
Error: kcov command not found
```

**Solutions**:

**macOS**:
```bash
brew install kcov
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install kcov
```

**Verify**:
```bash
kcov --version
```

## Test Discovery Issues

### No examples found

**Symptom**:
```bash
$ shellspec
No examples found
```

**Causes and Solutions**:

1. **Spec files not named correctly**:
```bash
# Wrong
test_backup.sh
backup.test.sh

# Correct
backup_spec.sh
```

2. **Spec files in wrong directory**:
```bash
# Default spec directory is 'spec/'
mkdir -p spec
mv test_*.sh spec/
rename 's/test_//' spec/test_*.sh
rename 's/$/_spec/' spec/*.sh
```

3. **Specify spec directory**:
```bash
shellspec --directory tests
```

Or in `.shellspec`:
```bash
--spec-dir tests
```

### Tests not running after changes

**Solution**:

Clear ShellSpec cache:
```bash
rm -rf .shellspec-cache
shellspec
```

## Test Execution Failures

### "The function 'X' is not defined"

**Symptom**:
```bash
The function "my_function" is not defined
```

**Causes and Solutions**:

1. **Function not sourced**:
```bash
# spec/spec_helper.sh
source "${PROJECT_ROOT}/scripts/my_script.sh"
```

2. **Using 'run' instead of 'call'**:
```bash
# Wrong - runs in subshell
When run my_function

# Correct - runs in current shell
When call my_function
```

3. **Function not exported**:
```bash
# In script file
my_function() {
  echo "test"
}

# Make available for testing
export -f my_function
```

### Tests pass individually but fail when run together

**Symptom**:
```bash
$ shellspec spec/test1_spec.sh  # Passes
$ shellspec spec/test2_spec.sh  # Passes
$ shellspec                      # Some fail
```

**Causes**:

1. **Shared state between tests**:
```bash
# Bad - tests affect each other
global_var="initial"

It 'test 1'
  global_var="changed"
End

It 'test 2'
  # Expects global_var="initial" but it's "changed"!
End
```

**Solution**:
```bash
# Good - reset state
BeforeEach 'reset_state() { global_var="initial"; }'

It 'test 1'
  global_var="changed"
End

It 'test 2'
  # global_var is reset to "initial"
End
```

2. **File system side effects**:
```bash
# Bad - tests create files without cleanup
It 'test 1'
  echo "data" > /tmp/test.txt
End

It 'test 2'
  # /tmp/test.txt still exists from test 1!
End
```

**Solution**:
```bash
# Good - cleanup after each test
AfterEach 'rm -f /tmp/test.txt'
```

### "When call" not capturing output

**Symptom**:
```bash
It 'outputs message'
  When call echo "test"
  The output should equal "test"  # Fails: output is empty
End
```

**Causes and Solutions**:

1. **Function redirects output**:
```bash
# Function being tested
my_function() {
  echo "result" > /dev/null  # Output is redirected!
}

# Solution: Remove redirection or capture before redirect
my_function() {
  local result="result"
  echo "${result}"
}
```

2. **Using variable assignment**:
```bash
# Wrong - output captured by assignment, not test
When call result=$(my_function)

# Correct - let ShellSpec capture output
When call my_function
```

## Assertion Failures

### Unexpected assertion failures

**Symptom**:
```bash
It 'tests output'
  When call echo "hello"
  The output should equal "hello"
End

# Failure: expected "hello" but got "hello\n"
```

**Cause**: Trailing newline

**Solutions**:

1. **Use include instead of equal**:
```bash
The output should include "hello"
```

2. **Account for newline**:
```bash
The output should equal "hello
"
```

3. **Trim output**:
```bash
trim() {
  echo -n "$1"
}

When call trim "$(echo 'hello')"
The output should equal "hello"
```

### Pattern matching not working

**Symptom**:
```bash
The output should match pattern '\d+'  # Fails
```

**Cause**: Using PCRE syntax instead of POSIX ERE

**Solution**:
```bash
# Wrong - \d is PCRE
The output should match pattern '\d+'

# Correct - [0-9] is POSIX ERE
The output should match pattern '[0-9]+'
```

### File assertions failing

**Symptom**:
```bash
The file "/tmp/test.txt" should be exist  # Fails even though file exists
```

**Causes and Solutions**:

1. **File created in subshell**:
```bash
# Wrong - runs in subshell
When run touch /tmp/test.txt
The file "/tmp/test.txt" should be exist  # Fails - file created in subshell

# Correct - run outside When block
It 'creates file'
  touch /tmp/test.txt
  The file "/tmp/test.txt" should be exist
End
```

2. **Timing issue**:
```bash
# Add small delay if needed
create_file_async /tmp/test.txt
sleep 0.1
The file "/tmp/test.txt" should be exist
```

## Mocking Issues

### Mock not being called

**Symptom**:
```bash
It 'uses mocked function'
  my_mock() {
    echo "mocked"
  }

  When call function_that_calls_my_mock
  The output should include "mocked"  # Fails - original function called
End
```

**Causes and Solutions**:

1. **Mock defined after function**:
```bash
# Wrong order
When call function_that_calls_my_mock
my_mock() { echo "mocked"; }  # Too late!

# Correct order
my_mock() { echo "mocked"; }  # Define before When
When call function_that_calls_my_mock
```

2. **Function runs in subshell**:
```bash
# Wrong - subshell doesn't see mock
When run my_function

# Correct - current shell sees mock
When call my_function
```

3. **Mock not in scope**:
```bash
# Move mock to Context level
Context 'with mock'
  my_mock() {
    echo "mocked"
  }

  It 'test 1'
    When call my_function
  End

  It 'test 2'
    When call my_function
  End
End
```

### Mock not resetting between tests

**Symptom**:
```bash
It 'test 1'
  mock_call_count=0
  my_mock() { ((mock_call_count++)); }
  When call my_function
  # mock_call_count is 1
End

It 'test 2'
  When call my_function
  # mock_call_count is 2 - not reset!
End
```

**Solution**:
```bash
BeforeEach 'reset_mock() { mock_call_count=0; }'

It 'test 1'
  my_mock() { ((mock_call_count++)); }
  When call my_function
  The variable mock_call_count should equal 1
End

It 'test 2'
  my_mock() { ((mock_call_count++)); }
  When call my_function
  The variable mock_call_count should equal 1  # Reset to 0, then incremented
End
```

## Coverage Issues

### No coverage data generated

**Symptom**:
```bash
$ shellspec --kcov
# Tests run but no coverage/ directory created
```

**Solutions**:

1. **Verify kcov installation**:
```bash
kcov --version
```

2. **Check file permissions**:
```bash
chmod +x scripts/*.sh
```

3. **Check include/exclude patterns**:
```bash
# Too restrictive exclude
--kcov-options "--exclude-pattern=/"  # Excludes everything!

# Better
--kcov-options "--exclude-pattern=/spec/,/usr/"
```

### Coverage shows 0% for all files

**Symptom**:
```bash
All files show 0% coverage
```

**Causes and Solutions**:

1. **Files not being executed**:
```bash
# Ensure tests actually call functions
It 'calls function'
  When call my_function  # This executes code
End

# vs

It 'sources file'
  When call source my_script.sh  # This doesn't execute functions!
End
```

2. **Scripts missing shebang**:
```bash
# Add shebang
#!/bin/bash

# Rest of script...
```

3. **Using --include-pattern incorrectly**:
```bash
# Wrong - too restrictive
--kcov-options "--include-pattern=/scripts/specific_file.sh"

# Better - include entire directory
--kcov-options "--include-pattern=/scripts/"
```

## Performance Issues

### Tests running slowly

**Diagnosis**:
```bash
# Measure test execution time
time shellspec
```

**Solutions**:

1. **Use fail-fast for quick feedback**:
```bash
shellspec --fail-fast
```

2. **Run tests in parallel**:
```bash
shellspec --jobs 4
```

3. **Identify slow tests**:
```bash
# Run with verbose timing
shellspec --format documentation
```

Look for tests taking >1 second.

4. **Mock slow operations**:
```bash
# Slow - makes actual network call
curl https://api.example.com/data

# Fast - mocked
curl() { echo '{"data": "mocked"}'; }
```

5. **Use smaller test data**:
```bash
# Slow - 1GB test file
create_test_file 1G

# Fast - 1KB test file
create_test_file 1K
```

## Debugging Techniques

### Enable Debug Output

**Show test execution details**:
```bash
shellspec --format debug
```

**Show shell commands**:
```bash
shellspec -x  # Equivalent to 'set -x'
```

### Inspect Test State

**Add debug output in tests**:
```bash
It 'debugs state'
  my_var="test"

  # Print variable for debugging
  echo "DEBUG: my_var=${my_var}" >&2

  When call my_function "${my_var}"
  The output should include "test"
End
```

### Run Single Test

**Run specific test file**:
```bash
shellspec spec/backup_spec.sh
```

**Run specific example**:
```bash
shellspec --example "creates backup"
```

**Focus on one test during development**:
```bash
fit 'focused test'  # Only this runs
  # Test code
End
```

Remember to remove `fit` before committing!

### Use Pending for Debugging

**Temporarily disable test**:
```bash
It 'might be causing issues'
  Pending "Debugging other tests first"
End
```

### Check ShellSpec Version

```bash
shellspec --version
```

Ensure you're using latest version:
```bash
curl -fsSL https://git.io/shellspec | sh -s -- --yes
```

## Common Error Messages

### "unexpected EOF while looking for matching"

**Error**:
```bash
spec/test_spec.sh: line 10: unexpected EOF while looking for matching `''
```

**Cause**: Unclosed quote or heredoc

**Solution**: Check for unmatched quotes
```bash
# Wrong
echo 'test

# Correct
echo 'test'
```

### "command substitution: line 0: unexpected end of file"

**Error**:
```bash
command substitution: line 0: unexpected end of file
```

**Cause**: Syntax error in command substitution

**Solution**:
```bash
# Wrong
result=$(
  echo "test"
  # Missing closing )

# Correct
result=$(
  echo "test"
)
```

### "No such file or directory"

**Error**:
```bash
spec/spec_helper.sh: No such file or directory
```

**Solutions**:

1. **Check .shellspec config**:
```bash
# .shellspec
--require spec_helper  # Looks in spec/ directory
```

2. **Create spec_helper.sh**:
```bash
touch spec/spec_helper.sh
```

3. **Use correct path**:
```bash
--require support/spec_helper  # For spec/support/spec_helper.sh
```

## Getting Help

### Run ShellSpec Self-Tests

```bash
shellspec --task fixture:example:initialize
shellspec --task fixture:example:run
```

If these fail, ShellSpec installation may be corrupted.

### Enable Trace Mode

```bash
SHELLSPEC_TRACE=1 shellspec
```

### Check ShellSpec Issues

Search existing issues:
https://github.com/shellspec/shellspec/issues

### Ask for Help

Include in your report:
1. ShellSpec version (`shellspec --version`)
2. Bash version (`bash --version`)
3. OS and version
4. Minimal reproducible example
5. Error messages
6. Expected vs actual behavior

## Best Practices for Avoiding Issues

1. **Keep tests independent** - Use BeforeEach/AfterEach
2. **Clean up resources** - Remove temp files/directories
3. **Use descriptive test names** - Easier to debug failures
4. **Run tests frequently** - Catch issues early
5. **Test one thing at a time** - Easier to isolate problems
6. **Use version control** - Revert when tests break
7. **Check ShellSpec documentation** - Stay updated on features
8. **Update regularly** - Bug fixes and improvements

## Next Steps

- Read `06-tdd-workflow.md` for preventing issues with TDD
- Read `09-ci-integration.md` for CI-specific troubleshooting
- Check ShellSpec documentation: https://github.com/shellspec/shellspec
- Join ShellSpec discussions: https://github.com/shellspec/shellspec/discussions
