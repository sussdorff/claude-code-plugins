#!/usr/bin/env bash
# Search Aidbox documentation by keyword
# Usage: search-docs.sh <keyword> [--fetch]
#   Without --fetch: lists matching page URLs
#   With --fetch: also downloads and greps content
set -euo pipefail

KEYWORD="${1:?Usage: search-docs.sh <keyword> [--fetch]}"
FETCH="${2:-}"
CACHE_FILE="/tmp/aidbox-doc-urls.txt"

# Build URL index if not cached (or older than 1 day)
if [[ ! -f "$CACHE_FILE" ]] || [[ $(find "$CACHE_FILE" -mtime +1 2>/dev/null) ]]; then
  echo "Building doc index..." >&2
  crwl crawl "https://www.health-samurai.io/docs/aidbox/getting-started" -o md 2>&1 \
    | grep -oE 'https://www.health-samurai.io/docs/aidbox/[^ )"]+' \
    | sort -u > "$CACHE_FILE"
  echo "Indexed $(wc -l < "$CACHE_FILE") pages" >&2
fi

# Search by URL path
echo "=== Pages matching '$KEYWORD' ==="
grep -i "$KEYWORD" "$CACHE_FILE" || echo "(no URL matches)"

if [[ "$FETCH" == "--fetch" ]]; then
  echo ""
  echo "=== Content search ==="
  while IFS= read -r url; do
    content=$(curl -sfL "${url}.md" 2>/dev/null || true)
    if echo "$content" | grep -qi "$KEYWORD"; then
      echo "--- $url ---"
      echo "$content" | grep -i -B1 -A2 "$KEYWORD" | head -20
      echo ""
    fi
  done < <(grep -i "$KEYWORD" "$CACHE_FILE")
fi
