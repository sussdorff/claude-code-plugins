#!/usr/bin/env bash
# UniFi CLI commands that require confirmation (-y flag).
# Wraps write operations with automatic confirmation bypass for non-interactive use.
# Usage: confirmed-commands.sh <operation> [args...]

set -euo pipefail

CMD="${1:?operation required}"
shift

case "$CMD" in
  set-ip)
    ui lo clients set-ip "$@" -y
    ;;
  rename)
    ui lo clients rename "$@" -y
    ;;
  kick)
    ui lo clients kick "$@" -y
    ;;
  block)
    ui lo clients block "$@" -y
    ;;
  unblock)
    ui lo clients unblock "$@" -y
    ;;
  restart-device)
    ui lo devices restart "$@" -y
    ;;
  upgrade-device)
    ui lo devices upgrade "$@" -y
    ;;
  revoke-voucher)
    ui lo vouchers revoke "$@" -y
    ;;
  delete-apgroup)
    ui lo apgroups delete "$@" -y
    ;;
  *)
    echo "Unknown operation: $CMD" >&2
    echo "Available: set-ip, rename, kick, block, unblock, restart-device, upgrade-device, revoke-voucher, delete-apgroup" >&2
    exit 1
    ;;
esac
