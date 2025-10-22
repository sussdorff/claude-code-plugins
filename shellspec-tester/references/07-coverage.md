# Code Coverage with Kcov and ShellSpec

Complete guide to measuring and improving test coverage for Bash scripts.

## What is Code Coverage?

Code coverage measures which parts of your code are executed during tests:

- **Line Coverage**: Percentage of lines executed
- **Branch Coverage**: Percentage of conditional branches taken
- **Function Coverage**: Percentage of functions called

**Goal**: High coverage indicates thorough testing, but 100% coverage doesn't guarantee bug-free code.

## Quick Start

### 1. Install Kcov

**macOS**:
```bash
brew install kcov
```

**Ubuntu/Debian**:
```bash
sudo apt-get install kcov
```

**Verify installation**:
```bash
kcov --version
```

### 2. Run Tests with Coverage

```bash
shellspec --kcov
```

### 3. View Coverage Report

```bash
open coverage/index.html
```

## Kcov Configuration

### Command Line Options

```bash
# Basic coverage
shellspec --kcov

# With exclusions
shellspec --kcov --kcov-options "--exclude-pattern=/spec/,/usr/"

# With inclusions only
shellspec --kcov --kcov-options "--include-pattern=/scripts/"

# Specify output directory
shellspec --kcov --kcov-options "--kcov-output=./coverage-report"
```

### .shellspec Configuration

```bash
# .shellspec

# Enable kcov
--kcov

# Exclude test files and system paths
--kcov-options "--exclude-pattern=/spec/,/usr/,/tmp/"

# Include only project scripts
--kcov-options "--include-pattern=/scripts/"

# Set coverage output directory
--kcov-options "--coveralls-id=github-action-id"
```

## Reading Coverage Reports

### HTML Report Structure

```
coverage/
├── index.html              # Overall summary
├── scripts/
│   ├── backup.sh.html     # Per-file coverage
│   └── deploy.sh.html
└── coverage.json          # Machine-readable data
```

### Coverage Colors

When viewing HTML reports:

- **Green**: Line was executed
- **Red**: Line was not executed
- **Yellow**: Line was partially executed (e.g., one branch of if/else)
- **Gray**: Non-executable line (comments, blank lines)

### Example Report

```
File: scripts/backup.sh
Lines: 45/50 (90.0%)
Functions: 4/5 (80.0%)
Branches: 12/16 (75.0%)

function create_backup() {
  local source="$1"                           # Green - executed
  local backup_dir="${BACKUP_DIR}"            # Green - executed

  if [[ -d "${source}" ]]; then              # Yellow - condition tested
    tar -czf backup.tar.gz "${source}"       # Green - executed
  else                                        # Red - not executed
    echo "Error: Source not found" >&2       # Red - not executed
    return 1                                  # Red - not executed
  fi

  echo "Backup created"                       # Green - executed
}
```

**Analysis**: Error handling path (else branch) not covered by tests.

## Improving Coverage

### Identify Uncovered Lines

From coverage report, find red/yellow lines and write tests:

```bash
# Uncovered code
if [[ -z "${input}" ]]; then
  echo "Error: Input required" >&2  # RED - not covered
  return 1
fi
```

**Add test**:

```bash
It 'returns error when input is empty'
  When call process_input ""
  The stderr should include "Error: Input required"
  The status should be failure
End
```

Run coverage again - line should be green now.

### Cover All Branches

```bash
# Function with branches
validate_age() {
  local age="$1"

  if (( age < 18 )); then
    echo "minor"
  elif (( age < 65 )); then
    echo "adult"
  else
    echo "senior"
  fi
}
```

**Tests for all branches**:

```bash
Describe 'validate_age'
  It 'identifies minor'
    When call validate_age 15
    The output should equal "minor"
  End

  It 'identifies adult'
    When call validate_age 30
    The output should equal "adult"
  End

  It 'identifies senior'
    When call validate_age 70
    The output should equal "senior"
  End

  # Edge cases
  It 'handles boundary at 18'
    When call validate_age 18
    The output should equal "adult"
  End

  It 'handles boundary at 65'
    When call validate_age 65
    The output should equal "senior"
  End
End
```

### Cover Error Paths

```bash
# Function with error handling
process_file() {
  local file="$1"

  # Error path 1: File doesn't exist
  if [[ ! -f "${file}" ]]; then
    echo "Error: File not found" >&2
    return 1
  fi

  # Error path 2: File not readable
  if [[ ! -r "${file}" ]]; then
    echo "Error: File not readable" >&2
    return 1
  fi

  # Success path
  process_data "${file}"
}
```

**Tests for all paths**:

```bash
It 'processes existing readable file'
  touch "${TEST_FILE}"
  chmod +r "${TEST_FILE}"
  When call process_file "${TEST_FILE}"
  The status should be success
End

It 'returns error for missing file'
  When call process_file "/nonexistent"
  The stderr should include "File not found"
  The status should be failure
End

It 'returns error for unreadable file'
  touch "${TEST_FILE}"
  chmod -r "${TEST_FILE}"
  When call process_file "${TEST_FILE}"
  The stderr should include "File not readable"
  The status should be failure
End
```

## Coverage Metrics

### What is Good Coverage?

| Coverage | Quality | Recommendation |
|----------|---------|----------------|
| 90-100%  | Excellent | Maintain this level |
| 80-90%   | Good | Improve critical paths |
| 70-80%   | Acceptable | Add tests for uncovered areas |
| < 70%    | Needs work | Prioritize test writing |

### Focus on Critical Code

Not all code needs 100% coverage:

**High priority** (aim for 100%):
- Business logic
- Error handling
- Data validation
- Security-sensitive code

**Lower priority** (coverage optional):
- Simple getters/setters
- Print/logging statements
- Unreachable error conditions

### Example Priority Zones

```bash
# HIGH PRIORITY - Must test
validate_user_credentials() {
  # Security-sensitive - 100% coverage required
}

# HIGH PRIORITY - Must test
calculate_payment() {
  # Business logic - 100% coverage required
}

# MEDIUM PRIORITY
format_output() {
  # Presentation logic - 80%+ coverage
}

# LOW PRIORITY
print_debug() {
  # Logging only - coverage not critical
  echo "Debug: $*" >&2
}
```

## Coverage in CI/CD

### GitHub Actions

```yaml
name: Tests with Coverage

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: |
          curl -fsSL https://git.io/shellspec | sh -s -- -y
          sudo apt-get install -y kcov

      - name: Run tests with coverage
        run: |
          export PATH="$HOME/.local/lib/shellspec:$PATH"
          shellspec --kcov

      - name: Check coverage threshold
        run: |
          coverage=$(grep -oP 'Overall coverage rate.*?\K[\d.]+' coverage/index.html || echo "0")
          threshold=80
          echo "Coverage: ${coverage}%"
          if (( $(echo "$coverage < $threshold" | bc -l) )); then
            echo "Coverage ${coverage}% is below threshold ${threshold}%"
            exit 1
          fi

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/cobertura.xml
```

### GitLab CI

```yaml
test:
  image: ubuntu:latest
  before_script:
    - apt-get update
    - apt-get install -y curl kcov bc
    - curl -fsSL https://git.io/shellspec | sh -s -- -y
  script:
    - export PATH="$HOME/.local/lib/shellspec:$PATH"
    - shellspec --kcov
    - ./scripts/check-coverage-threshold.sh 80
  coverage: '/Overall coverage rate.*?(\d+\.\d+)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura.xml
```

### Coverage Threshold Script

```bash
#!/bin/bash
# scripts/check-coverage-threshold.sh

threshold="${1:-80}"
coverage_file="coverage/index.html"

if [[ ! -f "${coverage_file}" ]]; then
  echo "Error: Coverage report not found"
  exit 1
fi

# Extract coverage percentage
coverage=$(grep -oP 'Overall coverage rate.*?\K[\d.]+' "${coverage_file}" 2>/dev/null)

if [[ -z "${coverage}" ]]; then
  echo "Error: Could not extract coverage percentage"
  exit 1
fi

echo "Coverage: ${coverage}%"
echo "Threshold: ${threshold}%"

# Compare (using bc for floating point)
if (( $(echo "${coverage} < ${threshold}" | bc -l) )); then
  echo "❌ Coverage ${coverage}% is below threshold ${threshold}%"
  exit 1
else
  echo "✅ Coverage ${coverage}% meets threshold ${threshold}%"
  exit 0
fi
```

## Coverage Gotchas and Limitations

### 1. Subshells Not Always Tracked

```bash
# May not show coverage correctly
result=$(complex_function)

# Better: Direct call
complex_function > output.txt
result=$(cat output.txt)
```

### 2. Sourced Files

Ensure sourced files are included:

```bash
--kcov-options "--include-pattern=/scripts/,/lib/"
```

### 3. External Commands

Coverage doesn't track external commands:

```bash
# No coverage for curl itself
curl -s https://api.example.com/data

# But function calling curl is tracked
fetch_data() {
  curl -s https://api.example.com/data
}
```

### 4. Generated Code

Exclude generated/vendor code:

```bash
--kcov-options "--exclude-pattern=/vendor/,/generated/"
```

## Kcov Advanced Options

### Common Options

```bash
# Exclude patterns (comma-separated)
--exclude-pattern=/spec/,/usr/,/tmp/

# Include only specific patterns
--include-pattern=/scripts/,/lib/

# Output directory
--kcov-output=./my-coverage

# Merge coverage from multiple runs
--merge

# Export to Cobertura format (for CI)
--cobertura

# Set coverage threshold
--coverage-threshold=80
```

### Multiple Exclusions

```bash
--kcov-options "--exclude-pattern=/spec/,/usr/,/tmp/,/vendor/ --include-pattern=/scripts/,/lib/"
```

## Coverage-Driven Development

### Workflow

1. **Write tests** (TDD)
2. **Run with coverage**
3. **Check coverage report**
4. **Add tests for uncovered lines**
5. **Refactor** if needed
6. **Repeat**

### Example Session

```bash
# 1. Write initial tests
$ shellspec spec/backup_spec.sh
3 examples, 0 failures

# 2. Check coverage
$ shellspec --kcov spec/backup_spec.sh
$ open coverage/index.html
# Shows: 75% coverage

# 3. Identify gaps
# Report shows error handling not tested

# 4. Add tests for uncovered code
$ vim spec/backup_spec.sh
# Add tests for error cases

# 5. Re-run coverage
$ shellspec --kcov spec/backup_spec.sh
$ open coverage/index.html
# Shows: 95% coverage

# 6. Commit
$ git add spec/backup_spec.sh
$ git commit -m "Improve backup tests - 95% coverage"
```

## Interpreting Low Coverage

### Reasons for Low Coverage

1. **Missing tests** - Add tests for uncovered code
2. **Dead code** - Remove unused code
3. **Defensive code** - Error cases that may never occur
4. **Integration code** - Hard to test in unit tests

### Improving from 50% to 90%

```bash
# Current: 50% coverage
$ shellspec --kcov

# Step 1: Find critical uncovered code
$ open coverage/index.html
# Focus on red lines in core functions

# Step 2: Add tests for main success paths
# (Brings coverage to ~70%)

# Step 3: Add tests for error conditions
# (Brings coverage to ~85%)

# Step 4: Add tests for edge cases
# (Brings coverage to ~95%)

# Step 5: Remove dead code
# (Achieves 95%+ of active code)
```

## Best Practices

1. **Run coverage regularly** - Check during development
2. **Set threshold in CI** - Prevent coverage regression
3. **Focus on untested code** - Use report to guide testing
4. **Don't chase 100%** - 90-95% is usually sufficient
5. **Test behavior, not coverage** - Coverage is metric, not goal
6. **Exclude test files** - Don't measure coverage of tests themselves
7. **Track trends** - Monitor coverage over time

## Next Steps

- Read `09-ci-integration.md` for automated coverage reporting
- Read `06-tdd-workflow.md` for test-first development
- Read `10-troubleshooting.md` for coverage issues
- Check `assets/coverage_setup.md` for detailed setup
