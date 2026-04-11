# Parallels Network Troubleshooting Guide

## Problem Summary

When the Mac changes network adapters (switching WiFi, docking/undocking, VPN changes), Parallels VMs can lose connectivity because:

1. **Bridged adapters become invalid** - The VM was bridged to an adapter that's no longer active
2. **Shared (NAT) network works but uses internal IPs** - 10.211.55.x IPs only reachable from host Mac
3. **VM suspended/resumed on different network** - IP cached by Parallels may be stale
4. **SSH service not started** - Windows SSH/OpenSSH may not be running after resume

## Diagnostic Steps

### 1. Check VM Status and IP
```bash
prlctl list -f "<vm-name>"
# Shows: UUID, STATUS, IP_ADDR, NAME
```

### 2. Check VM Network Adapter Type
```bash
prlctl list -i "<vm-name>" | grep -E "net[0-9]"
# Example output:
#   net0 (+) type=shared mac=001C422579D5 card=virtio     <- NAT network
#   net0 (+) type=bridged mac=001C422579D5 card=virtio    <- Bridged network
```

### 3. Check Mac's Active Network Interface
```bash
# Find which interface is currently active
route get default | grep interface
# Example: interface: en12

# Get IP on that interface
ifconfig en12 | grep "inet "
# Example: inet 192.168.2.120 netmask 0xffffff00
```

### 4. Check Available Parallels Network Adapters
```bash
prlsrvctl net list
# Shows all bridged adapters and which Mac interfaces they're bound to
```

### 5. Test Connectivity to VM
```bash
# Test ping (may be blocked by Windows firewall)
ping -c 2 -t 5 <vm-ip>

# Test SSH port
nc -zv -w 5 <vm-ip> 22
```

## Common Issues and Fixes

### Issue: VM Using Shared (NAT) Network Instead of Bridged

**Symptoms:**
- VM IP is 10.211.55.x (Parallels internal range)
- Can't reach VM from other machines on network
- SSH works from Mac but times out

**Fix:** Switch to bridged network (requires VM stop)
```bash
# 1. Stop VM
prlctl stop "<vm-name>"

# 2. List available bridged networks
prlsrvctl net list | grep bridged

# 3. Set to bridged on active adapter
prlctl set "<vm-name>" --device-set net0 --type bridged

# 4. Or specify exact adapter
prlctl set "<vm-name>" --device-set net0 --type bridged --iface "en12"

# 5. Start VM
prlctl start "<vm-name>"

# 6. Wait for IP and verify
sleep 30
prlctl list -f "<vm-name>"
```

### Issue: Bridged Adapter Bound to Wrong/Inactive Interface

**Symptoms:**
- VM shows no IP or old IP
- Mac switched from WiFi to Ethernet (or vice versa)
- `prlsrvctl net list` shows VM bridged to disconnected interface

**Fix:** Update bridged adapter binding
```bash
# 1. Find current active Mac interface
route get default | grep interface

# 2. Stop VM
prlctl stop "<vm-name>"

# 3. Rebind to active interface
prlctl set "<vm-name>" --device-set net0 --type bridged --iface "<active-interface>"

# 4. Start VM
prlctl start "<vm-name>"
```

### Issue: VM Suspended/Resumed - Stale IP

**Symptoms:**
- `prlctl list -f` shows old IP
- VM actually has different IP or no IP

**Fix:** Refresh VM network
```bash
# Option 1: Restart VM networking from inside (if you can connect)
ssh <vm> "ipconfig /release && ipconfig /renew"  # Windows
ssh <vm> "sudo dhclient -r && sudo dhclient"     # Linux

# Option 2: Reset VM network adapter
prlctl set "<vm-name>" --device-set net0 --disconnect
prlctl set "<vm-name>" --device-set net0 --connect

# Option 3: Full VM restart
prlctl restart "<vm-name>"
```

### Issue: Windows SSH Service Not Running After Resume

**Symptoms:**
- VM has valid IP, ping works
- SSH connection refused or times out
- Port 22 not listening

**Fix:** Start SSH service
```bash
# If you can use prlctl exec (Parallels Tools installed):
prlctl exec "<vm-name>" "powershell -Command \"Start-Service sshd\""

# Or via Parallels GUI: open VM and manually start OpenSSH service

# Verify SSH is listening:
prlctl exec "<vm-name>" "powershell -Command \"Get-Service sshd | Select Status\""
prlctl exec "<vm-name>" "netstat -an | findstr :22"
```

## Recommended SSH Config for Parallels VMs

For VMs that may change IPs, use a ProxyCommand with dynamic IP lookup:

```ssh-config
# @server-type: windows
# @parallels-vm: Windows 11 (Solutio)
Host charly-dev
    User malte
    HostName localhost
    ProxyCommand nc $(/Users/malte/.ssh/scripts/parallels-vm-ip.sh "Windows 11 (Solutio)") 22
    IdentityFile ~/.ssh/solutio_id_rsa
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ConnectTimeout 10
```

The `parallels-vm-ip.sh` script should:
```bash
#!/bin/bash
VM_NAME="$1"
prlctl list -f "$VM_NAME" 2>/dev/null | tail -1 | awk '{print $3}'
```

## Preventive Measures

### 1. Use "Default" Bridged Adapter
Setting the VM to use the "Default" bridged adapter (FF:FF:FF:FF:FF:FF) lets Parallels auto-select the active interface:
```bash
prlctl set "<vm-name>" --device-set net0 --type bridged --iface "Default"
```

### 2. Add Multiple Network Adapters
Add both shared and bridged adapters - shared always works from host:
```bash
# Keep net0 as shared (always works from Mac)
prlctl set "<vm-name>" --device-set net0 --type shared

# Add net1 as bridged (for network access)
prlctl set "<vm-name>" --device-add net --type bridged
```

### 3. Static IP in VM (if network supports it)
Configure Windows/Linux with a static IP in the bridged network range.

### 4. Wake-on-LAN Style Check Before SSH
Update parallels-vm-ip.sh to verify connectivity:
```bash
#!/bin/bash
VM_NAME="$1"
MAX_WAIT=60

# Ensure VM is running
STATE=$(prlctl list "$VM_NAME" 2>/dev/null | tail -1 | awk '{print $2}')
if [[ "$STATE" != "running" ]]; then
    prlctl start "$VM_NAME" >/dev/null 2>&1 || prlctl resume "$VM_NAME" >/dev/null 2>&1
fi

# Wait for valid IP
for i in $(seq 1 $MAX_WAIT); do
    IP=$(prlctl list -f "$VM_NAME" 2>/dev/null | tail -1 | awk '{print $3}')
    if [[ -n "$IP" && "$IP" != "-" ]]; then
        # Verify port 22 is reachable
        if nc -z -w 1 "$IP" 22 2>/dev/null; then
            echo "$IP"
            exit 0
        fi
    fi
    sleep 1
done

echo "ERROR: Could not get valid IP for $VM_NAME" >&2
exit 1
```

## Automatic Network Recovery

When a VM is unreachable, follow this diagnostic and recovery flow:

### Step 1: Diagnose the Problem

```bash
# Get VM name, status, and reported IP
VM_NAME="Windows 11 (Solutio)"
prlctl list -f "$VM_NAME"

# Check network adapter type
prlctl list -i "$VM_NAME" | grep -E "net[0-9]"
# Output: net0 (+) type=shared ...    <- NAT (10.211.55.x)
# Output: net0 (+) type=bridged ...   <- Direct LAN IP

# Get Mac's current active interface and IP
ACTIVE_IFACE=$(route -n get default 2>/dev/null | grep interface | awk '{print $2}')
echo "Active interface: $ACTIVE_IFACE"
ifconfig "$ACTIVE_IFACE" | grep "inet "
```

### Step 2: Check Routing Issues

```bash
VM_IP=$(/Users/malte/.ssh/scripts/parallels-vm-ip.sh "$VM_NAME")
echo "VM reports IP: $VM_IP"

# Check how traffic to VM IP is routed
route -n get "$VM_IP"
# PROBLEM if gateway is VPN (utun*) or wrong interface for 10.211.55.x
# OK if interface is bridge101 (shared) or your LAN interface (bridged)
```

**Common routing problems:**
- `10.211.55.x` routed via `utun*` → VPN is capturing Parallels subnet
- `10.211.55.x` routed via LAN gateway → Parallels shared network bridge broken
- Bridged IP routed via wrong interface → Adapter mismatch

### Step 3: Fix Based on Problem

#### Problem: VPN Capturing Parallels Shared Network (10.211.55.x via utun*)

**Best fix:** Switch to bridged networking to avoid VPN conflict:
```bash
# Find active LAN interface
ACTIVE_IFACE=$(route -n get default 2>/dev/null | grep interface | awk '{print $2}')

# Switch VM to bridged on active interface
prlctl set "$VM_NAME" --device-set net0 --type bridged --iface "$ACTIVE_IFACE"
prlctl restart "$VM_NAME"

# Wait and verify
sleep 20
prlctl list -f "$VM_NAME"
```

#### Problem: Bridged to Wrong/Inactive Interface

```bash
# List available Parallels bridged networks
prlsrvctl net list | grep bridged

# Find active interface
ACTIVE_IFACE=$(route -n get default 2>/dev/null | grep interface | awk '{print $2}')
echo "Should be bridged to: $ACTIVE_IFACE"

# Rebind to active interface
prlctl set "$VM_NAME" --device-set net0 --type bridged --iface "$ACTIVE_IFACE"
prlctl restart "$VM_NAME"
```

#### Problem: Shared Network Bridge Broken (ping fails even without VPN)

```bash
# Try reconnecting the adapter first
prlctl set "$VM_NAME" --device-disconnect net0
sleep 2
prlctl set "$VM_NAME" --device-connect net0
sleep 5
ping -c 2 -t 3 "$VM_IP"

# If still broken, switch to bridged
ACTIVE_IFACE=$(route -n get default 2>/dev/null | grep interface | awk '{print $2}')
prlctl set "$VM_NAME" --device-set net0 --type bridged --iface "$ACTIVE_IFACE"
prlctl restart "$VM_NAME"
```

### Step 4: Verify Recovery

```bash
VM_IP=$(/Users/malte/.ssh/scripts/parallels-vm-ip.sh "$VM_NAME")
echo "New VM IP: $VM_IP"

# Test connectivity
ping -c 2 -t 3 "$VM_IP" && echo "Ping OK" || echo "Ping FAILED"
nc -zv -w 5 "$VM_IP" 22 && echo "SSH port OK" || echo "SSH port FAILED"

# Test SSH
ssh -o ConnectTimeout=10 charly-dev "hostname"
```

## Hardware Adapter Change Handling

When switching Ethernet adapters (docking/undocking, different USB adapters):

### Recommended: Use Bridged with Explicit Interface Binding

```bash
# After connecting new adapter, find its interface name
networksetup -listallhardwareports | grep -A2 "USB\|Ethernet"

# Update VM binding
ACTIVE_IFACE=$(route -n get default 2>/dev/null | grep interface | awk '{print $2}')
prlctl set "$VM_NAME" --device-set net0 --type bridged --iface "$ACTIVE_IFACE"

# No restart needed if VM already running - just reconnect adapter
prlctl set "$VM_NAME" --device-disconnect net0
prlctl set "$VM_NAME" --device-connect net0
```

### Note on "Default" Adapter

The `prlsrvctl net list` shows a "Default" bridged network with `FF:FF:FF:FF:FF:FF`, but setting `--iface "Default"` doesn't work via CLI. The Default adapter auto-selection only works when configured through Parallels GUI.

**Workaround:** Create a script that detects the active interface and rebinds:

```bash
#!/bin/bash
# ~/.ssh/scripts/parallels-rebind-network.sh
VM_NAME="${1:-Windows 11 (Solutio)}"
ACTIVE_IFACE=$(route -n get default 2>/dev/null | grep interface | awk '{print $2}')

if [[ -z "$ACTIVE_IFACE" ]]; then
    echo "ERROR: No active network interface found" >&2
    exit 1
fi

echo "Rebinding $VM_NAME to $ACTIVE_IFACE..."
prlctl set "$VM_NAME" --device-set net0 --type bridged --iface "$ACTIVE_IFACE"
prlctl set "$VM_NAME" --device-disconnect net0
sleep 1
prlctl set "$VM_NAME" --device-connect net0
sleep 5

NEW_IP=$(prlctl list -f "$VM_NAME" 2>/dev/null | tail -1 | awk '{print $3}')
echo "VM IP: $NEW_IP"
```

## Quick Recovery Checklist

When SSH to Parallels VM fails:

1. [ ] Check VM is running: `prlctl list -a | grep "<vm-name>"`
2. [ ] Start/resume if needed: `prlctl start "<vm-name>"` or `prlctl resume "<vm-name>"`
3. [ ] Get current IP: `prlctl list -f "<vm-name>"`
4. [ ] Check network type: `prlctl list -i "<vm-name>" | grep net0`
5. [ ] **Check routing**: `route -n get <vm-ip>` - is it going to correct interface?
6. [ ] **If routed via VPN (utun*)**: Switch to bridged networking on active LAN interface
7. [ ] If shared (10.211.55.x) not routed via bridge101: Reconnect adapter or switch to bridged
8. [ ] If bridged with wrong IP: Rebind to current active interface
9. [ ] Test connectivity: `ping -c 2 <ip> && nc -zv -w 5 <ip> 22`
10. [ ] If port closed: Start SSH service in VM via `prlctl exec` or GUI
