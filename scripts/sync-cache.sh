#!/usr/bin/env bash
# Sync all sussdorff-plugins to Claude Code plugin cache.
# Manual full-sync — updates all plugins regardless of what changed.
# For targeted sync (changed plugins only), session-close runs
# handlers/sync-plugin-cache.sh automatically after each commit.
set -euo pipefail

MARKETPLACE="sussdorff-plugins"

for plugin in core beads-workflow dev-tools infra business content medical meta; do
  if claude plugins update "$plugin@$MARKETPLACE" 2>&1 | grep -q "Successfully\|already at"; then
    echo "✔ $plugin"
  else
    echo "✘ $plugin (not installed?)"
  fi
done
