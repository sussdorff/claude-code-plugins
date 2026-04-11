#!/usr/bin/env bash
# Fetch a single Aidbox doc page as markdown
# Usage: fetch-doc.sh <path>
# Example: fetch-doc.sh database/overview
#          fetch-doc.sh modules/other-modules/aidbox-trigger
set -euo pipefail

PATH_ARG="${1:?Usage: fetch-doc.sh <path>  (e.g. database/overview)}"
URL="https://www.health-samurai.io/docs/aidbox/${PATH_ARG}.md"

content=$(curl -sfL "$URL" 2>/dev/null)
if [[ -z "$content" ]] || echo "$content" | head -1 | grep -q '<!DOCTYPE'; then
  echo "ERROR: Page not found at $URL" >&2
  echo "Try: search-docs.sh <keyword> to find the right path" >&2
  exit 1
fi

echo "$content"
