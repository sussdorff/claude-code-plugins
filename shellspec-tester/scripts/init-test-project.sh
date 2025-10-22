#!/usr/bin/env bash
#
# Script: init-test-project.sh
# Description: Initialize ShellSpec test structure for a Bash project
# Usage: init-test-project.sh [--path PROJECT_DIR] [--force]
# Requires: None (copies from skill assets)

set -euo pipefail

# Declare and assign separately to avoid masking return values (SC2155)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly SCRIPT_NAME
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly SKILL_DIR

# Default values
PROJECT_DIR="$(pwd)"
FORCE=false

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

print_step() {
    echo -e "${BLUE}==>${NC} $*"
}

# Display usage information
usage() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS]

Initialize ShellSpec test structure in a Bash project.

OPTIONS:
    --path DIR          Project directory (default: current directory)
    --force             Overwrite existing files
    -h, --help          Show this help message

CREATED STRUCTURE:
    PROJECT_DIR/
    ├── .shellspec              # ShellSpec configuration
    ├── spec/                   # Test directory
    │   ├── spec_helper.sh      # Common test utilities
    │   └── example_spec.sh     # Example test (basic)
    └── scripts/                # Scripts to test (created if missing)

EXAMPLES:
    # Initialize in current directory
    $SCRIPT_NAME

    # Initialize in specific directory
    $SCRIPT_NAME --path /path/to/project

    # Force overwrite existing files
    $SCRIPT_NAME --force

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --path)
                if [[ -z "${2:-}" ]]; then
                    print_error "--path requires an argument"
                    usage
                    return 1
                fi
                PROJECT_DIR="$2"
                shift 2
                ;;
            --force)
                FORCE=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                usage
                return 1
                ;;
        esac
    done
}

# Check if file exists and handle --force
check_file_exists() {
    local file="$1"

    if [[ -f "$file" ]]; then
        if [[ "$FORCE" == "true" ]]; then
            print_warn "Overwriting existing file: $file"
            return 1  # Signal to overwrite
        else
            print_warn "File already exists (use --force to overwrite): $file"
            return 0  # Signal to skip
        fi
    fi

    return 1  # Signal to create
}

# Create directory if it doesn't exist
ensure_directory() {
    local dir="$1"

    if [[ ! -d "$dir" ]]; then
        print_info "Creating directory: $dir"
        mkdir -p "$dir"
    else
        print_info "Directory exists: $dir"
    fi
}

# Copy asset file to project
copy_asset() {
    local asset_name="$1"
    local dest_path="$2"
    local asset_path="${SKILL_DIR}/assets/${asset_name}"

    if [[ ! -f "$asset_path" ]]; then
        print_error "Asset not found: $asset_path"
        return 1
    fi

    if check_file_exists "$dest_path"; then
        return 0  # Skip
    fi

    print_info "Creating: $dest_path"
    cp "$asset_path" "$dest_path"
    return 0
}

# Create example spec file
create_example_spec() {
    local spec_file="${PROJECT_DIR}/spec/example_spec.sh"

    if check_file_exists "$spec_file"; then
        return 0  # Skip
    fi

    print_info "Creating: $spec_file"

    cat > "$spec_file" <<'EOF'
# Example ShellSpec Test
# This is a basic example to get you started with ShellSpec testing

# shellcheck shell=bash

Describe 'example_function'
  # Define a simple function to test
  example_function() {
    local input="$1"
    echo "Hello, ${input}!"
    return 0
  }

  It 'outputs greeting with input'
    When call example_function "World"
    The output should equal "Hello, World!"
  End

  It 'returns success exit code'
    When call example_function "Test"
    The status should be success
  End

  Context 'with empty input'
    It 'handles empty string'
      When call example_function ""
      The output should equal "Hello, !"
    End
  End
End

# Next steps:
# 1. Replace example_function with your actual functions
# 2. Source your script files in spec_helper.sh
# 3. Write tests following the TDD workflow (RED-GREEN-REFACTOR)
# 4. Run tests with: shellspec
# 5. Check coverage with: shellspec --kcov
EOF

    return 0
}

# Create README for spec directory
create_spec_readme() {
    local readme_file="${PROJECT_DIR}/spec/README.md"

    if check_file_exists "$readme_file"; then
        return 0  # Skip
    fi

    print_info "Creating: $readme_file"

    cat > "$readme_file" <<'EOF'
# ShellSpec Tests

This directory contains ShellSpec tests for the project.

## Running Tests

```bash
# Run all tests
shellspec

# Run specific test file
shellspec spec/example_spec.sh

# Run with coverage
shellspec --kcov

# Run with verbose output
shellspec -f documentation
```

## Test Structure

- `spec_helper.sh` - Common setup and utilities loaded before each test
- `*_spec.sh` - Test specification files

## Writing Tests

Follow the TDD workflow:

1. **RED**: Write a failing test
2. **GREEN**: Write minimal code to make it pass
3. **REFACTOR**: Improve the code while keeping tests green

### Example Test

```bash
Describe 'my_function'
  It 'does something useful'
    When call my_function "input"
    The output should equal "expected output"
    The status should be success
  End
End
```

## Resources

- ShellSpec documentation: https://shellspec.info/
- Project skill: Check the shellspec-tester skill for comprehensive guidance
EOF

    return 0
}

# Validate project directory
validate_project_dir() {
    if [[ ! -d "$PROJECT_DIR" ]]; then
        print_error "Project directory does not exist: $PROJECT_DIR"
        return 1
    fi

    if [[ ! -w "$PROJECT_DIR" ]]; then
        print_error "Project directory is not writable: $PROJECT_DIR"
        return 1
    fi

    return 0
}

# Check if ShellSpec is installed
check_shellspec_installed() {
    if ! command -v shellspec >/dev/null 2>&1; then
        print_warn "ShellSpec not found in PATH"
        print_info "Install it with: ${SCRIPT_DIR}/setup-shellspec.sh"
        return 1
    fi

    local shellspec_version
    shellspec_version="$(shellspec --version 2>/dev/null | head -1 || echo 'unknown')"
    print_info "ShellSpec found: $shellspec_version"
    return 0
}

# Display next steps
show_next_steps() {
    print_info ""
    print_info "Project initialized successfully!"
    print_info ""
    print_info "Next steps:"
    print_info "  1. Review the generated files in ${PROJECT_DIR}"
    print_info "  2. Update spec/spec_helper.sh to source your script files"
    print_info "  3. Replace spec/example_spec.sh with real tests"
    print_info "  4. Run tests with: shellspec"
    print_info ""
    print_info "TDD Workflow:"
    print_info "  RED    -> Write failing test"
    print_info "  GREEN  -> Make it pass"
    print_info "  REFACTOR -> Improve code"
    print_info ""
}

# Main initialization flow
main() {
    print_step "ShellSpec Project Initializer"
    print_info "=============================="

    # Parse arguments
    if ! parse_args "$@"; then
        return 1
    fi

    # Validate project directory
    if ! validate_project_dir; then
        return 1
    fi

    # Check ShellSpec installation (warning only)
    check_shellspec_installed || true

    # Resolve absolute path
    PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"
    print_info "Initializing project at: $PROJECT_DIR"

    # Create directory structure
    print_step "Creating directory structure"
    ensure_directory "${PROJECT_DIR}/spec"
    ensure_directory "${PROJECT_DIR}/scripts"

    # Copy configuration files
    print_step "Setting up configuration files"
    copy_asset ".shellspec" "${PROJECT_DIR}/.shellspec"
    copy_asset "spec_helper.sh" "${PROJECT_DIR}/spec/spec_helper.sh"

    # Create example files
    print_step "Creating example files"
    create_example_spec
    create_spec_readme

    # Display next steps
    show_next_steps

    return 0
}

main "$@"
