#!/usr/bin/env bash
# Gather backlog data for workplan analysis.
# Run all bd queries in parallel and print combined output.
# Usage: gather-data.sh [--label=<label>] [--epic=<epic>] [--focus=<priority>]
set -euo pipefail

bd stats
bd list --status=in_progress -n 0
bd ready -n 50
bd blocked | head -40
bd list --priority 0 --status=open -n 0
bd list --priority 1 --status=open -n 0
