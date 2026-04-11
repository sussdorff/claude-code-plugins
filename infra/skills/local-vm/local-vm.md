# Local VM Manager Skill

Manage local and remote virtual machines across different hypervisors. This skill detects VM metadata from SSH config and can start/stop/check VMs before establishing connections.

## Supported Hypervisors

| Hypervisor | SSH Config Tag | Location | CLI Tool |
|------------|----------------|----------|----------|
| Parallels | `@parallels-vm: <name>` | Local macOS | `prlctl` |
| Hyper-V | `@hyperv-vm: <name>` | Remote Windows (e.g., Elysium) | `PowerShell` via SSH |
| QEMU/libvirt | `@qemu-vm: <name>` | Local/Remote Linux | `virsh` |
| Proxmox | `@proxmox-vm: <id>` | Remote Proxmox host | `qm` via SSH |

## SSH Config Metadata Format

Add metadata comments BEFORE the Host line in `~/.ssh/config` or `~/.ssh/config.d/*`:

```ssh-config
# @server-type: windows
# @parallels-vm: Windows 11 (Solutio)
Host charly-dev
    User malte
    HostName localhost
    ProxyCommand nc $(/Users/malte/.ssh/scripts/parallels-vm-ip.sh "Windows 11 (Solutio)") 22
    ...
```

## When to Use This Skill

Use this skill when:
- SSH connection to a server fails with "Could not find IP" or similar VM-not-running errors
- You need to start/stop/check status of a local or remote VM
- Setting up new VM entries in SSH config

## VM Management Commands

### Check VM Status

**Parallels (local):**
```bash
prlctl list -a | grep -i "<vm-name>"
```

**Hyper-V (remote on Windows host):**
```bash
ssh <windows-host> "powershell -Command \"Get-VM -Name '<vm-name>' | Select-Object Name,State\""
```

**QEMU/libvirt (local or remote):**
```bash
virsh list --all | grep "<vm-name>"
# or remote:
ssh <host> "virsh list --all | grep '<vm-name>'"
```

**Proxmox (remote):**
```bash
ssh <proxmox-host> "qm status <vmid>"
```

### Start VM

**Parallels:**
```bash
# If stopped:
prlctl start "<vm-name>"
# If suspended/paused:
prlctl resume "<vm-name>"
```

**Hyper-V:**
```bash
ssh <windows-host> "powershell -Command \"Start-VM -Name '<vm-name>'\""
```

**QEMU/libvirt:**
```bash
virsh start "<vm-name>"
```

**Proxmox:**
```bash
ssh <proxmox-host> "qm start <vmid>"
```

### Stop VM

**Parallels:**
```bash
prlctl stop "<vm-name>"
# or graceful:
prlctl stop "<vm-name>" --acpi
```

**Hyper-V:**
```bash
ssh <windows-host> "powershell -Command \"Stop-VM -Name '<vm-name>' -Force\""
```

**QEMU/libvirt:**
```bash
virsh shutdown "<vm-name>"
# or force:
virsh destroy "<vm-name>"
```

**Proxmox:**
```bash
ssh <proxmox-host> "qm shutdown <vmid>"
# or force:
ssh <proxmox-host> "qm stop <vmid>"
```

## Workflow: SSH Connection Fails

When an SSH connection fails due to VM not running:

1. **Parse SSH config** to find the server's VM metadata
2. **Identify hypervisor** from the metadata tag
3. **Check VM status** using appropriate CLI
4. **Start/resume VM** if not running
5. **Wait for VM to get IP** (usually 10-30 seconds)
6. **Retry SSH connection**

Example for Parallels:
```bash
# 1. Check status
prlctl list -a | grep "Windows 11 (Solutio)"
# Output: {uuid} suspended - Windows 11 (Solutio)

# 2. Resume if suspended
prlctl resume "Windows 11 (Solutio)"

# 3. Wait for IP
sleep 15

# 4. Retry SSH
ssh charly-dev "echo connected"
```

## Adding New VM to SSH Config

When setting up a new VM-backed SSH host:

1. Determine the hypervisor type
2. Add the appropriate metadata tag
3. Configure the connection (direct IP or ProxyCommand for dynamic IP)

### Example: Parallels with Dynamic IP
```ssh-config
# @server-type: windows
# @parallels-vm: MyWindowsVM
Host my-windows
    User myuser
    HostName localhost
    ProxyCommand nc $(/Users/malte/.ssh/scripts/parallels-vm-ip.sh "MyWindowsVM") 22
    IdentityFile ~/.ssh/my_key
    StrictHostKeyChecking no
```

### Example: Hyper-V on Remote Windows Host
```ssh-config
# @server-type: vm
# @hyperv-vm: CharlyVM
# @hyperv-host: Elysium
Host ElysiumVM
    User charly
    HostName <static-ip>
    IdentityFile ~/.ssh/solutio_master_key
    ProxyJump Elysium
```

### Example: Future Proxmox Setup
```ssh-config
# @server-type: vm
# @proxmox-vm: 100
# @proxmox-host: proxmox-server
Host my-proxmox-vm
    User root
    HostName <vm-ip>
    ProxyJump proxmox-server
```

## Server Discovery

The `scripts/server_info.py` script parses SSH config metadata and provides both CLI and programmatic access to server information. It reads `~/.ssh/config` and `~/.ssh/config.d/*` files, extracting metadata from `# @key: value` comments.

### Supported Metadata Tags

| Tag | Description | Example |
|-----|-------------|---------|
| `@server-type` | Server type (windows, vm, etc.) | `# @server-type: windows` |
| `@platform` | OS platform | `# @platform: windows-11` |
| `@vm-host` | VM host reference | `# @vm-host: dev-vm` |
| `@host-machine` | Physical host machine | `# @host-machine: server1` |
| `@parallels-vm` | Parallels VM name | `# @parallels-vm: Windows 11 (Solutio)` |

### CLI Usage

```bash
# List all servers
python ~/.claude/skills/local-vm/scripts/server_info.py list

# List with verbose details
python ~/.claude/skills/local-vm/scripts/server_info.py list -v

# Filter by server type
python ~/.claude/skills/local-vm/scripts/server_info.py list --type windows -v

# Only servers with metadata
python ~/.claude/skills/local-vm/scripts/server_info.py list --metadata-only

# Show details for a specific server
python ~/.claude/skills/local-vm/scripts/server_info.py show charly-dev
```

### Programmatic Usage

```python
import sys
sys.path.insert(0, str(Path.home() / ".claude/skills/local-vm/scripts"))
from server_info import get_server_info, list_servers, clear_cache

# Get info for a specific server
info = get_server_info("charly-dev")
if info:
    print(info.name, info.type, info.hostname)

# List all Windows servers
windows = list_servers(type="windows")

# List servers that have metadata annotations
annotated = list_servers(with_metadata_only=True)

# Force reload from disk (cache TTL is 5 minutes)
clear_cache()
```

### Cache Behavior

Server information is cached in memory for 5 minutes (300s TTL). Use `clear_cache()` programmatically or restart the script to force a reload.

## Troubleshooting

### Parallels VM won't start
```bash
# Check if Parallels is running
pgrep -x "prl_client_app" || open -a "Parallels Desktop"

# Check VM configuration issues
prlctl problem-report "<vm-name>" --dump
```

### Can't get VM IP (Parallels)
```bash
# List all IPs for VM
prlctl exec "<vm-name>" ipconfig  # Windows
prlctl exec "<vm-name>" ip addr   # Linux
```

### Hyper-V VM stuck
```bash
ssh Elysium "powershell -Command \"
    \$vm = Get-VM -Name '<vm-name>'
    if (\$vm.State -eq 'Paused') { Resume-VM -Name '<vm-name>' }
    elseif (\$vm.State -eq 'Off') { Start-VM -Name '<vm-name>' }
    elseif (\$vm.State -eq 'Saved') { Start-VM -Name '<vm-name>' }
\""
```
