# Elysium Host Details

## Hardware Specs

| Component   | Spec                                    |
| ----------- | --------------------------------------- |
| CPU         | AMD Ryzen AI 9 HX 370 (12C/24T, Zen 5) |
| RAM         | 128 GB DDR5-5600                        |
| Storage     | Samsung 990 PRO 4TB NVMe               |
| Network     | 2x Realtek 2.5GbE + WiFi 6             |
| OS          | Proxmox VE 9.1                          |

## VMs (Proxmox)

| VMID | Name | IP | RAM | Purpose |
|------|------|----|-----|---------|
| 100 | homeassistant | 192.168.2.100 | 8 GB | Critical — smart home control |
| 200 | shikigami | 192.168.60.63 (DHCP) | 8 GB | 24/7 Agent VM (OpenClaw) |
| 201 | hokora | 192.168.60.51 | 4 GB | Dev-VM (Claude Code + tmux) |

## LXCs (Proxmox)

| CTID | Name | IP | Port | Service |
|------|------|----|------|---------|
| 101 | ignis | 192.168.60.10 | — | Ignis |
| 102 | proxy | 192.168.60.5 | 80/443 | Reverse Proxy |
| 105 | ollama | 192.168.60.15 | 11434 | Ollama |
| 106 | plex | 192.168.60.16 | 32400 | Plex + SABnzbd + *arr |
| 107 | immich | 192.168.60.17 | 2283 | Immich (Photos) |
| 108 | paperless | 192.168.60.18 | — | Paperless-ngx |
| 109 | calibre-web | 192.168.60.19 | 8083 | Calibre-Web |
| 110 | audiobookshelf | 192.168.60.20 | 13378 | Audiobookshelf |
| 111 | mailpiler | 192.168.60.21 | 8080 | Mailpiler |
| 112 | komga | 192.168.60.22 | 25600 | Komga (Comics) |
| 113 | monitoring | 192.168.60.23 | 3000/9090 | Prometheus + Grafana |
| 114 | mira | 192.168.60.24 | — | MIRA |
| 115 | netbird | — | — | NetBird routing peer |
| 116 | services | 192.168.60.30 | 3307 | Dolt Server |

## IP Ranges (VLAN 60)

LXCs: .5–.24 | VMs: .50–.63 | Services: .30

Config repo: `~/code/house-projects/elysium-proxmox/`

## LXC Services Detail

### LXC 108 — Paperless-ngx

- **Paperless-ngx**: LXC 108 on Elysium, Samba consume folder for scanner input.
- **ScanSnap iX1600**: WiFi → SMB → Paperless consume folder. NOT USB passthrough to LXC (fragile device paths, udev issues). Domain field in ScanSnap Home = "WORKGROUP" for standalone Samba.

## Setting Up New Claude Code VMs

New VMs are always created from scratch — **never clone** existing VMs.
Setup scripts live in `~/code/house-projects/elysium-proxmox/vm/<name>/`.

```bash
# 1. Create VM on Proxmox (cloud-init: Ubuntu 24.04, Node.js, Docker, Claude Code)
ssh root@192.168.2.3 'bash -s' < vm/<name>/setup-vm.sh

# 2. Deploy Claude Code config from Mac (settings, plugins, beads)
bash vm/<name>/deploy.sh
```

Each VM needs two scripts:
- `setup-vm.sh` — runs on Proxmox host, creates VM + cloud-init
- `deploy.sh` — runs from Mac via SSH, configures Claude Code + plugins

Key config targets on the VM:
- `~/.claude/settings.json` — plugins, hooks, permissions
- `~/.claude/plugins/known_marketplaces.json` — plugin sources
- Beads Dolt: `bd dolt set mode server && bd dolt set host 192.168.60.30`
