#!/usr/bin/env bash
# WorktreeCreate hook: sync config files from main repo into the new worktree.
# Receives JSON via stdin: {cwd, name, ...} or {worktreePath, ...}
set -euo pipefail

STDIN=$(cat)

# Derive worktree path: prefer explicit worktreePath, fall back to cwd/.claude/worktrees/name
WORKTREE_PATH=$(echo "$STDIN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
p = d.get('worktreePath') or d.get('worktree', {}).get('path') or ''
if not p:
    cwd = d.get('cwd', '')
    name = d.get('name', '')
    if cwd and name:
        p = f'{cwd}/.claude/worktrees/{name}'
print(p)
" 2>/dev/null || echo "")

# Guard: path must be a non-empty existing directory
[ -z "$WORKTREE_PATH" ] && exit 0
[ -d "$WORKTREE_PATH" ] || exit 0

# Resolve main repo root (first entry in worktree list)
MAIN_ROOT=$(git -C "$WORKTREE_PATH" worktree list --porcelain | head -1 | awk '{print $2}')
if [ -z "$MAIN_ROOT" ] || [ "$MAIN_ROOT" = "$WORKTREE_PATH" ]; then
  exit 0
fi

# Copy .env if present
[ -f "$MAIN_ROOT/.env" ] && cp "$MAIN_ROOT/.env" "$WORKTREE_PATH/.env"

# Copy CLAUDE.local.md if present
[ -f "$MAIN_ROOT/CLAUDE.local.md" ] && cp "$MAIN_ROOT/CLAUDE.local.md" "$WORKTREE_PATH/CLAUDE.local.md"

# Sync .claude/ directory if present (exclude worktrees/ to avoid recursive copies)
if [ -d "$MAIN_ROOT/.claude" ]; then
  rsync -a --delete-after --exclude='worktrees/' "$MAIN_ROOT/.claude/" "$WORKTREE_PATH/.claude/"
fi

# Start bd dolt server if .beads/ exists and bd is available (auto-discovers db from cwd)
if [ -d "$WORKTREE_PATH/.beads" ] && command -v bd &>/dev/null; then
  (cd "$WORKTREE_PATH" && bd dolt start &>/dev/null) || true
fi
