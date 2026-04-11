#!/usr/bin/env bash
# Sync plugin cache after commits in plugin/open-brain repos.
# Called by session-close after push.
# Usage: sync-plugin-cache.sh <repo_root>
set -euo pipefail

REPO_ROOT="${1:-$(git rev-parse --show-toplevel 2>/dev/null || echo "")}"

if [ -z "$REPO_ROOT" ]; then
  echo "sync-plugin-cache: no repo root, skipping"
  exit 0
fi

REPO_NAME=$(basename "$REPO_ROOT")

# Determine which repo we're in
case "$REPO_NAME" in
  claude-code-plugins)
    MARKETPLACE="sussdorff-plugins"
    ALL_PLUGINS=(core beads-workflow dev-tools infra business content medical meta)

    # Detect which plugin dirs were touched in the last commit
    CHANGED_DIRS=$(git -C "$REPO_ROOT" diff HEAD~1 HEAD --name-only 2>/dev/null | cut -d/ -f1 | sort -u || true)

    if [ -z "$CHANGED_DIRS" ]; then
      echo "sync-plugin-cache: no committed changes detected, skipping"
      exit 0
    fi

    PLUGINS_TO_UPDATE=()
    for plugin in "${ALL_PLUGINS[@]}"; do
      if echo "$CHANGED_DIRS" | grep -qx "$plugin"; then
        PLUGINS_TO_UPDATE+=("$plugin")
      fi
    done

    if [ "${#PLUGINS_TO_UPDATE[@]}" -eq 0 ]; then
      echo "sync-plugin-cache: no plugin dirs changed in last commit, skipping"
      exit 0
    fi

    echo "sync-plugin-cache: updating plugins in $MARKETPLACE: ${PLUGINS_TO_UPDATE[*]}"
    for plugin in "${PLUGINS_TO_UPDATE[@]}"; do
      OUTPUT=$(claude plugins update "$plugin@$MARKETPLACE" 2>&1 || true)
      if echo "$OUTPUT" | grep -q "Successfully\|already at\|Updated"; then
        echo "  ✔ $plugin"
      else
        echo "  ✘ $plugin — $OUTPUT"
      fi
    done
    ;;

  open-brain)
    MARKETPLACE="open-brain-marketplace"
    PLUGIN="open-brain"

    # Check if plugin dir was touched
    CHANGED=$(git -C "$REPO_ROOT" diff HEAD~1 HEAD --name-only 2>/dev/null | grep -c "^plugin/" || true)
    if [ "$CHANGED" -eq 0 ]; then
      echo "sync-plugin-cache: no plugin/ changes in open-brain, skipping"
      exit 0
    fi

    echo "sync-plugin-cache: updating $PLUGIN@$MARKETPLACE"
    OUTPUT=$(claude plugins update "$PLUGIN@$MARKETPLACE" 2>&1 || true)
    if echo "$OUTPUT" | grep -q "Successfully\|already at\|Updated"; then
      echo "  ✔ $PLUGIN"
    else
      echo "  ✘ $PLUGIN — $OUTPUT"
    fi
    ;;

  *)
    # Not a plugin repo — skip silently
    exit 0
    ;;
esac
