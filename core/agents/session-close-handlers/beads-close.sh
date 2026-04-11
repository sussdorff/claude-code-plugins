#!/usr/bin/env bash
# beads-close.sh - Interactive beads closing workflow
# Usage: beads-close.sh [--dry-run]
#
# Lists open/in-progress beads and outputs them for Claude to present interactively.

set -euo pipefail

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

# Check if bd command is available
if ! command -v bd &>/dev/null; then
  echo "WARNING: bd command not found. Skipping beads review."
  exit 0
fi

echo "Checking open beads..."
echo ""

# Show in-progress beads
IN_PROGRESS=$(bd list --status=in_progress 2>/dev/null || echo "")
if [ -n "$IN_PROGRESS" ]; then
  echo "IN-PROGRESS beads:"
  echo "$IN_PROGRESS"
  echo ""
else
  echo "No in-progress beads."
  echo ""
fi

# Show ready beads
READY=$(bd ready 2>/dev/null || echo "")
if [ -n "$READY" ]; then
  echo "READY beads (unblocked):"
  echo "$READY"
  echo ""
else
  echo "No ready beads."
  echo ""
fi

if $DRY_RUN; then
  echo "[DRY-RUN] Would interactively ask to close each in-progress bead."
else
  echo "For each in-progress bead, decide:"
  echo "  - Close with reason: bd close <id> --reason=\"...\""
  echo "  - Leave open: skip"
  echo "  - Update: bd update <id> --status=<status>"
fi
