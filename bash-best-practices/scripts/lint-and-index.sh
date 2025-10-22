#!/usr/bin/env bash
# Combined linting and indexing workflow
# Always run both ShellCheck and function analysis together to keep extract.json synchronized

set -euo pipefail

# Bash version check - Require 4.0+ for mapfile support
if [[ "${BASH_VERSINFO[0]}" -lt 4 ]]; then
    cat >&2 << 'EOF'
Error: Bash 4.0+ required (current version: ${BASH_VERSION})

This script requires Bash 4.0+ for mapfile/readarray support.
Bash 5.x is recommended for best performance and features.

Upgrade instructions:
  macOS:    brew install bash  (installs latest 5.x)
  Linux:    apt-get install bash  (Debian/Ubuntu)
            yum install bash      (RHEL/CentOS)
  Windows:  Update Git Bash or use WSL (usually already 4.4+)

After installing via Homebrew on macOS:
  - New shell: /opt/homebrew/bin/bash (Apple Silicon)
            or /usr/local/bin/bash (Intel)
  - Verify:  /opt/homebrew/bin/bash --version
  - Current: /bin/bash (system default, leave untouched)

EOF
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
readonly ANALYZER="${SCRIPT_DIR}/analyze-shell-functions.py"

show_help() {
    cat << 'EOF'
Lint and Index - Combined Workflow
===================================

DESCRIPTION:
    Runs ShellCheck for linting AND regenerates extract.json for function metadata.
    Keeping these synchronized ensures:
    - extract.json reflects current codebase structure
    - ShellCheck validates all indexed functions
    - No stale metadata after code changes

USAGE:
    bash lint-and-index.sh --path <directory> [--severity <level>] [--fix]

    --path DIR          Directory to analyze and lint (required)
    --severity LEVEL    ShellCheck severity: error, warning, info, style (default: warning)
    --fix               Auto-fix ShellCheck issues where possible
    --help              Show this help message

WORKFLOW:
    1. Run ShellCheck on all .sh/.bash files
    2. Report any linting issues
    3. Regenerate extract.json with current function metadata
    4. Report summary

OUTPUT:
    - ShellCheck results (stderr/stdout)
    - extract.json in analyzed directory
    - Summary of both operations

EXAMPLES:
    # Lint and index current directory
    bash lint-and-index.sh --path .

    # Only show errors, but index everything
    bash lint-and-index.sh --path ./scripts --severity error

    # Auto-fix issues and regenerate index
    bash lint-and-index.sh --path . --fix

WHY COUPLE THESE OPERATIONS:
    - Code changes invalidate extract.json
    - ShellCheck runs indicate code was modified
    - Always keeping them synchronized avoids stale metadata
    - Claude Code workflow: lint → index → discover → extract

EOF
}

# Parse arguments
TARGET_PATH=""
SEVERITY="warning"
AUTO_FIX=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --path)
            TARGET_PATH="$2"
            shift 2
            ;;
        --severity)
            SEVERITY="$2"
            shift 2
            ;;
        --fix)
            AUTO_FIX=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Validate inputs
if [[ -z "$TARGET_PATH" ]]; then
    echo "Error: --path is required" >&2
    show_help
    exit 1
fi

if [[ ! -d "$TARGET_PATH" ]]; then
    echo "Error: Path does not exist: $TARGET_PATH" >&2
    exit 1
fi

# Check for required tools
if ! command -v shellcheck &> /dev/null; then
    echo "Error: shellcheck not found. Install with: brew install shellcheck" >&2
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "Error: jq not found. Install with: brew install jq" >&2
    exit 1
fi

if ! command -v uv &> /dev/null; then
    echo "Error: uv not found. Install with: brew install uv" >&2
    exit 1
fi

echo "========================================" >&2
echo "Bash Lint and Index Workflow" >&2
echo "========================================" >&2
echo "Target: $TARGET_PATH" >&2
echo "" >&2

# Step 1: ShellCheck
echo "Step 1: Running ShellCheck (severity: $SEVERITY)..." >&2
echo "----------------------------------------" >&2

# Find all shell files
mapfile -t shell_files < <(find "$TARGET_PATH" -type f \( -name "*.sh" -o -name "*.bash" \) 2>/dev/null)

if [[ ${#shell_files[@]} -eq 0 ]]; then
    echo "No shell files found in: $TARGET_PATH" >&2
    exit 1
fi

echo "Found ${#shell_files[@]} shell file(s)" >&2

# Run ShellCheck
shellcheck_failed=false
if [[ "$AUTO_FIX" == true ]]; then
    echo "Running with --fix (auto-fixing where possible)..." >&2
    for file in "${shell_files[@]}"; do
        echo "  Checking: $(basename "$file")" >&2
        if ! shellcheck --severity="$SEVERITY" --format=diff "$file" | patch -p1; then
            echo "  ⚠️  Could not apply auto-fixes for: $(basename "$file")" >&2
            shellcheck_failed=true
        fi
    done
else
    # Just report issues
    if ! shellcheck --severity="$SEVERITY" --format=gcc "${shell_files[@]}"; then
        shellcheck_failed=true
    fi
fi

echo "" >&2
if [[ "$shellcheck_failed" == true ]]; then
    echo "⚠️  ShellCheck found issues" >&2
else
    echo "✅ ShellCheck passed" >&2
fi
echo "" >&2

# Step 2: Regenerate extract.json
echo "Step 2: Regenerating function index..." >&2
echo "----------------------------------------" >&2

extract_output="${TARGET_PATH}/extract.json"

if uv run "$ANALYZER" --path "$TARGET_PATH" --output "$extract_output"; then
    func_count=$(jq '.index | length' "$extract_output" 2>/dev/null || echo "0")
    echo "✅ Index updated: $func_count function(s)" >&2
else
    echo "⚠️  Index generation failed" >&2
fi

echo "" >&2

# Summary
echo "========================================" >&2
echo "Summary" >&2
echo "========================================" >&2
echo "Files checked: ${#shell_files[@]}" >&2
echo "Functions indexed: ${func_count:-0}" >&2
echo "Extract file: $extract_output" >&2

if [[ "$shellcheck_failed" == true ]]; then
    echo "" >&2
    echo "⚠️  Action required: Fix ShellCheck issues" >&2
    echo "" >&2
    exit 1
else
    echo "" >&2
    echo "✅ All checks passed, index is up to date" >&2
    echo "" >&2
    exit 0
fi
