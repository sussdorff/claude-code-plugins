#!/usr/bin/env bash
# arch-signal-detect.sh — Detect architecture review signals for beads
#
# Usage: arch-signal-detect.sh <bead-id1> [bead-id2] ...
# Output: JSON array with signal scores per bead
#
# Signal scoring:
#   STRONG patterns (3 points each): [ARCH], state machine, boundary, protocol, API contract
#   MEDIUM patterns (2 points each): [REFACTOR]+core, blocks 2+ beads, alternative approaches
#   Score >= 6 → REVIEW_YES
#   Score 3-5 → REVIEW_MAYBE (needs Haiku fallback)
#   Score < 3 → REVIEW_NO
#
# Exit codes: 0 = success, 1 = no bead IDs given

set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo '{"error": "No bead IDs provided"}' >&2
  exit 1
fi

# Strong signal patterns (case-insensitive grep)
STRONG_PATTERNS=(
  '\[ARCH\]'
  'state.machine'
  'boundary|boundaries'
  'protocol'
  'API.contract'
  'layer.separation|layer.trennung'
)

# Medium signal patterns
MEDIUM_PATTERNS=(
  '\[REFACTOR\]'
  'alternative.approach|trade.off'
  'migration.path|migration.strateg'
)

results="["
first=true

for bead_id in "$@"; do
  # Skip --flags
  [[ "$bead_id" == --* ]] && continue

  # Get bead data
  bead_json=$(bd show "$bead_id" --json 2>/dev/null) || {
    if [[ "$first" != true ]]; then results+=","; fi
    first=false
    results+="{\"id\":\"$bead_id\",\"error\":\"bead not found\"}"
    continue
  }

  title=$(echo "$bead_json" | jq -r '.[0].title // ""')
  description=$(echo "$bead_json" | jq -r '.[0].description // ""')
  issue_type=$(echo "$bead_json" | jq -r '.[0].issue_type // ""')
  full_text="$title $description"

  # Skip types that don't need arch review
  if [[ "$issue_type" == "bug" || "$issue_type" == "chore" ]]; then
    if [[ "$first" != true ]]; then results+=","; fi
    first=false
    results+="{\"id\":\"$bead_id\",\"title\":$(printf '%s' "$title" | jq -Rs .),\"score\":0,\"verdict\":\"REVIEW_NO\",\"reason\":\"type=$issue_type (auto-skip)\",\"signals\":[]}"
    continue
  fi

  score=0
  signals="[]"

  # Check strong signals
  for pattern in "${STRONG_PATTERNS[@]}"; do
    if echo "$full_text" | grep -qiE "$pattern"; then
      matched=$(echo "$full_text" | grep -oiE "$pattern" | head -1)
      score=$((score + 3))
      signals=$(echo "$signals" | jq --arg m "$matched" --arg s "STRONG" '. + [{"match": $m, "strength": $s, "points": 3}]')
    fi
  done

  # Check medium signals
  for pattern in "${MEDIUM_PATTERNS[@]}"; do
    if echo "$full_text" | grep -qiE "$pattern"; then
      matched=$(echo "$full_text" | grep -oiE "$pattern" | head -1)
      score=$((score + 2))
      signals=$(echo "$signals" | jq --arg m "$matched" --arg s "MEDIUM" '. + [{"match": $m, "strength": $s, "points": 2}]')
    fi
  done

  # Check dependency count (medium signal: blocks 2+ beads)
  blocks_count=$(echo "$bead_json" | jq '.[0].blocks // [] | length')
  if [[ "$blocks_count" -ge 2 ]]; then
    score=$((score + 2))
    signals=$(echo "$signals" | jq --arg c "$blocks_count" '. + [{"match": "blocks " + $c + " beads", "strength": "MEDIUM", "points": 2}]')
  fi

  # Determine verdict
  if [[ $score -ge 6 ]]; then
    verdict="REVIEW_YES"
  elif [[ $score -ge 3 ]]; then
    verdict="REVIEW_MAYBE"
  else
    verdict="REVIEW_NO"
  fi

  if [[ "$first" != true ]]; then results+=","; fi
  first=false
  results+="{\"id\":\"$bead_id\",\"title\":$(printf '%s' "$title" | jq -Rs .),\"score\":$score,\"verdict\":\"$verdict\",\"signals\":$signals}"
done

results+="]"
echo "$results" | jq .
