---
name: shellspec-tester
description: Guide for testing Bash scripts using ShellSpec with TDD workflow. Use when writing tests for Bash scripts, practicing test-driven development, setting up BDD-style specs, implementing mocking/stubbing, measuring code coverage, or debugging test failures. Covers installation, assertions, test structure, mocking patterns, and CI/CD integration.
allowed_tools: Bash(shellspec *)
---

# ShellSpec Tester

## Overview

ShellSpec is a BDD (Behavior-Driven Development) testing framework for Bash scripts. This skill guides Claude Code in writing effective tests using ShellSpec with Test-Driven Development (TDD) principles. It covers everything from basic test writing to advanced patterns like mocking, coverage analysis, and CI/CD integration.

**Core capabilities**:
- Write BDD-style specifications for Bash functions and scripts
- Practice Test-Driven Development (RED-GREEN-REFACTOR cycle)
- Mock external dependencies and commands
- Measure code coverage with Kcov
- Organize test suites for maintainability
- Integrate tests into CI/CD pipelines

## When to Use This Skill

ShellSpec-Tester applies to tasks involving:

✅ **Writing tests for Bash scripts** - Creating test specifications for shell functions and scripts
✅ **Test-Driven Development** - Writing tests before implementation
✅ **Refactoring with confidence** - Adding test coverage before changing code
✅ **Mocking external dependencies** - Isolating tests from external commands, APIs, or services
✅ **Measuring test coverage** - Using Kcov to identify untested code
✅ **Setting up CI/CD** - Integrating ShellSpec into automated pipelines
✅ **Debugging test failures** - Troubleshooting failing tests or coverage issues
✅ **Improving existing test suites** - Enhancing test organization and patterns

## Quick Reference Navigator

Based on immediate testing needs, consult the appropriate reference guide:

### Getting Started
- **Quick automated setup** → Run `scripts/setup-shellspec.sh` and `scripts/init-test-project.sh`
- **First-time ShellSpec users** → Read `references/01-installation.md`
- **Initial test creation** → Check `assets/basic_spec_example.sh`
- **TDD workflow guidance** → Read `references/06-tdd-workflow.md`

### Writing Tests
- **Available assertions** → Read `references/02-assertions.md`
- **Test organization** → Read `references/03-test-structure.md`
- **Multiple scenario testing** → Check `assets/advanced_spec_example.sh`

### Advanced Patterns
- **Mocking commands and functions** → Read `references/04-mocking-and-stubbing.md`
- **Specific testing patterns** → Read `references/08-common-patterns.md`
- **Large test suite organization** → Read `references/05-test-organization.md`

### Coverage & Quality
- **Measuring coverage** → Read `references/07-coverage.md`
- **Kcov setup** → Check `assets/coverage_setup.md`
- **Improving low coverage** → Read `references/07-coverage.md` (Improving Coverage section)

### CI/CD & Automation
- **GitHub Actions integration** → Read `references/09-ci-integration.md`
- **GitLab CI / Jenkins / CircleCI** → Read `references/09-ci-integration.md`

### Troubleshooting
- **Unexpected test failures** → Read `references/10-troubleshooting.md`
- **Coverage issues** → Read `references/10-troubleshooting.md` (Coverage Issues section)
- **Performance problems** → Read `references/10-troubleshooting.md` (Performance section)

## Test-Driven Development Workflow

ShellSpec is designed for TDD. Always follow the RED-GREEN-REFACTOR cycle:

### 🔴 RED: Write Failing Test First

```bash
# spec/backup_spec.sh

Describe 'create_backup'
  It 'creates backup with timestamp'
    When call create_backup "/data"
    The output should include "Backup created:"
    The status should be success
  End
End
```

Run test: `shellspec spec/backup_spec.sh`
Expected: ❌ **FAILS** (function doesn't exist)

### 🟢 GREEN: Make Test Pass

```bash
# scripts/backup.sh

create_backup() {
  local source="$1"
  local timestamp=$(date +%Y%m%d_%H%M%S)
  local backup_file="/backups/backup_${timestamp}.tar.gz"

  tar -czf "${backup_file}" "${source}"
  echo "Backup created: ${backup_file}"
  return 0
}
```

Run test: `shellspec spec/backup_spec.sh`
Expected: ✅ **PASSES**

### ♻️ REFACTOR: Improve Code

Add error handling, extract functions, improve names - while tests stay green:

```bash
create_backup() {
  local source="$1"

  validate_source "${source}" || return $?
  create_archive "${source}" || return $?
  report_success
}
```

Run test: `shellspec spec/backup_spec.sh`
Expected: ✅ **STILL PASSES**

## Core Principle

Write production code only after creating a failing test that verifies the desired behavior. This test-first discipline drives better design and ensures comprehensive test coverage.

For detailed TDD workflow, read `references/06-tdd-workflow.md`.

## Critical Concepts

### 1. Test Structure: Describe/It Blocks

```bash
Describe 'function_name'
  It 'describes expected behavior'
    # Arrange
    input="test"

    # Act
    When call my_function "${input}"

    # Assert
    The output should equal "expected"
    The status should be success
  End
End
```

### 2. When call vs When run

- **When call** - Executes function in current shell (preferred for testing functions)
- **When run** - Executes in subshell (use for testing commands/scripts)

```bash
# Testing a function
When call my_function "arg"

# Testing a script/command
When run ./my_script.sh "arg"
```

### 3. Common Assertions

```bash
# Output assertions
The output should equal "exact match"
The output should include "substring"
The output should match pattern "regex"

# Exit code assertions
The status should be success   # Exit code 0
The status should be failure   # Exit code non-zero
The status should equal 42     # Specific exit code

# File assertions
The file "/path/to/file" should be exist
The file "/path/to/file" should be executable
The contents of file "/path/to/file" should include "text"

# Variable assertions
The variable VAR should equal "value"
The variable VAR should be defined
```

For complete assertion reference, see `references/02-assertions.md`.

### 4. Setup and Teardown

```bash
Describe 'file operations'
  # Run before each test
  BeforeEach 'setup() { TEST_FILE=$(mktemp); }'

  # Run after each test
  AfterEach 'cleanup() { rm -f "${TEST_FILE}"; }'

  It 'test 1'
    # TEST_FILE exists and is clean
  End

  It 'test 2'
    # TEST_FILE is recreated fresh
  End
End
```

### 5. Mocking External Dependencies

```bash
Describe 'fetch_data'
  # Mock curl command
  curl() {
    echo '{"status": "ok", "data": [1,2,3]}'
    return 0
  }

  It 'processes API response'
    When call fetch_data "https://api.example.com/data"
    The output should include '"status": "ok"'
  End
End
```

For comprehensive mocking patterns, see `references/04-mocking-and-stubbing.md` and `assets/mock_spec_example.sh`.

### 6. Parameterized Tests

```bash
Describe 'validate_email'
  Parameters
    "user@example.com"     success
    "test@domain.com"      success
    "invalid.email"        failure
    "@no-local.com"        failure
  End

  Example "email $1 should be $2"
    When call validate_email "$1"
    The status should be "$2"
  End
End
```

## Project Setup Quick Start

### Automated Setup (Recommended)

Use the provided automation scripts for quick setup:

```bash
# 1. Install ShellSpec (and optionally Kcov for coverage)
bash scripts/setup-shellspec.sh --kcov

# 2. Initialize your project
bash scripts/init-test-project.sh
```

### Manual Setup (Alternative)

If you prefer manual installation:

### 1. Install ShellSpec

```bash
curl -fsSL https://git.io/shellspec | sh
export PATH="${HOME}/.local/lib/shellspec:${PATH}"
```

### 2. Initialize Project Structure

```bash
mkdir -p spec scripts
cp assets/.shellspec .
cp assets/spec_helper.sh spec/
```

### 3. Create Your First Test

```bash
cat > spec/example_spec.sh <<'EOF'
Describe 'greet'
  greet() { echo "Hello, $1!"; }

  It 'greets with name'
    When call greet "World"
    The output should equal "Hello, World!"
  End
End
EOF
```

### 4. Run Tests

```bash
shellspec
```

For detailed installation, see `references/01-installation.md`.

## Common Workflows

### Writing a New Feature (TDD Approach)

1. **Write failing test** describing desired behavior
2. **Run test** - confirm it fails for the right reason
3. **Write minimal code** to make test pass
4. **Run test** - confirm it passes
5. **Refactor** code while keeping tests green
6. **Repeat** for next behavior

### Adding Tests to Existing Code

1. **Start with high-level behavior** - test the main success path
2. **Add error condition tests** - test failure modes
3. **Add edge case tests** - boundaries, empty input, null values
4. **Check coverage** - identify gaps: `shellspec --kcov`
5. **Fill coverage gaps** - add tests for uncovered lines

### Debugging Test Failures

1. **Run specific test** - `shellspec spec/failing_spec.sh`
2. **Enable debug output** - `shellspec -x`
3. **Add debug statements** - `echo "DEBUG: var=$var" >&2`
4. **Check test assumptions** - verify mocks, fixtures, setup
5. **Isolate the issue** - use `fit` to focus on failing test
6. **Check troubleshooting guide** - `references/10-troubleshooting.md`

## Testing Patterns by Scenario

### Testing Functions with Parameters

```bash
It 'accepts multiple parameters'
  When call my_function "arg1" "arg2" "arg3"
  The output should include "arg1"
End
```

See `references/08-common-patterns.md` for more patterns.

### Testing Error Conditions

```bash
It 'returns error for missing file'
  When call process_file "/nonexistent"
  The stderr should include "Error: File not found"
  The status should be failure
End
```

### Testing File Operations

```bash
It 'creates output file'
  When call generate_report "${TEST_DIR}/report.txt"
  The file "${TEST_DIR}/report.txt" should be exist
  The contents of file "${TEST_DIR}/report.txt" should include "Report"
End
```

### Testing stdout vs stderr

```bash
It 'outputs to stdout and logs to stderr'
  When call process_data "input"
  The output should equal "processed data"
  The stderr should include "[INFO] Processing"
End
```

For comprehensive patterns, see `references/08-common-patterns.md`.

## Coverage Analysis

### Running Tests with Coverage

```bash
shellspec --kcov
open coverage/index.html
```

### Interpreting Results

- **Green lines** - Executed during tests ✅
- **Red lines** - Not executed (need tests) ❌
- **Yellow lines** - Partially executed (some branches not tested) ⚠️

### Coverage Goals

| Coverage | Quality | Action |
|----------|---------|--------|
| 90-100%  | Excellent | Maintain |
| 80-90%   | Good | Improve critical paths |
| 70-80%   | Acceptable | Add tests |
| < 70%    | Needs work | Prioritize testing |

For detailed coverage guide, see `references/07-coverage.md` and `assets/coverage_setup.md`.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install ShellSpec
        run: curl -fsSL https://git.io/shellspec | sh -s -- -y
      - name: Run tests
        run: ${HOME}/.local/lib/shellspec/shellspec
      - name: Coverage
        run: |
          sudo apt-get install -y kcov
          ${HOME}/.local/lib/shellspec/shellspec --kcov
```

For GitLab CI, Jenkins, CircleCI, and more, see `references/09-ci-integration.md`.

## Best Practices

### Recommended Practices

- **Write tests first** (TDD) - Drives better design
- **Test behavior, not implementation** - Tests should survive refactoring
- **Keep tests independent** - No shared state between tests
- **Use descriptive names** - Test name should explain what's being tested
- **Mock external dependencies** - Fast, reliable tests
- **Clean up resources** - Use AfterEach for temp files/directories
- **Test error paths** - Failures are important behavior
- **Run tests frequently** - Quick feedback loop

### Practices to Avoid

- **Avoid testing implementation details** - Test public API only
- **Avoid shared state between tests** - Each test should be isolated
- **Avoid skipping refactoring** - Keep test code clean too
- **Avoid ignoring failing tests** - Fix or remove, never skip
- **Avoid chasing 100% coverage blindly** - Focus on critical code
- **Avoid testing external libraries** - Trust them, mock them
- **Avoid writing tests after code** - TDD is more effective

## Available Resources

### Scripts (Automation)

Use these scripts to automate setup and initialization:

- **`setup-shellspec.sh`** - Install ShellSpec and Kcov (supports macOS, Linux, WSL)
  - `--kcov` flag to also install code coverage tool
  - `--prefix PATH` to customize installation location
  - Detects OS and uses appropriate package manager
- **`init-test-project.sh`** - Initialize test structure in your project
  - Creates `spec/` directory with spec_helper.sh
  - Copies `.shellspec` configuration
  - Creates example test file
  - `--path DIR` to initialize in specific directory
  - `--force` to overwrite existing files

### Assets (Templates & Examples)

Copy these files to your project (or use `init-test-project.sh` to automate):

- **`.shellspec`** - ShellSpec configuration template
- **`spec_helper.sh`** - Common test setup and utilities
- **`basic_spec_example.sh`** - Simple test patterns (functions, assertions, exit codes)
- **`advanced_spec_example.sh`** - Advanced patterns (mocking, data-driven, stderr/stdout)
- **`mock_spec_example.sh`** - Comprehensive mocking examples
- **`coverage_setup.md`** - Kcov installation and configuration guide

### References (Deep Dives)

Read these for detailed information:

1. **`01-installation.md`** - Installing ShellSpec and Kcov, project setup
2. **`02-assertions.md`** - All assertion types and matchers
3. **`03-test-structure.md`** - Describe/It blocks, hooks, organization
4. **`04-mocking-and-stubbing.md`** - Isolating tests, mocking patterns
5. **`05-test-organization.md`** - Project structure, shared examples, fixtures
6. **`06-tdd-workflow.md`** - RED-GREEN-REFACTOR workflow, TDD principles
7. **`07-coverage.md`** - Code coverage with Kcov, improving coverage
8. **`08-common-patterns.md`** - Testing patterns for common scenarios
9. **`09-ci-integration.md`** - GitHub Actions, GitLab CI, Jenkins, etc.
10. **`10-troubleshooting.md`** - Common issues and solutions

## Skill Usage Examples

### Example 1: User asks to write tests for a function

**User**: "Help me write tests for this backup function"

**Recommended workflow**:
1. Check if ShellSpec is installed (`references/01-installation.md`)
2. Review the function to understand its behavior
3. Start with TDD approach (`references/06-tdd-workflow.md`)
4. Write test for main success path
5. Add tests for error conditions
6. Use appropriate assertions (`references/02-assertions.md`)
7. Mock external commands if needed (`references/04-mocking-and-stubbing.md`)

### Example 2: User wants to set up testing from scratch

**User**: "Set up ShellSpec testing for my Bash project"

**Recommended workflow**:
1. Run `scripts/setup-shellspec.sh --kcov` to install ShellSpec and Kcov
2. Run `scripts/init-test-project.sh` to initialize project structure
3. Verify installation and show created files
4. Show basic test example from the created `spec/example_spec.sh`
5. Explain how to source their scripts in `spec/spec_helper.sh`
6. Explain TDD workflow (`references/06-tdd-workflow.md`)

**Alternative (manual setup)**:
1. Guide through installation (`references/01-installation.md`)
2. Copy configuration from `assets/.shellspec`
3. Set up spec directory with `assets/spec_helper.sh`
4. Show basic test example from `assets/basic_spec_example.sh`
5. Create first test together
6. Explain TDD workflow (`references/06-tdd-workflow.md`)

### Example 3: User has failing tests

**User**: "My tests are failing and I don't know why"

**Recommended workflow**:
1. Ask for error message
2. Consult `references/10-troubleshooting.md`
3. Check common issues (mocking, assertions, file paths)
4. Enable debug mode: `shellspec -x`
5. Help isolate the issue
6. Fix and verify

### Example 4: User wants coverage reporting

**User**: "How do I measure code coverage?"

**Recommended workflow**:
1. Check if Kcov is installed (`assets/coverage_setup.md`)
2. Configure `.shellspec` with `--kcov` option
3. Run tests with coverage: `shellspec --kcov`
4. Review coverage report
5. Identify uncovered lines (`references/07-coverage.md`)
6. Guide writing tests for gaps

## Additional Notes

### ShellSpec Advantages Over Alternative Testing Frameworks

ShellSpec offers several advantages compared to BATS, shUnit2, and other shell testing frameworks:

- BDD-style syntax (more readable)
- Built-in mocking capabilities
- Better coverage integration
- Active maintenance
- Parameterized tests
- Rich assertion library

### Running ShellSpec in a ZSH Environment

**Important**: Understand the three layers of shell usage when testing:

#### Layer 1: Command Execution Shell (Your Terminal)

You can run ShellSpec from any shell, including ZSH:

```zsh
# Running from your ZSH terminal - this works fine
shellspec spec/
shellspec --kcov
shellspec spec/my_test_spec.sh
```

**Takeaway**: Use your preferred shell (ZSH) to execute the `shellspec` command.

#### Layer 2: Test File Syntax (Always Bash)

**Test spec files are ALWAYS written in Bash syntax**, regardless of:
- What shell you use to run shellspec
- What shell your code-under-test uses

```bash
# spec/example_spec.sh - Written in BASH syntax
# shellcheck shell=bash

Describe 'testing arrays'
  It 'uses Bash 0-based array indexing'
    local arr=("first" "second" "third")

    # Use Bash syntax: 0-based indexing, Bash quoting rules
    When call echo "${arr[0]}"
    The output should equal "first"
  End
End
```

**Common pitfall**: Don't use ZSH patterns in test files:

```bash
# ❌ WRONG - This is ZSH thinking in a Bash test file
arr=("first" "second")
echo "${arr[1]}"  # Expects "first" (ZSH is 1-based) but gets "second" (Bash is 0-based)

# ✅ CORRECT - Use Bash patterns
arr=("first" "second")
echo "${arr[0]}"  # Bash: first element is at index 0
```

**Takeaway**: Write test specs using Bash syntax (0-based arrays, Bash word splitting, Bash quoting rules).

#### Layer 3: Code Under Test Execution

This is where `--shell` configuration matters.

**Testing Bash scripts** (default):
```bash
# scripts/my-bash-script.sh
#!/usr/bin/env bash
my_function() {
    local arr=("a" "b")
    echo "${arr[0]}"  # Bash: 0-based
}
```

```bash
# spec/my_bash_script_spec.sh - Test file in Bash syntax
Describe 'my_function'
  It 'returns first element'
    When call my_function
    The output should equal "a"
  End
End
```

ShellSpec executes `my_function` using Bash (default behavior).

**Testing ZSH scripts** (requires configuration):
```zsh
# scripts/my-zsh-script.zsh
#!/usr/bin/env zsh
my_zsh_function() {
    local arr=("a" "b")
    echo "${arr[1]}"  # ZSH: 1-based indexing
}
```

```bash
# spec/my_zsh_script_spec.sh - Test file STILL in Bash syntax!
# But configure ShellSpec to execute code-under-test with ZSH

Describe 'my_zsh_function'
  It 'returns first element using ZSH indexing'
    When call my_zsh_function
    The output should equal "a"  # ZSH function uses arr[1] for first element
  End
End
```

**Configure ShellSpec to use ZSH for execution**:
```bash
# .shellspec
--shell zsh
```

Or per-file:
```bash
# spec/my_zsh_script_spec.sh
#shellspec shell:zsh

Describe 'my_zsh_function'
  # ...
End
```

**Takeaway**:
- Test files = Always Bash syntax
- Code execution = Bash by default, ZSH with `--shell zsh`
- The `--shell` flag controls HOW your code-under-test runs, NOT how test files are parsed

**Important Note About Shebangs**:
- When you execute a script directly (e.g., `./my-script.sh`), the shebang IS honored
- When ShellSpec tests functions, it **sources** your script file, so the shebang is **ignored**
- This is why the `--shell` configuration flag exists - it tells ShellSpec what shell to use when sourcing and executing your functions
- Example: A script with `#!/usr/bin/env bash` tested by ShellSpec with `--shell zsh` will run in ZSH, not Bash

#### Summary Table

| Layer | Shell Used | Syntax Rules | Configuration |
|-------|-----------|--------------|---------------|
| **Command execution** (running shellspec) | Your choice (ZSH is fine) | Your shell's syntax | N/A |
| **Test file syntax** (spec files) | Always Bash | Bash patterns only | N/A |
| **Code-under-test execution** | Bash (default) or ZSH | Depends on `--shell` flag, NOT shebang* | `.shellspec --shell zsh` |

\* ShellSpec sources files to test functions, so shebangs are ignored. Use `--shell` to control execution environment.

#### Practical Examples

**Scenario 1: ZSH user testing Bash scripts** (most common)
```zsh
# From ZSH terminal
shellspec spec/  # ✅ Works fine
```
- Test files: Bash syntax ✅
- Code runs in: Bash ✅
- No special configuration needed ✅

**Scenario 2: ZSH user testing ZSH scripts**
```zsh
# From ZSH terminal
shellspec spec/  # ✅ Works fine
```
- Test files: Bash syntax ✅
- Code runs in: ZSH ⚠️ (requires `--shell zsh` in `.shellspec`)
- Configuration needed: Add `--shell zsh` to `.shellspec`

### Integration with Other Skills

- **bash-best-practices** - For Bash syntax and patterns
- **zsh-best-practices** - For Zsh-specific patterns
- **CI/CD skills** - For pipeline integration

## Getting Help

If encountering issues not covered in this skill:

1. Check `references/10-troubleshooting.md` first
2. Search ShellSpec issues: https://github.com/shellspec/shellspec/issues
3. Review ShellSpec documentation: https://shellspec.info/
4. Ask in ShellSpec discussions: https://github.com/shellspec/shellspec/discussions

---

**Remember**: Test-Driven Development is a discipline. Write the test first, watch it fail, make it pass, then refactor. This skill is here to guide you through that process with ShellSpec.
