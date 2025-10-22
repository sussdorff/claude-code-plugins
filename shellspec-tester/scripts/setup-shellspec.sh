#!/usr/bin/env bash
#
# Script: setup-shellspec.sh
# Description: Install ShellSpec and Kcov for testing Bash scripts
# Usage: setup-shellspec.sh [--kcov] [--prefix PATH]
# Requires: curl, git (for building kcov)

set -euo pipefail

# Declare and assign separately to avoid masking return values (SC2155)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly SCRIPT_NAME

# Default installation prefix
INSTALL_PREFIX="${HOME}/.local"
INSTALL_KCOV=false

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
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

# Display usage information
usage() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS]

Install ShellSpec testing framework and optionally Kcov for code coverage.

OPTIONS:
    --kcov              Also install Kcov for coverage analysis
    --prefix PATH       Installation prefix (default: ~/.local)
    -h, --help          Show this help message

EXAMPLES:
    # Install ShellSpec only
    $SCRIPT_NAME

    # Install ShellSpec and Kcov
    $SCRIPT_NAME --kcov

    # Install to custom location
    $SCRIPT_NAME --prefix /usr/local

ENVIRONMENT:
    After installation, add to your shell rc file:
    export PATH="\${HOME}/.local/lib/shellspec:\${PATH}"

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --kcov)
                INSTALL_KCOV=true
                shift
                ;;
            --prefix)
                if [[ -z "${2:-}" ]]; then
                    print_error "--prefix requires an argument"
                    usage
                    return 1
                fi
                INSTALL_PREFIX="$2"
                shift 2
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

# Detect operating system
detect_os() {
    local os_type
    os_type="$(uname -s)"

    case "$os_type" in
        Darwin)
            echo "macos"
            ;;
        Linux)
            echo "linux"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            echo "windows"
            ;;
        *)
            print_error "Unsupported operating system: $os_type"
            return 1
            ;;
    esac
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install ShellSpec
install_shellspec() {
    print_info "Installing ShellSpec to ${INSTALL_PREFIX}..."

    # Download and run installer
    if ! curl -fsSL https://git.io/shellspec | sh -s -- --yes --prefix="${INSTALL_PREFIX}"; then
        print_error "ShellSpec installation failed"
        return 1
    fi

    print_info "ShellSpec installed successfully"

    # Check if ShellSpec is in PATH
    local shellspec_bin="${INSTALL_PREFIX}/lib/shellspec/shellspec"
    if [[ ! -x "$shellspec_bin" ]]; then
        print_error "ShellSpec binary not found at: $shellspec_bin"
        return 1
    fi

    print_info "ShellSpec location: $shellspec_bin"

    # Display PATH setup instructions
    if [[ ":$PATH:" != *":${INSTALL_PREFIX}/lib/shellspec:"* ]]; then
        print_warn "Add ShellSpec to your PATH by adding this to your shell rc file:"
        echo "    export PATH=\"${INSTALL_PREFIX}/lib/shellspec:\${PATH}\""
    fi

    return 0
}

# Install Kcov on macOS using Homebrew
install_kcov_macos() {
    print_info "Installing Kcov on macOS..."

    if ! command_exists brew; then
        print_error "Homebrew not found. Install from https://brew.sh/"
        return 1
    fi

    if command_exists kcov; then
        print_info "Kcov already installed: $(command -v kcov)"
        return 0
    fi

    if ! brew install kcov; then
        print_error "Kcov installation via Homebrew failed"
        return 1
    fi

    print_info "Kcov installed successfully"
    return 0
}

# Install Kcov on Linux using package manager
install_kcov_linux() {
    print_info "Installing Kcov on Linux..."

    if command_exists kcov; then
        print_info "Kcov already installed: $(command -v kcov)"
        return 0
    fi

    # Try package managers
    if command_exists apt-get; then
        print_info "Using apt-get to install kcov..."
        if sudo apt-get update && sudo apt-get install -y kcov; then
            print_info "Kcov installed successfully"
            return 0
        fi
    elif command_exists dnf; then
        print_info "Using dnf to install kcov..."
        if sudo dnf install -y kcov; then
            print_info "Kcov installed successfully"
            return 0
        fi
    elif command_exists yum; then
        print_info "Using yum to install kcov..."
        if sudo yum install -y kcov; then
            print_info "Kcov installed successfully"
            return 0
        fi
    fi

    print_warn "Could not install kcov via package manager"
    print_info "Building kcov from source..."

    # Build from source as fallback
    if ! build_kcov_from_source; then
        print_error "Failed to build kcov from source"
        return 1
    fi

    return 0
}

# Build Kcov from source (fallback)
build_kcov_from_source() {
    print_info "Building kcov from source..."

    # Check dependencies
    local missing_deps=()
    for cmd in git cmake make g++; do
        if ! command_exists "$cmd"; then
            missing_deps+=("$cmd")
        fi
    done

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing build dependencies: ${missing_deps[*]}"
        print_error "Install them first, then retry"
        return 1
    fi

    # Create temporary directory
    local tmp_dir
    tmp_dir="$(mktemp -d -t kcov-build.XXXXXX)"

    # Clone and build
    (
        cd "$tmp_dir"
        if ! git clone --depth 1 https://github.com/SimonKagstrom/kcov.git; then
            print_error "Failed to clone kcov repository"
            return 1
        fi

        cd kcov
        mkdir build
        cd build

        if ! cmake -DCMAKE_INSTALL_PREFIX="${INSTALL_PREFIX}" ..; then
            print_error "CMake configuration failed"
            return 1
        fi

        if ! make -j"$(nproc 2>/dev/null || echo 1)"; then
            print_error "Build failed"
            return 1
        fi

        if ! make install; then
            print_error "Installation failed"
            return 1
        fi
    )

    # Cleanup
    rm -rf "$tmp_dir"

    print_info "Kcov built and installed successfully"
    return 0
}

# Install Kcov based on OS
install_kcov() {
    local os_type
    os_type="$(detect_os)"

    case "$os_type" in
        macos)
            install_kcov_macos
            ;;
        linux)
            install_kcov_linux
            ;;
        windows)
            print_warn "Kcov is not fully supported on Windows"
            print_info "Consider using WSL for coverage analysis"
            return 1
            ;;
        *)
            print_error "Cannot install kcov on unknown OS"
            return 1
            ;;
    esac
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."

    local shellspec_bin="${INSTALL_PREFIX}/lib/shellspec/shellspec"

    if [[ ! -x "$shellspec_bin" ]]; then
        print_error "ShellSpec not found at: $shellspec_bin"
        return 1
    fi

    print_info "ShellSpec: OK ($shellspec_bin)"

    if [[ "$INSTALL_KCOV" == "true" ]]; then
        if command_exists kcov; then
            print_info "Kcov: OK ($(command -v kcov))"
        else
            print_warn "Kcov installation was attempted but kcov command not found"
            return 1
        fi
    fi

    return 0
}

# Main installation flow
main() {
    print_info "ShellSpec Setup Installer"
    print_info "========================="

    # Parse arguments
    if ! parse_args "$@"; then
        return 1
    fi

    # Detect OS
    local os_type
    os_type="$(detect_os)"
    print_info "Detected OS: $os_type"

    # Install ShellSpec
    if ! install_shellspec; then
        print_error "ShellSpec installation failed"
        return 1
    fi

    # Install Kcov if requested
    if [[ "$INSTALL_KCOV" == "true" ]]; then
        if ! install_kcov; then
            print_warn "Kcov installation failed, but ShellSpec is installed"
            print_info "You can install kcov manually later"
        fi
    fi

    # Verify installation
    if ! verify_installation; then
        print_error "Installation verification failed"
        return 1
    fi

    print_info ""
    print_info "Installation complete!"
    print_info ""
    print_info "Next steps:"
    print_info "  1. Add ShellSpec to PATH (if not already):"
    print_info "     export PATH=\"${INSTALL_PREFIX}/lib/shellspec:\${PATH}\""
    print_info "  2. Initialize your project:"
    print_info "     ${SCRIPT_DIR}/init-test-project.sh"
    print_info "  3. Write your first test in spec/example_spec.sh"
    print_info "  4. Run tests with: shellspec"

    return 0
}

main "$@"
