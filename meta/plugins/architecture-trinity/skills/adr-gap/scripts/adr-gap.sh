#!/usr/bin/env bash
# adr-gap.sh — Shell runner for the /adr-gap skill.
#
# Locates adr-hoist-check.py relative to this script and runs it with
# all arguments forwarded. Defaults repo_root to the current directory
# if no positional argument is given.
#
# Usage:
#   adr-gap.sh [repo_root] [--create-beads] [--ci] [--allow-unknown]
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECKER="$SCRIPT_DIR/adr-hoist-check.py"

if [[ ! -f "$CHECKER" ]]; then
    echo "ERROR: adr-hoist-check.py not found at $CHECKER" >&2
    exit 1
fi

# Default repo_root to current directory if first arg looks like a flag or is absent
if [[ $# -eq 0 ]] || [[ "$1" == --* ]]; then
    REPO_ROOT="$(pwd)"
    exec uv run "$CHECKER" "$REPO_ROOT" "$@"
else
    exec uv run "$CHECKER" "$@"
fi
