# ShellSpec Installation and Setup

Complete guide to installing ShellSpec and Kcov, and setting up your first testing project.

## Installing ShellSpec

### Method 1: Quick Install (Recommended)

```bash
curl -fsSL https://git.io/shellspec | sh
```

This installs ShellSpec to `~/.local/lib/shellspec/`

Add to PATH in your shell RC file (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export PATH="$HOME/.local/lib/shellspec:$PATH"
```

### Method 2: Homebrew (macOS/Linux)

```bash
brew install shellspec
```

### Method 3: Manual Installation

```bash
git clone https://github.com/shellspec/shellspec.git
cd shellspec
sudo make install
```

### Method 4: Project-Local Installation

Install ShellSpec within your project (doesn't require sudo):

```bash
cd your-project
curl -fsSL https://git.io/shellspec | sh -s -- --prefix .
```

Add to your project's scripts:

```json
{
  "scripts": {
    "test": "./lib/shellspec/shellspec"
  }
}
```

## Verifying Installation

```bash
shellspec --version
```

Expected output: `ShellSpec 0.28.1` or similar

Run self-tests to ensure everything works:

```bash
shellspec --task fixture:example:initialize
shellspec --task fixture:example:run
```

## Installing Kcov (for Coverage)

### macOS

```bash
brew install kcov
```

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install kcov
```

### Fedora/RHEL

```bash
sudo dnf install kcov
```

### From Source

```bash
git clone https://github.com/SimonKagstrom/kcov.git
cd kcov
mkdir build && cd build
cmake ..
make
sudo make install
```

Verify kcov installation:

```bash
kcov --version
```

## Project Setup

### 1. Create Project Structure

```bash
your-project/
├── scripts/              # Scripts to test
│   ├── backup.sh
│   └── utils.sh
├── spec/                 # Test files
│   ├── spec_helper.sh   # Shared test setup
│   ├── backup_spec.sh   # Tests for backup.sh
│   └── utils_spec.sh    # Tests for utils.sh
└── .shellspec           # Configuration
```

Create directories:

```bash
mkdir -p spec scripts
```

### 2. Initialize ShellSpec Configuration

Create `.shellspec` configuration file:

```bash
cat > .shellspec << 'EOF'
# Require spec_helper before each spec
--require spec_helper

# Output format (documentation, tap, junit, etc.)
--format documentation

# Enable colored output
--color

# Optional: Enable coverage with Kcov
# --kcov
# --kcov-options "--exclude-pattern=/spec/,/usr/"
EOF
```

### 3. Create spec_helper.sh

```bash
cat > spec/spec_helper.sh << 'EOF'
# Spec Helper - Common setup for all tests

# Add scripts directory to PATH
SCRIPT_DIR="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}/scripts"
export PATH="${SCRIPT_DIR}:${PATH}"

# Source functions to test
# Adjust paths as needed
# source "${SCRIPT_DIR}/backup.sh"
# source "${SCRIPT_DIR}/utils.sh"
EOF
```

### 4. Create Your First Test

```bash
cat > spec/example_spec.sh << 'EOF'
# Example Test Specification

Describe 'example test'
  # Simple function to test
  greet() {
    echo "Hello, $1!"
  }

  It 'greets with name'
    When call greet "World"
    The output should equal "Hello, World!"
  End

  It 'succeeds'
    When call greet "Test"
    The status should be success
  End
End
EOF
```

### 5. Run Your Tests

```bash
shellspec
```

Expected output:

```
example test
  greets with name
  succeeds

Finished in 0.12345 seconds (files took 0.23456 seconds to load)
2 examples, 0 failures
```

## Advanced Configuration Options

### .shellspec Configuration Reference

```bash
# Require files before tests
--require spec_helper
--require custom_helpers

# Output formats
--format documentation    # Detailed output (default)
--format tap             # TAP format
--format junit           # JUnit XML format
--format progress        # Dots (RSpec style)

# Output control
--color                  # Colored output
--no-color              # Disable colors
--quiet                 # Minimal output
--verbose               # Detailed output

# Test execution
--jobs 4                # Run tests in parallel (4 workers)
--random                # Random execution order
--fail-fast             # Stop on first failure
--fail-no-examples      # Fail if no examples found
--dry-run              # List tests without running

# Coverage
--kcov                          # Enable Kcov coverage
--kcov-options "OPTIONS"        # Pass options to Kcov

# Filtering
--example "PATTERN"             # Run examples matching pattern
--tag TAG                       # Run examples with tag
--focus                         # Run only focused examples (fit/fdescribe)

# Shell selection
--shell bash                    # Use bash (default: auto-detect)
--shell sh                      # Use sh
```

### Environment Variables

```bash
# Set shell to use
export SHELLSPEC_SHELL=bash

# Set number of parallel jobs
export SHELLSPEC_JOBS=4

# Enable kcov
export SHELLSPEC_KCOV=1

# Custom spec directory
export SHELLSPEC_SPECDIR=tests
```

## Project Directory Conventions

### Standard Layout

```bash
project/
├── scripts/              # Production scripts
│   ├── lib/             # Shared libraries
│   └── bin/             # Executable scripts
├── spec/                 # Test specifications
│   ├── support/         # Test support files
│   │   ├── spec_helper.sh
│   │   └── fixtures/    # Test data
│   ├── lib/             # Tests for lib/
│   └── bin/             # Tests for bin/
├── coverage/            # Coverage reports (generated)
└── .shellspec          # Configuration
```

### Alternative Layout (spec alongside code)

```bash
project/
├── src/
│   ├── backup.sh
│   └── backup_spec.sh   # Test next to implementation
├── lib/
│   ├── utils.sh
│   └── utils_spec.sh
└── .shellspec
```

Configure spec directory in `.shellspec`:

```bash
--spec-dir src
--spec-dir lib
```

## Troubleshooting Installation

### "shellspec: command not found"

**Solution**: Add to PATH:

```bash
export PATH="$HOME/.local/lib/shellspec:$PATH"
```

Add to `~/.bashrc` or `~/.zshrc` to persist.

### Permission Denied

**Solution**: Make shellspec executable:

```bash
chmod +x ~/.local/lib/shellspec/shellspec
```

### Kcov Not Working

**Check installation**:

```bash
which kcov
kcov --version
```

**Check .shellspec** has correct options:

```bash
--kcov
--kcov-options "--exclude-pattern=/spec/"
```

### Tests Not Found

**Ensure** spec files end with `_spec.sh`:

```bash
# Good
backup_spec.sh
utils_spec.sh

# Bad - won't be discovered
test_backup.sh
backup.test.sh
```

**Check** spec directory:

```bash
shellspec --list
```

## Next Steps

- Read `02-assertions.md` for assertion types
- Read `03-test-structure.md` for organizing tests
- Read `06-tdd-workflow.md` for TDD best practices
- Check example specs in `assets/basic_spec_example.sh`

## Resources

- ShellSpec GitHub: https://github.com/shellspec/shellspec
- ShellSpec Documentation: https://shellspec.info/
- Quick Reference: https://github.com/shellspec/shellspec#dsl
- Examples: https://github.com/shellspec/shellspec/tree/master/examples
