# bd-lint-extension.sh — Source this file in .zshrc or .bashrc
# Compatible with bash and zsh.
# Shell wrapper that extends 'bd lint' with --check support.
#
# Usage: source this file in your .zshrc or .bashrc:
#
#   source /path/to/beads-workflow/scripts/bd-lint-extension.sh
#
# After sourcing, the following command works:
#
#   bd lint --check=architecture-contracts [--all] [--bead <id>]
#
# Arguments after --check=architecture-contracts are forwarded to the Python script.

_BD_LINT_CONTRACTS_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")" 2>/dev/null && pwd)"

bd() {
    # Intercept: bd lint --check=architecture-contracts [...]
    if [[ "$1" == "lint" ]] && [[ "$2" == --check=architecture-contracts ]]; then
        local script="${_BD_LINT_CONTRACTS_SCRIPT_DIR}/bd_lint_contracts.py"
        if [[ ! -f "$script" ]]; then
            echo "bd-lint-extension: ERROR — bd_lint_contracts.py not found at $script" >&2
            return 1
        fi
        shift 2  # Remove 'lint' and '--check=architecture-contracts'
        python3 "$script" "$@"
        return $?
    fi

    # Pass everything else to the real bd binary
    command bd "$@"
}
