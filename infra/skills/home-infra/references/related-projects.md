# Related Projects and Skills

## Related Projects

| Project                                       | Purpose                          |
| --------------------------------------------- | -------------------------------- |
| `~/code/house-projects/`                      | All home projects                |
| `~/code/house-projects/elysium-proxmox/`      | Proxmox migration planning       |
| `~/code/house-projects/homeassistant/`         | HA config and docs               |
| `~/code/house-projects/ccu-cli/`              | Homematic CLI tool               |
| `~/code/house-projects/pi-hole/`              | Pi-hole config (legacy)          |
| `~/code/house-projects/evcc/`                  | EV charging                      |
| `~/code/house-projects/hydraulic-balance-viewer/` | Heating system balancing      |
| `~/code/house-projects/media-vm/`              | Media server (future/unused)     |
| `~/code/house-projects/ui-cli/`               | UniFi CLI tool                   |

## Related Skills (Detailed Usage)

For command details and advanced usage, load the specific skill:

- **ui-cli** — UniFi device lookup, client management, DHCP reservations
- **hass-cli** — HA state queries, service calls, history, statistics
- **ccu-cli** — Homematic device management, thermostats, schedules

## CLI Quick Reference (Extended)

```bash
# UniFi — WiFi networks
ui lo networks list

# UniFi — VLANs and networks
ui lo wlans list

# Home Assistant — specific entity state
hass-cli state get sensor.xxx

# Homematic — room list
ccu-cli room list

# Homematic — read a datapoint
ccu-cli datapoint get <device> <dp>
```
