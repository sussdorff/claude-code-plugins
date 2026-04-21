#!/usr/bin/env bash
# WorktreeCreate hook: sync config files from main repo into the new worktree.
# Receives JSON via stdin with worktreePath.
set -euo pipefail

WORKTREE_PATH=$(python3 -c "import sys,json; print(json.load(sys.stdin).get('worktreePath',''))")
if [ -z "$WORKTREE_PATH" ]; then
  exit 0
fi

# Resolve main repo root (first entry in worktree list)
MAIN_ROOT=$(git -C "$WORKTREE_PATH" worktree list --porcelain | head -1 | awk '{print $2}')
if [ -z "$MAIN_ROOT" ] || [ "$MAIN_ROOT" = "$WORKTREE_PATH" ]; then
  exit 0
fi

# Copy .env if present
[ -f "$MAIN_ROOT/.env" ] && cp "$MAIN_ROOT/.env" "$WORKTREE_PATH/.env"

# Copy CLAUDE.local.md if present
[ -f "$MAIN_ROOT/CLAUDE.local.md" ] && cp "$MAIN_ROOT/CLAUDE.local.md" "$WORKTREE_PATH/CLAUDE.local.md"

# Sync .claude/ directory if present
if [ -d "$MAIN_ROOT/.claude" ]; then
  rsync -a --delete-after "$MAIN_ROOT/.claude/" "$WORKTREE_PATH/.claude/"
fi

# Start bd dolt server if .beads/ exists and bd is available (auto-discovers db from cwd)
if [ -d "$WORKTREE_PATH/.beads" ] && command -v bd &>/dev/null; then
  (cd "$WORKTREE_PATH" && bd dolt start &>/dev/null) || true
fi
