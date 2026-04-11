#!/usr/bin/env bash
# changelog.sh - git-cliff wrapper for changelog generation
# Usage: changelog.sh [--dry-run]
#
# Generates/updates CHANGELOG.md from conventional commits since last tag.
# Requires: git-cliff installed, cliff.toml in repo root.

set -euo pipefail

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
CHANGELOG="$REPO_ROOT/CHANGELOG.md"
CLIFF_CONFIG="$REPO_ROOT/cliff.toml"

# Check prerequisites
if ! command -v git-cliff &>/dev/null; then
  echo "ERROR: git-cliff not found. Install with: brew install git-cliff"
  exit 1
fi

if [ ! -f "$CLIFF_CONFIG" ]; then
  echo "ERROR: cliff.toml not found at $CLIFF_CONFIG"
  exit 1
fi

# Determine tag range
LATEST_TAG=$(git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LATEST_TAG" ]; then
  echo "Last tag: $LATEST_TAG"
  RANGE="${LATEST_TAG}..HEAD"
else
  echo "No previous tags found. Generating full changelog."
  RANGE=""
fi

COMMIT_COUNT=$(git -C "$REPO_ROOT" log ${RANGE:+"$RANGE"} --oneline 2>/dev/null | wc -l | tr -d ' ')
echo "Commits since last tag: $COMMIT_COUNT"

if [ "$COMMIT_COUNT" -eq 0 ]; then
  echo "No new commits. Changelog is up to date."
  exit 0
fi

if $DRY_RUN; then
  echo ""
  echo "[DRY-RUN] Would generate changelog with git-cliff:"
  echo ""
  cd "$REPO_ROOT"
  if [ -n "$RANGE" ]; then
    git-cliff --config "$CLIFF_CONFIG" "$RANGE" --unreleased 2>/dev/null || \
      git-cliff --config "$CLIFF_CONFIG" --unreleased 2>/dev/null || \
      echo "[DRY-RUN] git-cliff preview unavailable"
  else
    git-cliff --config "$CLIFF_CONFIG" --unreleased 2>/dev/null || \
      echo "[DRY-RUN] git-cliff preview unavailable"
  fi
else
  echo "Generating changelog..."
  cd "$REPO_ROOT"

  if [ -f "$CHANGELOG" ]; then
    # Update existing changelog (prepend new entries)
    git-cliff --config "$CLIFF_CONFIG" --output "$CHANGELOG" 2>/dev/null
  else
    # Create new changelog
    git-cliff --config "$CLIFF_CONFIG" --output "$CHANGELOG" 2>/dev/null
  fi

  if [ -f "$CHANGELOG" ]; then
    echo "CHANGELOG.md updated."
    echo "Staging CHANGELOG.md..."
    git -C "$REPO_ROOT" add "$CHANGELOG"
  else
    echo "WARNING: CHANGELOG.md was not created. Check git-cliff configuration."
  fi
fi
