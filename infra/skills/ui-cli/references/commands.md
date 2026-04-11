# UI-CLI Command Reference

## Local Controller Commands (`ui lo`)

### devices
```bash
ui lo devices list              # List all devices
ui lo devices get <identifier>  # Get device by MAC/name/IP
ui lo devices restart <id>      # Restart device
ui lo devices locate <id>       # Flash locate LED
ui lo devices adopt <id>        # Adopt pending device
```

### clients
```bash
ui lo clients list              # Connected clients
ui lo clients list --all       # Include offline/historical
ui lo clients get <mac>        # Client details
ui lo clients block <mac>      # Block client
ui lo clients unblock <mac>    # Unblock client
```

### wlans
```bash
ui lo wlans list               # List WiFi networks
ui lo wlans get <name>         # WLAN details
```

### networks
```bash
ui lo networks list            # List VLANs/networks
ui lo networks get <name>      # Network details
```

### apgroups
```bash
ui lo apgroups list                        # List AP groups
ui lo apgroups get <name>                  # Group details with APs
ui lo apgroups create <name>               # Create new group
ui lo apgroups delete <name>               # Delete group
ui lo apgroups add-device <group> <device> # Add AP to group
ui lo apgroups remove-device <group> <device>  # Remove AP
```

### vouchers
```bash
ui lo vouchers list            # List guest vouchers
ui lo vouchers create          # Create voucher
ui lo vouchers delete <id>     # Delete voucher
```

### events
```bash
ui lo events list              # Recent events
ui lo events list --limit 100 # More events
```

### stats
```bash
ui lo stats daily              # Daily statistics
ui lo stats hourly             # Hourly statistics
```

### health
```bash
ui lo health                   # Controller health check
```

## Global Options

```bash
--output/-o <format>   # table, json, csv, yaml
--quick/-q             # Short timeout (5s)
--timeout/-t <sec>     # Custom timeout
```

## Device Types

| type | Description |
|------|-------------|
| ugw  | Gateway/Router (UDM, USG) |
| usw  | Switch |
| uap  | Access Point |

## JSON Filtering Examples

```bash
# Get all APs with name and IP
ui lo devices list -o json | jq '.[] | select(.type == "uap") | {name, ip, mac}'

# Find client by partial hostname
ui lo clients list -o json | jq '.[] | select(.hostname | test("iphone"; "i"))'

# Get device IPs only
ui lo devices list -o json | jq -r '.[].ip'
```
