#!/usr/bin/env bash
# session-close-lock.sh — Serialize parallel session-close agents via a JSON lockfile.
#
# Subcommands:
#   acquire <lockfile> <bead_id> <surface>
#       Atomically acquire the lock or queue + poll until acquired.
#       Exit 0 on success.
#
#   release <lockfile>
#       Remove self from holder, promote next in queue.
#       Exit 0 on success, 1 if lock file not found.
#
#   status <lockfile>
#       Print current holder + queue as JSON to stdout.
#       Exit 0.
#
# Lockfile format (JSON, written atomically via temp+mv):
#   {
#     "holder": {
#       "bead_id": "...",
#       "surface": "...",
#       "pid": 123,
#       "started_at": "ISO-8601"
#     },
#     "queue": [
#       { "bead_id": "...", "surface": "...", "queued_at": "ISO-8601" }
#     ]
#   }
#
# Stale detection: if holder PID is dead AND started_at > 30 minutes ago → auto-clear.
#
# Poll behavior: acquire polls every LOCK_POLL_INTERVAL seconds (default 5s).
# Timeout after LOCK_TIMEOUT seconds (default 3600s / 1 hour).
#
# Usage in phase-b-prepare.sh:
#   LOCK_FILE="${REPO_ROOT}/.session-close.lock"
#   bash session-close-lock.sh acquire "$LOCK_FILE" "$BEAD_ID" "$SURFACE"
#
# Usage in phase-b-close-beads.sh:
#   bash session-close-lock.sh release "$LOCK_FILE"

set -uo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LOCK_POLL_INTERVAL="${LOCK_POLL_INTERVAL:-5}"     # seconds between poll attempts
LOCK_TIMEOUT="${LOCK_TIMEOUT:-3600}"               # max seconds to wait for lock
STALE_THRESHOLD=1800                               # seconds: holder PID dead + this old → stale

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

now_iso() {
  date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date +%Y-%m-%dT%H:%M:%SZ
}

# pid_alive <pid> — returns 0 if pid is running, 1 otherwise
pid_alive() {
  local pid="$1"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

# iso_to_epoch <iso8601> — convert ISO-8601 UTC string to epoch seconds
iso_to_epoch() {
  local iso="$1"
  # macOS / BSD date
  if date -jf '%Y-%m-%dT%H:%M:%SZ' "$iso" +%s 2>/dev/null; then
    return
  fi
  # GNU date
  date -d "$iso" +%s 2>/dev/null || echo "0"
}

# read_lock <lockfile> — emit the JSON lockfile contents, or empty object if absent/corrupt
read_lock() {
  local lockfile="$1"
  if [[ -f "$lockfile" ]]; then
    jq '.' "$lockfile" 2>/dev/null || echo '{"holder":null,"queue":[]}'
  else
    echo '{"holder":null,"queue":[]}'
  fi
}

# write_lock_atomic <lockfile> <json> — write JSON atomically via temp+mv
write_lock_atomic() {
  local lockfile="$1"
  local json="$2"
  local tmpfile
  tmpfile="$(dirname "$lockfile")/.$(basename "$lockfile").tmp.$$"
  printf '%s\n' "$json" > "$tmpfile"
  mv -f "$tmpfile" "$lockfile"
}

# is_stale <holder_json> — returns 0 if holder is stale, 1 otherwise
is_stale() {
  local holder_json="$1"
  local pid started_at epoch_started epoch_now age

  pid=$(printf '%s' "$holder_json" | jq -r '.pid // 0')
  started_at=$(printf '%s' "$holder_json" | jq -r '.started_at // ""')

  # If PID is alive, definitely not stale
  if pid_alive "$pid"; then
    return 1
  fi

  # PID is dead — check age
  if [[ -z "$started_at" ]]; then
    # No timestamp, treat as stale (PID dead and no record of when it started)
    return 0
  fi

  epoch_started=$(iso_to_epoch "$started_at")
  epoch_now=$(date +%s 2>/dev/null || echo "0")
  age=$(( epoch_now - epoch_started ))

  if [[ "$age" -ge "$STALE_THRESHOLD" ]]; then
    return 0
  fi

  # PID dead but recently started (within STALE_THRESHOLD) — treat as stale anyway
  # because a dead holder cannot release the lock
  return 0
}

# ---------------------------------------------------------------------------
# Subcommand: status
# ---------------------------------------------------------------------------
cmd_status() {
  local lockfile="$1"
  read_lock "$lockfile"
}

# ---------------------------------------------------------------------------
# Subcommand: acquire
# ---------------------------------------------------------------------------
cmd_acquire() {
  local lockfile="$1"
  local bead_id="$2"
  local surface="$3"
  local my_pid="$$"
  local start_time
  start_time=$(date +%s 2>/dev/null || echo "0")
  local waited=0

  echo "==> [session-close-lock] acquire: bead=$bead_id surface=$surface pid=$my_pid" >&2

  while true; do
    local lock_json holder holder_pid holder_null

    lock_json=$(read_lock "$lockfile")
    holder=$(printf '%s' "$lock_json" | jq -r 'if .holder then "present" else "null" end')
    holder_null=$(printf '%s' "$lock_json" | jq '.holder == null')

    # --- Case 1: No holder → acquire immediately ---
    if [[ "$holder_null" == "true" ]]; then
      local new_lock
      new_lock=$(printf '%s' "$lock_json" | jq \
        --arg bead_id "$bead_id" \
        --arg surface "$surface" \
        --argjson pid "$my_pid" \
        --arg started_at "$(now_iso)" \
        '.holder = {bead_id: $bead_id, surface: $surface, pid: $pid, started_at: $started_at}
         | .queue = [.queue[] | select(.bead_id != $bead_id)]')
      write_lock_atomic "$lockfile" "$new_lock"
      echo "==> [session-close-lock] acquired immediately (no prior holder)" >&2
      return 0
    fi

    # --- Case 2: Stale holder → auto-clear and retry ---
    local holder_json
    holder_json=$(printf '%s' "$lock_json" | jq '.holder')
    if is_stale "$holder_json"; then
      local stale_bead stale_pid
      stale_bead=$(printf '%s' "$holder_json" | jq -r '.bead_id // "unknown"')
      stale_pid=$(printf '%s' "$holder_json" | jq -r '.pid // 0')
      echo "==> [session-close-lock] stale holder detected (bead=$stale_bead pid=$stale_pid) — auto-clearing" >&2

      # Promote queue head as new holder, or clear
      local queue_length
      queue_length=$(printf '%s' "$lock_json" | jq '.queue | length')

      if [[ "$queue_length" -eq 0 ]]; then
        # No queue — just clear holder, let this caller acquire fresh
        local cleared
        cleared=$(printf '%s' "$lock_json" | jq '.holder = null | .queue = []')
        write_lock_atomic "$lockfile" "$cleared"
      else
        # Promote first in queue
        local next_entry new_holder_json promoted
        next_entry=$(printf '%s' "$lock_json" | jq '.queue[0]')
        new_holder_json=$(printf '%s' "$next_entry" | jq \
          --arg started_at "$(now_iso)" \
          'del(.queued_at) | . + {pid: 0, started_at: $started_at}')
        promoted=$(printf '%s' "$lock_json" | jq \
          --argjson holder "$new_holder_json" \
          '.holder = $holder | .queue = .queue[1:]')
        write_lock_atomic "$lockfile" "$promoted"
      fi
      # Immediately retry without sleeping
      continue
    fi

    # --- Case 3: Active holder — queue ourselves if not already queued, then wait ---
    local already_queued
    already_queued=$(printf '%s' "$lock_json" | jq \
      --arg bead_id "$bead_id" \
      '[.queue[] | select(.bead_id == $bead_id)] | length > 0')

    if [[ "$already_queued" == "false" ]]; then
      local new_entry enqueued
      new_entry=$(jq -cn \
        --arg bead_id "$bead_id" \
        --arg surface "$surface" \
        --arg queued_at "$(now_iso)" \
        '{bead_id: $bead_id, surface: $surface, queued_at: $queued_at}')
      enqueued=$(printf '%s' "$lock_json" | jq --argjson entry "$new_entry" '.queue += [$entry]')
      write_lock_atomic "$lockfile" "$enqueued"

      local current_holder
      current_holder=$(printf '%s' "$lock_json" | jq -r '.holder.bead_id // "unknown"')
      local queue_pos
      queue_pos=$(printf '%s' "$enqueued" | jq \
        --arg bead_id "$bead_id" \
        '[.queue[] | .bead_id] | index($bead_id) + 1')
      echo "==> [session-close-lock] queued (position $queue_pos, waiting for holder: $current_holder)" >&2
    fi

    # Check timeout
    local now_time elapsed
    now_time=$(date +%s 2>/dev/null || echo "0")
    elapsed=$(( now_time - start_time ))
    if [[ "$elapsed" -ge "$LOCK_TIMEOUT" ]]; then
      echo "==> [session-close-lock] ERROR: timed out after ${elapsed}s waiting for lock" >&2
      # Remove ourselves from queue
      local dequeued
      dequeued=$(read_lock "$lockfile" | jq \
        --arg bead_id "$bead_id" \
        '.queue = [.queue[] | select(.bead_id != $bead_id)]')
      write_lock_atomic "$lockfile" "$dequeued" 2>/dev/null || true
      exit 1
    fi

    echo "==> [session-close-lock] waiting ${LOCK_POLL_INTERVAL}s (elapsed: ${elapsed}s)" >&2
    sleep "$LOCK_POLL_INTERVAL"

    # Re-read lock — maybe we're now the head of queue and the holder released
    lock_json=$(read_lock "$lockfile")
    local head_bead
    head_bead=$(printf '%s' "$lock_json" | jq -r '.queue[0].bead_id // ""')

    # Are we now first in queue and holder is gone/stale?
    if [[ "$head_bead" == "$bead_id" ]]; then
      local holder_null_check
      holder_null_check=$(printf '%s' "$lock_json" | jq '.holder == null')
      if [[ "$holder_null_check" == "true" ]]; then
        # Promote ourselves from queue to holder
        local promoted_self
        promoted_self=$(printf '%s' "$lock_json" | jq \
          --arg bead_id "$bead_id" \
          --arg surface "$surface" \
          --argjson pid "$my_pid" \
          --arg started_at "$(now_iso)" \
          '.holder = {bead_id: $bead_id, surface: $surface, pid: $pid, started_at: $started_at}
           | .queue = .queue[1:]')
        write_lock_atomic "$lockfile" "$promoted_self"
        echo "==> [session-close-lock] promoted from queue — acquired" >&2
        return 0
      fi
    fi
  done
}

# ---------------------------------------------------------------------------
# Subcommand: release
# ---------------------------------------------------------------------------
cmd_release() {
  local lockfile="$1"

  if [[ ! -f "$lockfile" ]]; then
    echo "==> [session-close-lock] release: lockfile not found ($lockfile)" >&2
    return 1
  fi

  local lock_json queue_length next_holder

  lock_json=$(read_lock "$lockfile")
  queue_length=$(printf '%s' "$lock_json" | jq '.queue | length')

  echo "==> [session-close-lock] releasing lock (queue length: $queue_length)" >&2

  if [[ "$queue_length" -eq 0 ]]; then
    # No queue — just clear the holder entirely
    local cleared
    cleared=$(printf '%s' "$lock_json" | jq '.holder = null | .queue = []')
    write_lock_atomic "$lockfile" "$cleared"
    echo "==> [session-close-lock] released — no queue, lock is free" >&2
  else
    # Promote first queued entry to holder
    local next_entry new_holder promoted
    next_entry=$(printf '%s' "$lock_json" | jq '.queue[0]')
    new_holder=$(printf '%s' "$next_entry" | jq \
      --arg started_at "$(now_iso)" \
      'del(.queued_at) | . + {pid: 0, started_at: $started_at}')
    promoted=$(printf '%s' "$lock_json" | jq \
      --argjson holder "$new_holder" \
      '.holder = $holder | .queue = .queue[1:]')
    write_lock_atomic "$lockfile" "$promoted"
    next_holder=$(printf '%s' "$new_holder" | jq -r '.bead_id // "unknown"')
    echo "==> [session-close-lock] released — promoted next holder: $next_holder" >&2
  fi

  return 0
}

# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------
SUBCOMMAND="${1:-}"
shift || true

case "$SUBCOMMAND" in
  acquire)
    [[ $# -ge 3 ]] || { echo "Usage: session-close-lock.sh acquire <lockfile> <bead_id> <surface>" >&2; exit 1; }
    cmd_acquire "$1" "$2" "$3"
    ;;
  release)
    [[ $# -ge 1 ]] || { echo "Usage: session-close-lock.sh release <lockfile>" >&2; exit 1; }
    cmd_release "$1"
    ;;
  status)
    [[ $# -ge 1 ]] || { echo "Usage: session-close-lock.sh status <lockfile>" >&2; exit 1; }
    cmd_status "$1"
    ;;
  *)
    echo "Usage: session-close-lock.sh <acquire|release|status> <lockfile> [<bead_id> <surface>]" >&2
    exit 1
    ;;
esac
