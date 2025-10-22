# Coverage Setup with Kcov

This guide explains how to set up and use Kcov for code coverage reporting with ShellSpec.

## Installing Kcov

### macOS (via Homebrew)

```bash
brew install kcov
```

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install kcov
```

### Linux (from source)

```bash
git clone https://github.com/SimonKagstrom/kcov.git
cd kcov
mkdir build
cd build
cmake ..
make
sudo make install
```

## Verifying Installation

```bash
kcov --version
```

Expected output: `kcov v38` or similar (version may vary)

## Configuring ShellSpec for Coverage

### Option 1: Command Line

Run ShellSpec with kcov enabled:

```bash
shellspec --kcov
```

With custom kcov options:

```bash
shellspec --kcov --kcov-options "--exclude-pattern=/spec/,/usr/"
```

### Option 2: Configuration File

Add to `.shellspec`:

```
--kcov
--kcov-options "--exclude-pattern=/spec/,/usr/ --include-pattern=/scripts/"
```

## Understanding Coverage Reports

After running tests with coverage, Kcov generates HTML reports:

```
coverage/
├── index.html           # Main coverage report
├── script1.sh.html      # Per-file coverage
└── script2.sh.html
```

Open `coverage/index.html` in a browser to view:

- **Line coverage**: Percentage of lines executed
- **Branch coverage**: Percentage of conditional branches taken
- **Color-coded source**: Green (covered), Red (not covered), Yellow (partially covered)

## Coverage Metrics

### Line Coverage

Percentage of executable lines that were run during tests:

```
Total Lines: 100
Covered Lines: 85
Line Coverage: 85%
```

### Branch Coverage

Percentage of conditional branches (if/else/case) that were exercised:

```
Total Branches: 20
Covered Branches: 16
Branch Coverage: 80%
```

## Interpreting Coverage Results

### High Coverage (>80%)

✅ Good test coverage
✅ Most code paths are tested
✅ Likely catching most bugs

### Medium Coverage (60-80%)

⚠️ Some code paths untested
⚠️ Review uncovered areas for critical logic
⚠️ Consider adding tests for edge cases

### Low Coverage (<60%)

❌ Significant gaps in testing
❌ Many code paths untested
❌ High risk of undetected bugs

## Excluding Files from Coverage

### Using kcov-options

Exclude test files and system paths:

```bash
--kcov-options "--exclude-pattern=/spec/,/usr/,/tmp/"
```

Include only specific directories:

```bash
--kcov-options "--include-pattern=/scripts/,/lib/"
```

### Using .kcov Configuration

Create `.kcov` in project root:

```
--exclude-pattern=/spec/,/usr/,/tmp/
--include-pattern=/scripts/,/lib/
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests with Coverage

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install ShellSpec
        run: |
          curl -fsSL https://git.io/shellspec | sh -s -- -y
          sudo ln -s ${HOME}/.local/lib/shellspec/shellspec /usr/local/bin/shellspec

      - name: Install Kcov
        run: sudo apt-get update && sudo apt-get install -y kcov

      - name: Run tests with coverage
        run: shellspec --kcov

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/cobertura.xml
          fail_ci_if_error: true
```

### GitLab CI

```yaml
test:
  image: ubuntu:latest
  before_script:
    - apt-get update && apt-get install -y curl kcov
    - curl -fsSL https://git.io/shellspec | sh -s -- -y
    - export PATH="$HOME/.local/lib/shellspec:$PATH"
  script:
    - shellspec --kcov
  coverage: '/Coverage: \d+\.\d+%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura.xml
```

## Coverage Gotchas

### Subshells Not Tracked

Code in subshells may not be tracked correctly:

```bash
# This may not show coverage
result=$(complex_function_call)

# Better: call function directly
complex_function_call > output.txt
result=$(cat output.txt)
```

### Sourced Files

Ensure sourced files are in included patterns:

```bash
--kcov-options "--include-pattern=/scripts/,/lib/"
```

### Early Exits

Code after `exit` may show as uncovered even if reachable:

```bash
check_error() {
  [[ -z "$1" ]] && exit 1  # Exit prevents coverage of remaining code
  echo "Processing: $1"
}
```

## Setting Coverage Thresholds

### Enforce Minimum Coverage

In CI/CD, fail if coverage drops below threshold:

```bash
#!/bin/bash
shellspec --kcov

# Extract coverage percentage
coverage=$(grep -oP 'Coverage: \K[\d.]+' coverage/index.html)

# Fail if below threshold
if (( $(echo "$coverage < 80" | bc -l) )); then
  echo "Coverage ${coverage}% is below threshold 80%"
  exit 1
fi
```

### Coverage Ratcheting

Prevent coverage from decreasing:

```bash
# Store current coverage
echo "$coverage" > .coverage-baseline

# In CI: compare against baseline
if (( $(echo "$coverage < $baseline" | bc -l) )); then
  echo "Coverage decreased from ${baseline}% to ${coverage}%"
  exit 1
fi
```

## Best Practices

1. **Run coverage locally** before pushing to catch gaps early
2. **Review uncovered lines** to identify missing test cases
3. **Don't chase 100%** - focus on critical paths and edge cases
4. **Exclude generated code** from coverage metrics
5. **Use coverage trends** to track test quality over time
6. **Combine with mutation testing** for deeper quality assurance

## Troubleshooting

### Kcov Not Found

```
Error: kcov command not found
```

**Solution**: Install kcov (see installation section above)

### No Coverage Data Generated

```
Warning: No coverage data was collected
```

**Solutions**:
- Ensure scripts have execute permissions: `chmod +x scripts/*.sh`
- Check file patterns in `--kcov-options`
- Verify tests are actually calling functions (not just sourcing)

### Coverage Shows 0% for All Files

**Solutions**:
- Check `--include-pattern` matches your scripts
- Ensure scripts are being executed, not just sourced
- Verify shebang line is present: `#!/bin/bash`

## Resources

- Kcov Documentation: https://github.com/SimonKagstrom/kcov
- ShellSpec Coverage Guide: https://github.com/shellspec/shellspec#coverage
- Codecov Integration: https://about.codecov.io/
