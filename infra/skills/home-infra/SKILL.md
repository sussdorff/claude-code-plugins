---
name: home-infra
model: haiku
description: >-
  Home infrastructure overview - hardware, network, services, and CLI tools.
  Use when finding what runs where, choosing CLI tools, or planning infra changes.
  Triggers on home infra, home network, what devices, home server, infrastructure.
requires_standards: [english-only]
---

# Home Infrastructure Overview

## When to Use

- Finding which device or service runs at a specific IP or on which host
- Choosing the right CLI tool for a home infrastructure task
- Looking up VLAN layout, network topology, or DNS configuration
- Planning changes to Proxmox VMs/LXCs or home server services
- Checking which project repo contains config for a specific service

## Network Topology

```
Internet (Telekom FTTH)
    │
Fritz!Box (192.168.178.1) ─── Modem/Bridge
    │
UniFi Dream Wall (192.168.178.2 WAN / 192.168.2.1 LAN) ─── Gateway/Router/Firewall
    │
    ├── VLANs managed by UniFi
    │   ├── Management (192.168.2.0/24) ─── Infra devices
    │   ├── Sussdorff (main WLAN + LAN)
    │   ├── IoT (smart home devices)
    │   ├── AirBnB (guest network)
    │   ├── Dachgeschoss (top floor guest)
    │   ├── Gaeste (general guest)
    │   └── NordVPN (routed through VPN)
    │
    ├── Switches
    │   ├── USW Büro (US8P60, PoE) ─── Office
    │   ├── USW Keller (US8P60, PoE) ─── Basement
    │   ├── USW Wohnzimmer (USWED8P) ─── Living room
    │   └── USW Dachgeschoss (USWED8P) ─── Top floor
    │
    └── Access Points
        ├── Büro Malte (UAL6) ─── Office
        ├── Büro Jenny (U7NHD) ─── Office
        ├── AirBnB (U7NHD) ─── Guest apartment
        ├── Dachgeschoss (U7LR) ─── Top floor
        └── Gartenhaus (U7MSH) ─── Garden (often offline)
```

## DNS

### Local DNS (LAN)

UniFi Gateway handles local DNS. Pi-hole on infra-vm (192.168.2.6) is legacy and
no longer actively used. WHY: DNS was consolidated to UniFi Gateway for single-point
management. Previously switched to NextDNS but verify current WAN DNS settings in
UniFi OS if unsure.

### Public DNS (Domains)

All public DNS is managed via `hcloud` CLI (aliased through 1Password).
→ Load `references/dns-and-networking.md` for full `hcloud` commands, zone IDs, ScanSnap, Paperless, and NetBird details.

## Key Devices & Services

### Elysium (192.168.2.3) — Home Server

AMD Ryzen AI 9 HX 370, 128 GB RAM, Proxmox VE 9.1.
→ Load `references/elysium-hosts.md` for full VMs/LXCs tables, IP ranges, and VM setup guide.

### Home Assistant (192.168.2.5:8123 / VM 100)

Full Home Assistant OS running as Proxmox VM on Elysium.
Manages: Homematic IP (via CCU3), Shelly, Hue, various integrations.

### RaspberryMatic / CCU3 (raspberrymatic.local)

Homematic CCU3 hub for HomeMatic IP devices (thermostats, window sensors, switches).
Runs RaspberryMatic OS.

### Malte's Workstation

MacBook Pro M4 Max — primary development machine (192.168.2.120 typically).

## CLI Tools

| Tool       | Manages              | Install / Location                   | Config                          |
| ---------- | -------------------- | ------------------------------------ | ------------------------------- |
| `hcloud`   | Hetzner Cloud + DNS  | `brew install hcloud`                | via 1Password plugin (`op`)     |
| `ui`       | UniFi network        | `pip install unifi-cli` (ui-cli)     | `~/.config/ui-cli/config`       |
| `hass-cli` | Home Assistant       | `pip install homeassistant-cli`      | env vars via dotenv             |
| `ccu-cli`  | Homematic CCU3       | `~/code/house-projects/ccu-cli/`     | `~/.config/ccu-cli/config.toml` |
| `ssh`      | Elysium (Proxmox)    | built-in                             | `ssh elysium`                   |

Run: `scripts/cli-overview.sh` for a combined snapshot across all tools.

Individual commands:
```bash
ui lo devices list        # UniFi network devices
ui lo clients list        # UniFi connected clients
hass-cli state list       # Home Assistant entities
ccu-cli device list       # Homematic CCU3 devices
ssh elysium "qm list"     # Proxmox VMs
```

→ Load `references/related-projects.md` for full project list and related skills.

## Do NOT

- Do NOT assume device IPs are static without checking DHCP reservations via `ui lo clients list`. WHY: devices may have changed IPs since last documented.
- Do NOT modify DNS records without first listing existing RRSets. WHY: `add-records` appends — use `set-records` to replace.
- Do NOT use Pi-hole for DNS configuration — it is legacy. WHY: UniFi Gateway handles local DNS.
- Do NOT SSH into Elysium and make manual Proxmox changes without updating `~/code/house-projects/elysium-proxmox/`. WHY: Infrastructure as Code rule.
- Do NOT assume the Gartenhaus AP is reachable. WHY: frequently offline.
- Do NOT default to VLAN 60 for new services without checking inter-VLAN routing.
- Do NOT clone VMs or LXCs. Always create from scratch with setup scripts. WHY: clones carry leftover config — every machine must be reproducible via its setup script.
- Do NOT use bare product domains for demo/staging environments. WHY: use `demo.<domain>` subdomain instead.
