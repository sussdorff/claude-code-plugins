#!/bin/bash
# Automated Hook Testing Script
#
# This script tests Claude Code hooks to ensure they behave correctly.
# It validates security patterns, exit codes, and integration with settings.json.
#
# Usage:
#   ./test_hooks.sh                    # Run all tests
#   ./test_hooks.sh pre_tool_use       # Test specific hook
#   ./test_hooks.sh --help             # Show help

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
PASSED=0
FAILED=0
TOTAL=0

# Print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_failure() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_header() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════════════"
}

# Test a hook with specific input and expected exit code
test_hook() {
    local hook_script=$1
    local test_name=$2
    local test_input=$3
    local expected_exit=$4
    local description=$5

    TOTAL=$((TOTAL + 1))

    if [ ! -f "$hook_script" ]; then
        print_failure "$test_name: Hook script not found: $hook_script"
        FAILED=$((FAILED + 1))
        return 1
    fi

    # Run the hook with test input
    local actual_exit=0
    echo "$test_input" | uv run "$hook_script" >/dev/null 2>&1 || actual_exit=$?

    if [ "$actual_exit" -eq "$expected_exit" ]; then
        print_success "$test_name: $description (exit $actual_exit)"
        PASSED=$((PASSED + 1))
        return 0
    else
        print_failure "$test_name: Expected exit $expected_exit, got $actual_exit"
        print_info "  Description: $description"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Test PreToolUse hook
test_pre_tool_use() {
    local hook_script="${1:-.claude/hooks/pre_tool_use.py}"

    print_header "Testing PreToolUse Hook"

    # Test 1: Dangerous rm -rf /
    test_hook "$hook_script" \
        "PreToolUse-1" \
        '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' \
        2 \
        "Should block 'rm -rf /'"

    # Test 2: Dangerous rm -rf ~
    test_hook "$hook_script" \
        "PreToolUse-2" \
        '{"tool_name":"Bash","tool_input":{"command":"rm -rf ~"}}' \
        2 \
        "Should block 'rm -rf ~'"

    # Test 3: Dangerous rm -rf *
    test_hook "$hook_script" \
        "PreToolUse-3" \
        '{"tool_name":"Bash","tool_input":{"command":"rm -rf *"}}' \
        2 \
        "Should block 'rm -rf *'"

    # Test 4: Safe ls command
    test_hook "$hook_script" \
        "PreToolUse-4" \
        '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' \
        0 \
        "Should allow 'ls -la'"

    # Test 5: Safe mkdir command
    test_hook "$hook_script" \
        "PreToolUse-5" \
        '{"tool_name":"Bash","tool_input":{"command":"mkdir test"}}' \
        0 \
        "Should allow 'mkdir test'"

    # Test 6: Access to .env file
    test_hook "$hook_script" \
        "PreToolUse-6" \
        '{"tool_name":"Read","tool_input":{"file_path":"/path/to/.env"}}' \
        2 \
        "Should block access to .env file"

    # Test 7: Access to .env.sample file
    test_hook "$hook_script" \
        "PreToolUse-7" \
        '{"tool_name":"Read","tool_input":{"file_path":"/path/to/.env.sample"}}' \
        0 \
        "Should allow access to .env.sample"

    # Test 8: Access to regular file
    test_hook "$hook_script" \
        "PreToolUse-8" \
        '{"tool_name":"Read","tool_input":{"file_path":"/path/to/regular.txt"}}' \
        0 \
        "Should allow access to regular files"

    # Test 9: Dangerous chmod 777
    test_hook "$hook_script" \
        "PreToolUse-9" \
        '{"tool_name":"Bash","tool_input":{"command":"chmod 777 file.sh"}}' \
        2 \
        "Should block 'chmod 777'"

    # Test 10: Safe chmod 755
    test_hook "$hook_script" \
        "PreToolUse-10" \
        '{"tool_name":"Bash","tool_input":{"command":"chmod 755 file.sh"}}' \
        0 \
        "Should allow 'chmod 755'"
}

# Test PostToolUse hook
test_post_tool_use() {
    local hook_script="${1:-.claude/hooks/post_tool_use.py}"

    print_header "Testing PostToolUse Hook"

    # PostToolUse hooks should never block (exit 0 or 1, never 2)

    # Test 1: Edit Python file
    test_hook "$hook_script" \
        "PostToolUse-1" \
        '{"tool_name":"Edit","tool_input":{"file_path":"/tmp/test.py"},"tool_output":{}}' \
        0 \
        "Should process Python file edit (non-blocking)"

    # Test 2: Write JavaScript file
    test_hook "$hook_script" \
        "PostToolUse-2" \
        '{"tool_name":"Write","tool_input":{"file_path":"/tmp/test.js"},"tool_output":{}}' \
        0 \
        "Should process JavaScript file write (non-blocking)"

    # Test 3: Non-code file
    test_hook "$hook_script" \
        "PostToolUse-3" \
        '{"tool_name":"Edit","tool_input":{"file_path":"/tmp/test.txt"},"tool_output":{}}' \
        0 \
        "Should handle non-code files gracefully"
}

# Test SessionStart hook
test_session_start() {
    local hook_script="${1:-.claude/hooks/session_start.py}"

    print_header "Testing SessionStart Hook"

    # SessionStart should always succeed (exit 0)

    # Test 1: Basic session start
    test_hook "$hook_script" \
        "SessionStart-1" \
        '{"session_id":"test-123","transcript_path":"/tmp/transcript.jsonl"}' \
        0 \
        "Should initialize session successfully"

    # Test 2: Session start with empty input
    test_hook "$hook_script" \
        "SessionStart-2" \
        '{}' \
        0 \
        "Should handle empty input gracefully"
}

# Test Stop hook
test_stop() {
    local hook_script="${1:-.claude/hooks/stop.py}"

    print_header "Testing Stop Hook"

    print_warning "Stop hook tests depend on project state (tests, build, etc.)"
    print_info "These tests verify the hook runs, not the validation logic"

    # Test 1: Basic stop validation
    test_hook "$hook_script" \
        "Stop-1" \
        '{"session_id":"test-123","transcript_path":"/tmp/transcript.jsonl"}' \
        0 \
        "Should validate stop conditions (may vary by project)"
}

# Test hook manager script
test_hook_manager() {
    print_header "Testing Hook Manager Script"

    local hook_manager="scripts/hook_manager.py"

    if [ ! -f "$hook_manager" ]; then
        print_warning "Hook manager not found at: $hook_manager"
        return 0
    fi

    # Test list command
    TOTAL=$((TOTAL + 1))
    if uv run "$hook_manager" list >/dev/null 2>&1; then
        print_success "Hook manager list command works"
        PASSED=$((PASSED + 1))
    else
        print_failure "Hook manager list command failed"
        FAILED=$((FAILED + 1))
    fi
}

# Test settings.json validation
test_settings_validation() {
    print_header "Testing Settings Validation"

    local settings_files=(
        ".claude/settings.json"
        "$HOME/.claude/settings.json"
    )

    for settings_file in "${settings_files[@]}"; do
        if [ -f "$settings_file" ]; then
            TOTAL=$((TOTAL + 1))
            if jq empty "$settings_file" 2>/dev/null; then
                print_success "Valid JSON: $settings_file"
                PASSED=$((PASSED + 1))
            else
                print_failure "Invalid JSON: $settings_file"
                FAILED=$((FAILED + 1))
            fi
        fi
    done

    if [ "$TOTAL" -eq 0 ]; then
        print_info "No settings.json files found (this is okay)"
    fi
}

# Test template scripts
test_templates() {
    print_header "Testing Template Scripts"

    local templates=(
        "assets/templates/pre_tool_use_template.py"
        "assets/templates/post_tool_use_template.py"
        "assets/templates/session_start_template.py"
        "assets/templates/stop_template.py"
    )

    for template in "${templates[@]}"; do
        if [ -f "$template" ]; then
            TOTAL=$((TOTAL + 1))
            # Check if template has --test mode
            if grep -q "def test_hook" "$template" 2>/dev/null; then
                if uv run "$template" --test >/dev/null 2>&1; then
                    print_success "Template test mode works: $(basename "$template")"
                    PASSED=$((PASSED + 1))
                else
                    print_failure "Template test mode failed: $(basename "$template")"
                    FAILED=$((FAILED + 1))
                fi
            else
                print_warning "Template missing test mode: $(basename "$template")"
            fi
        fi
    done
}

# Print test summary
print_summary() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  Test Summary"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "  Total tests:   $TOTAL"
    echo -e "  ${GREEN}Passed:${NC}        $PASSED"
    echo -e "  ${RED}Failed:${NC}        $FAILED"
    echo ""

    if [ "$FAILED" -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}✗ Some tests failed${NC}"
        return 1
    fi
}

# Show help
show_help() {
    cat << EOF
Hook Testing Script

Usage:
  $0 [OPTIONS] [TEST_NAME]

Options:
  --help              Show this help message

Test Names:
  all                 Run all tests (default)
  pre_tool_use        Test PreToolUse hook
  post_tool_use       Test PostToolUse hook
  session_start       Test SessionStart hook
  stop                Test Stop hook
  manager             Test hook manager script
  settings            Test settings.json validation
  templates           Test template scripts

Examples:
  $0                          # Run all tests
  $0 pre_tool_use             # Test only PreToolUse hook
  $0 templates                # Test template scripts

Requirements:
  - uv (UV package manager)
  - jq (JSON processor)
  - Hook scripts in .claude/hooks/ or specify path

EOF
}

# Main function
main() {
    local test_name="${1:-all}"

    if [ "$test_name" = "--help" ] || [ "$test_name" = "-h" ]; then
        show_help
        exit 0
    fi

    print_header "Claude Code Hook Tests"
    print_info "Testing hook behavior and validation logic"

    case "$test_name" in
        all)
            test_pre_tool_use
            test_post_tool_use
            test_session_start
            test_stop
            test_hook_manager
            test_settings_validation
            test_templates
            ;;
        pre_tool_use)
            test_pre_tool_use "$2"
            ;;
        post_tool_use)
            test_post_tool_use "$2"
            ;;
        session_start)
            test_session_start "$2"
            ;;
        stop)
            test_stop "$2"
            ;;
        manager)
            test_hook_manager
            ;;
        settings)
            test_settings_validation
            ;;
        templates)
            test_templates
            ;;
        *)
            print_failure "Unknown test: $test_name"
            show_help
            exit 1
            ;;
    esac

    print_summary
}

# Run main function
main "$@"
