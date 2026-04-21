#!/usr/bin/env bash
# fetch-latest.sh — Compare baseline system prompt version against cchistory API
#
# Output (key=value lines, stable for parsing):
#   BASELINE_VERSION=2.1.92
#   LATEST_VERSION=2.1.93
#   STATUS=current|outdated
#   NEW_PROMPT_FILE=/tmp/prompt-2.1.93.md   (only when STATUS=outdated)
#
# Exit codes:
#   0 — success (current or outdated, output always valid)
#   1 — error (API unreachable, baseline not found, etc.)

set -euo pipefail

API_BASE="https://cchistory.mariozechner.at/data"
BASELINE_DIR="$(cd "$(dirname "$0")/../../../system-prompts/baseline" 2>/dev/null && pwd)" || {
  echo "ERROR: Cannot locate malte/system-prompts/baseline/ directory" >&2
  exit 1
}

# ── Locate baseline file ──────────────────────────────────────────────────────

BASELINE_FILE="$(ls "$BASELINE_DIR"/anthropic-v*.md 2>/dev/null | sort -V | tail -1)"
if [[ -z "$BASELINE_FILE" ]]; then
  echo "ERROR: No baseline file matching anthropic-v*.md in $BASELINE_DIR" >&2
  exit 1
fi

# Extract version from filename: anthropic-v2.1.92.md → 2.1.92
BASELINE_FILENAME="$(basename "$BASELINE_FILE")"
BASELINE_VERSION="${BASELINE_FILENAME#anthropic-v}"
BASELINE_VERSION="${BASELINE_VERSION%.md}"

# Validate baseline version format (defence against malformed filenames)
if [[ ! "$BASELINE_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "ERROR: Unexpected baseline version format: '$BASELINE_VERSION' (expected N.N.N)" >&2
  exit 1
fi

# ── Fetch latest version from API ────────────────────────────────────────────

VERSIONS_JSON="$(curl -sf "${API_BASE}/versions.json")" || {
  echo "ERROR: Failed to fetch ${API_BASE}/versions.json" >&2
  exit 1
}

# Extract last version entry (array is chronological, latest = last)
LATEST_VERSION="$(echo "$VERSIONS_JSON" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data['versions'][-1]['version'])
except (json.JSONDecodeError, KeyError, IndexError) as e:
    print(f'ERROR: Failed to parse versions JSON: {e}', file=sys.stderr)
    sys.exit(1)
")"

if [[ -z "$LATEST_VERSION" ]]; then
  echo "ERROR: Could not parse latest version from API response" >&2
  exit 1
fi

# Validate version format to prevent path traversal from a compromised API
if [[ ! "$LATEST_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "ERROR: Unexpected version format from API: '$LATEST_VERSION' (expected N.N.N)" >&2
  exit 1
fi

# ── Compare versions ──────────────────────────────────────────────────────────

echo "BASELINE_VERSION=${BASELINE_VERSION}"
echo "LATEST_VERSION=${LATEST_VERSION}"

if [[ "$BASELINE_VERSION" == "$LATEST_VERSION" ]]; then
  echo "STATUS=current"
else
  echo "STATUS=outdated"

  # Fetch new prompt and save to tmp file
  PROMPT_URL="${API_BASE}/prompts-${LATEST_VERSION}.md"
  TMP_FILE="/tmp/prompt-${LATEST_VERSION}.md"

  curl -sf "$PROMPT_URL" -o "$TMP_FILE" || {
    echo "ERROR: Failed to fetch prompt from $PROMPT_URL" >&2
    exit 1
  }

  echo "NEW_PROMPT_FILE=${TMP_FILE}"
fi
