#!/usr/bin/env sh
# bd-lint-extension.sh — Shell wrapper that adds `bd lint --check=architecture-contracts` support.
#
# The bd binary does not natively support `bd lint`. Source this file to define a bd() shell
# function that intercepts the lint subcommand and delegates to bd_lint_contracts.py.
#
# Usage:
#   source beads-workflow/scripts/bd-lint-extension.sh
#   bd lint --check=architecture-contracts
#   bd lint --check=architecture-contracts --all
#   bd lint --check=architecture-contracts --bead CCP-0hr
#
# Compatible with bash and zsh.
#
# The Python script path is resolved relative to this shell script's location,
# so the extension works regardless of where you source it from.

# Resolve the directory containing this script.
# Works in both bash (BASH_SOURCE) and zsh (0).
_bd_lint_ext_resolve_dir() {
    if [ -n "${BASH_SOURCE[0]}" ]; then
        # bash
        echo "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    elif [ -n "${ZSH_VERSION}" ]; then
        # zsh
        echo "$(cd "$(dirname "${(%):-%x}")" && pwd)"
    else
        # POSIX fallback — may not work for all sourcing scenarios
        echo "$(cd "$(dirname "$0")" && pwd)"
    fi
}

_BD_LINT_SCRIPT_DIR="$(_bd_lint_ext_resolve_dir)"
_BD_LINT_CONTRACTS_PY="${_BD_LINT_SCRIPT_DIR}/bd_lint_contracts.py"

# bd() — wrapper function that intercepts lint subcommand.
bd() {
    # Check if this is a lint call with --check=architecture-contracts
    case "$*" in
        lint*--check=architecture-contracts*)
            # Extract extra flags for the Python script
            _bd_lint_extra_args=""
            for arg in "$@"; do
                case "$arg" in
                    lint|--check=architecture-contracts) ;;
                    *) _bd_lint_extra_args="${_bd_lint_extra_args} ${arg}" ;;
                esac
            done
            # shellcheck disable=SC2086
            python3 "${_BD_LINT_CONTRACTS_PY}" ${_bd_lint_extra_args}
            return $?
            ;;
        *)
            # Pass everything else through to the real bd binary
            command bd "$@"
            return $?
            ;;
    esac
}

# Export so sub-shells can use it (bash only; zsh does not support function export)
if [ -n "${BASH_VERSION}" ]; then
    export -f bd 2>/dev/null || true
fi

echo "bd-lint-extension loaded. 'bd lint --check=architecture-contracts' now available."
echo "Python script: ${_BD_LINT_CONTRACTS_PY}"
