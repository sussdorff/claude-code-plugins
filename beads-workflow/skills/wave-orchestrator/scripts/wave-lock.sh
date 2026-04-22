#!/usr/bin/env bash
# wave-lock.sh — Single-instance guard for the wave orchestrator.
#
# Usage:
#   wave-lock.sh acquire <lockfile> <wave_id> <surface>
#       Fail-fast: exits 1 immediately if another live orchestrator holds the lock.
#       If lock exists but holder PID is dead → warn, auto-clear, acquire.
#       Exits 0 on success.
#
#   wave-lock.sh release <lockfile>
#       Remove the lock. Called on clean orchestrator exit.
#       Exits 0. Safe to call even if lockfile is absent.
#
#   wave-lock.sh status <lockfile>
#       Print lock state JSON to stdout.
#       Exits 0 regardless of lock state.
#
# Lockfile: written atomically (temp+mv). Stored at $MAIN_REPO_ROOT/.wave-orchestrator.lock
#
# Lockfile format:
#   {
#     "holder": {
#       "wave_id": "...",
#       "surface": "...",
#       "pid": 123,
#       "acquired_at": "ISO-8601"
#     }
#   }
#
# Error message on collision:
#   Wave orchestrator already running (wave_id: ..., surface: ...).
#   Do NOT start another — use beads-workflow:wave-monitor to watch progress.

set -uo pipefail

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

now_iso() {
  date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date +%Y-%m-%dT%H:%M:%SZ
}

pid_alive() {
  local pid="$1"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

read_lock() {
  local lockfile="$1"
  if [[ -f "$lockfile" ]]; then
    jq '.' "$lockfile" 2>/dev/null || echo '{"holder":null}'
  else
    echo '{"holder":null}'
  fi
}

write_lock_atomic() {
  local lockfile="$1"
  local json="$2"
  local tmpfile
  tmpfile="$(dirname "$lockfile")/.$(basename "$lockfile").tmp.$$"
  printf '%s\n' "$json" > "$tmpfile"
  mv -f "$tmpfile" "$lockfile"
}

# ---------------------------------------------------------------------------
# Subcommand: status
# ---------------------------------------------------------------------------
cmd_status() {
  local lockfile="$1"
  read_lock "$lockfile"
}

# ---------------------------------------------------------------------------
# Subcommand: acquire (fail-fast)
# ---------------------------------------------------------------------------
cmd_acquire() {
  local lockfile="$1"
  local wave_id="$2"
  local surface="$3"
  local my_pid="$$"

  local lock_json holder_null holder_json holder_pid holder_wave holder_surface

  lock_json=$(read_lock "$lockfile")
  holder_null=$(printf '%s' "$lock_json" | jq '.holder == null')

  # --- Case 1: No holder → acquire immediately ---
  if [[ "$holder_null" == "true" ]]; then
    local new_lock
    new_lock=$(jq -cn \
      --arg wave_id "$wave_id" \
      --arg surface "$surface" \
      --argjson pid "$my_pid" \
      --arg acquired_at "$(now_iso)" \
      '{"holder": {"wave_id": $wave_id, "surface": $surface, "pid": $pid, "acquired_at": $acquired_at}}')
    write_lock_atomic "$lockfile" "$new_lock"
    echo "==> [wave-lock] acquired (wave_id=$wave_id surface=$surface pid=$my_pid)" >&2
    return 0
  fi

  # --- Case 2: Lock exists — inspect holder ---
  holder_json=$(printf '%s' "$lock_json" | jq '.holder')
  holder_pid=$(printf '%s' "$holder_json" | jq -r '.pid // 0')
  holder_wave=$(printf '%s' "$holder_json" | jq -r '.wave_id // "unknown"')
  holder_surface=$(printf '%s' "$holder_json" | jq -r '.surface // "unknown"')

  if pid_alive "$holder_pid"; then
    # Live holder → fail-fast with clear error message
    echo "" >&2
    echo "ERROR: Wave orchestrator already running (wave_id: $holder_wave, surface: $holder_surface)." >&2
    echo "Do NOT start another — use beads-workflow:wave-monitor to watch progress." >&2
    echo "" >&2
    exit 1
  fi

  # --- Case 3: Holder PID is dead → warn, auto-clear, acquire ---
  local acquired_at
  acquired_at=$(printf '%s' "$holder_json" | jq -r '.acquired_at // "unknown"')
  echo "==> [wave-lock] WARNING: found dead holder (wave_id=$holder_wave pid=$holder_pid acquired_at=$acquired_at)" >&2
  echo "==> [wave-lock] auto-clearing stale lock and acquiring" >&2

  local new_lock
  new_lock=$(jq -cn \
    --arg wave_id "$wave_id" \
    --arg surface "$surface" \
    --argjson pid "$my_pid" \
    --arg acquired_at "$(now_iso)" \
    '{"holder": {"wave_id": $wave_id, "surface": $surface, "pid": $pid, "acquired_at": $acquired_at}}')
  write_lock_atomic "$lockfile" "$new_lock"
  echo "==> [wave-lock] acquired after stale-clear (wave_id=$wave_id surface=$surface pid=$my_pid)" >&2
  return 0
}

# ---------------------------------------------------------------------------
# Subcommand: release
# ---------------------------------------------------------------------------
cmd_release() {
  local lockfile="$1"

  if [[ ! -f "$lockfile" ]]; then
    echo "==> [wave-lock] release: lockfile not found ($lockfile) — already released or never acquired" >&2
    return 0
  fi

  local cleared
  cleared='{"holder":null}'
  write_lock_atomic "$lockfile" "$cleared"
  echo "==> [wave-lock] lock released" >&2
  return 0
}

# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------
SUBCOMMAND="${1:-}"
shift || true

case "$SUBCOMMAND" in
  acquire)
    [[ $# -ge 3 ]] || { echo "Usage: wave-lock.sh acquire <lockfile> <wave_id> <surface>" >&2; exit 1; }
    cmd_acquire "$1" "$2" "$3"
    ;;
  release)
    [[ $# -ge 1 ]] || { echo "Usage: wave-lock.sh release <lockfile>" >&2; exit 1; }
    cmd_release "$1"
    ;;
  status)
    [[ $# -ge 1 ]] || { echo "Usage: wave-lock.sh status <lockfile>" >&2; exit 1; }
    cmd_status "$1"
    ;;
  *)
    echo "Usage: wave-lock.sh <acquire|release|status> <lockfile> [<wave_id> <surface>]" >&2
    exit 1
    ;;
esac
