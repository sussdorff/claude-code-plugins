#!/usr/bin/env bash
# Quick overview of home infrastructure via CLI tools.
# Shows UniFi devices/clients, Home Assistant entities, Homematic devices,
# and Proxmox VM list.

set -euo pipefail

echo "=== UniFi network devices ==="
ui lo devices list

echo ""
echo "=== UniFi connected clients ==="
ui lo clients list

echo ""
echo "=== Home Assistant entities ==="
hass-cli state list

echo ""
echo "=== Homematic CCU3 devices ==="
ccu-cli device list

echo ""
echo "=== Proxmox VMs on Elysium ==="
ssh elysium "qm list"
