#!/usr/bin/env bash
# Common piler-cli commands for searching and reading archived emails.
# Must be run from ~/code/piler-cli (or adjust path below).
# Usage: piler-commands.sh <command> [args...]

set -euo pipefail

PILER_DIR="${PILER_DIR:-${HOME}/code/piler-cli}"
cd "$PILER_DIR"

CMD="${1:?command required: stats|search|list|read}"
shift

case "$CMD" in
  stats)
    uv run piler stats
    ;;
  search)
    QUERY="${1:?search query required}"
    FIELD="${2:-}"
    if [[ -n "$FIELD" ]]; then
      uv run piler search "$QUERY" -f "$FIELD"
    else
      uv run piler search "$QUERY"
    fi
    ;;
  list)
    uv run piler list "$@"
    ;;
  read)
    ID="${1:?email id required}"
    RAW="${2:-}"
    if [[ "$RAW" == "--raw" ]]; then
      uv run piler read "$ID" --raw
    else
      uv run piler read "$ID"
    fi
    ;;
  *)
    echo "Unknown command: $CMD" >&2
    echo "Usage: $0 <stats|search|list|read> [args...]" >&2
    exit 1
    ;;
esac
