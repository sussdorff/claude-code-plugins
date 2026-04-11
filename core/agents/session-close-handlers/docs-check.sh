#!/usr/bin/env bash
# docs-check.sh - Documentation gap detection
# Usage: docs-check.sh
#
# Scans files changed since last tag and identifies potential documentation gaps.
# Advisory only -- does not make changes.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

# Determine what changed since last tag
LATEST_TAG=$(git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LATEST_TAG" ]; then
  RANGE="${LATEST_TAG}..HEAD"
  echo "Checking changes since $LATEST_TAG..."
else
  # No tags -- check last 20 commits
  RANGE="HEAD~20..HEAD"
  echo "No tags found. Checking last 20 commits..."
fi

# Get changed files
CHANGED_FILES=$(git -C "$REPO_ROOT" diff --name-only "$RANGE" 2>/dev/null || echo "")

if [ -z "$CHANGED_FILES" ]; then
  echo "No changed files to check."
  exit 0
fi

# Track findings
GAPS_FOUND=false

# Check 1: New skills without documentation
NEW_SKILLS=$(echo "$CHANGED_FILES" | grep -E '^malte/skills/[^/]+/SKILL\.md$' || true)
if [ -n "$NEW_SKILLS" ]; then
  echo ""
  echo "New/modified skills (verify documentation is complete):"
  echo "$NEW_SKILLS" | while read -r f; do
    SKILL_NAME=$(echo "$f" | sed 's|malte/skills/\([^/]*\)/.*|\1|')
    echo "  - $SKILL_NAME"
  done
  GAPS_FOUND=true
fi

# Check 2: New agents without documentation
NEW_AGENTS=$(echo "$CHANGED_FILES" | grep -E '\.claude/agents/' || true)
if [ -n "$NEW_AGENTS" ]; then
  echo ""
  echo "New/modified agents (check if docs need update):"
  echo "$NEW_AGENTS" | sed 's/^/  - /'
  GAPS_FOUND=true
fi

# Check 3: Changed hooks
CHANGED_HOOKS=$(echo "$CHANGED_FILES" | grep -E 'hooks/' || true)
if [ -n "$CHANGED_HOOKS" ]; then
  echo ""
  echo "Changed hooks (verify CLAUDE.md references are current):"
  echo "$CHANGED_HOOKS" | sed 's/^/  - /'
  GAPS_FOUND=true
fi

# Check 4: Changed standards
CHANGED_STANDARDS=$(echo "$CHANGED_FILES" | grep -E 'standards/' || true)
if [ -n "$CHANGED_STANDARDS" ]; then
  echo ""
  echo "Changed standards (check index.yml is updated):"
  echo "$CHANGED_STANDARDS" | sed 's/^/  - /'
  GAPS_FOUND=true
fi

# Check 5: README changes needed?
CODE_CHANGES=$(echo "$CHANGED_FILES" | grep -vE '\.(md|txt|json|yml|yaml|toml)$' | head -10 || true)
DOC_CHANGES=$(echo "$CHANGED_FILES" | grep -E '\.(md)$' || true)
if [ -n "$CODE_CHANGES" ] && [ -z "$DOC_CHANGES" ]; then
  echo ""
  echo "Code changed without documentation updates:"
  echo "$CODE_CHANGES" | sed 's/^/  - /'
  echo "  (Consider if README or docs/ need updating)"
  GAPS_FOUND=true
fi

# Summary
echo ""
if $GAPS_FOUND; then
  echo "Documentation gaps detected. Review the items above."
else
  echo "No documentation gaps detected."
fi
