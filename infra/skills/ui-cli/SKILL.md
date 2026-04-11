---
name: ui-cli
model: haiku
description: CLI for querying UniFi network infrastructure. Use when finding devices, looking up client MAC/IP, checking network config, or listing WLANs. Triggers on UniFi, network clients, WiFi, AP, switch, gateway, device IP, device MAC.
disableModelInvocation: true
---

# UI-CLI - UniFi Network CLI

Query UniFi controllers for device and network information.

## When to Use

- Look up a device's IP or MAC address on the UniFi network
- List connected clients or find a specific client by hostname or manufacturer
- Set a fixed IP (DHCP reservation) for a device like Shelly or Homematic
- Check WLAN configurations or AP group assignments
- Find device info needed for Home Assistant integrations

## Prerequisites

UI-CLI must be configured with controller credentials in `~/.config/ui-cli/config`:

```
UNIFI_CONTROLLER_URL=https://192.168.1.1
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=secret
UNIFI_CONTROLLER_SITE=default
UNIFI_CONTROLLER_VERIFY_SSL=false
```

## Common Commands

### Find Devices (APs, Switches, Gateways)

```bash
ui lo devices list                    # All devices
ui lo devices list -o json           # JSON output for parsing
ui lo devices get "Büro AP"          # Specific device details
```

### Find Network Clients

```bash
ui lo clients list                   # All connected (online) clients
ui lo clients all                    # All known clients (including offline)
ui lo clients get aa:bb:cc:dd:ee:ff  # Specific client by MAC
```

### List WLANs

```bash
ui lo wlans list                     # All WiFi networks
ui lo wlans get "Sussdorff"         # Specific WLAN details
```

### List Networks (VLANs)

```bash
ui lo networks list                  # All network configurations
```

### AP Groups (Broadcasting Groups)

```bash
ui lo apgroups list                  # Which APs broadcast which WLANs
ui lo apgroups get "Office"         # Devices in a group
```

### Set Fixed IP (DHCP Reservation)

```bash
ui lo clients set-ip "Shelly Keller" 192.168.30.21 -y   # Set fixed IP (auto-kicks for DHCP renewal)
ui lo clients set-ip AA:BB:CC:DD:EE:FF 192.168.30.21 -y # Skip confirmation
ui lo clients set-ip "Device" 192.168.1.100 -y --no-kick # Don't auto-kick client
```

The `set-ip` command:
1. Creates a DHCP reservation for the client
2. Automatically kicks the client to force immediate DHCP renewal
3. Client reconnects with the new fixed IP

Use `--no-kick` if you want the client to get the new IP on next natural DHCP renewal.

### Rename Client

```bash
ui lo clients rename "old-name" "New Name" -y           # Rename a client
ui lo clients rename AA:BB:CC:DD:EE:FF "Display Name" -y
```

## Confirmation Prompts

**IMPORTANT:** Many commands require confirmation. Always use `-y` or `--yes` to skip interactive prompts.
WHY: Without `-y`, the CLI blocks waiting for stdin input that cannot be provided in non-interactive contexts.

```bash
# Commands that support -y:
ui lo clients set-ip ... -y
ui lo clients rename ... -y
ui lo clients kick ... -y
ui lo clients block ... -y
ui lo clients unblock ... -y
ui lo devices restart ... -y
ui lo devices upgrade ... -y
ui lo vouchers revoke ... -y
ui lo apgroups delete ... -y
```

## Output Formats

All commands support `-o/--output` with: `table` (default), `json`, `csv`, `yaml`

Use `json` for programmatic parsing:

```bash
ui lo devices list -o json | jq '.[] | select(.type == "uap") | {name, ip, mac}'
```

## Finding Device Info for Home Assistant

To find IP/MAC for HA integrations:

```bash
# Find all APs
ui lo devices list -o json | jq '.[] | select(.type == "uap") | {name, ip, mac}'

# Find specific device
ui lo devices get "Living Room AP" -o json | jq '{ip, mac}'

# Find client by hostname (use select twice, not "!= null")
ui lo clients list -o json | jq '.[] | select(.hostname) | select(.hostname | test("philips"; "i"))'

# Find client by manufacturer/OUI (e.g., Homematic, Shelly, Philips)
ui lo clients all -o json | jq '.[] | select(.oui) | select(.oui | test("eq-3|homematic"; "i"))'
```

**jq tip:** Avoid `!= null` in jq - it causes escaping issues. Use `select(.field)` to filter out nulls instead.

## Do NOT

- Do NOT use `ui lo devices restart` or `ui lo devices upgrade` without explicit user confirmation. WHY: restarting an AP or switch causes network downtime for all clients connected to that device.
- Do NOT use `ui lo clients block` without confirming the MAC address with the user. WHY: blocking the wrong client locks a device out of the network, requiring UniFi controller access to unblock.
- Do NOT use `ui lo clients set-ip` on a device that is currently serving critical infrastructure (e.g., NAS, CCU, HA). WHY: the auto-kick forces a reconnect and brief network interruption that can disrupt running services.
- Do NOT use `!= null` in jq filters -- use `select(.field)` instead. WHY: `!= null` causes shell escaping issues and unexpected jq behavior; `select(.field)` is the idiomatic null-safe pattern.

## Output Format

Default output is tables. Use `-o json` for machine-readable data with MAC, IP, hostname, uptime:
```
ui lo clients list           # Table of connected clients
ui lo devices list -o json   # JSON array of network devices
ui lo clients list -o json | jq '.[] | {name, ip, mac}'
```

## Command Reference

See [references/commands.md](references/commands.md) for full command list.
