---
disable-model-invocation: true
name: local-vm
model: haiku
description: Manage local and remote VMs across Parallels, Hyper-V, QEMU, and Proxmox. Use when SSH fails due to stopped VMs, or to start/stop/check VM status. Triggers on VM not running, SSH failed, start vm, parallels, hyper-v, qemu, proxmox.
requires_standards: [english-only]
---

# Local VM Manager

Manage local and remote virtual machines across hypervisors. Detects VM metadata from SSH config and starts/stops/checks VMs before establishing connections.

## When to Use

- SSH connection fails with "Could not find IP" or VM-not-running errors
- Start/stop/check status of a local or remote VM
- Setting up new VM entries in SSH config
- Troubleshooting VM networking (bridged, NAT)

## Supported Hypervisors

| Hypervisor | SSH Config Tag | CLI Tool |
|------------|----------------|----------|
| Parallels | `@parallels-vm: <name>` | `prlctl` |
| Hyper-V | `@hyperv-vm: <name>` | `PowerShell` via SSH |
| QEMU/libvirt | `@qemu-vm: <name>` | `virsh` |
| Proxmox | `@proxmox-vm: <id>` | `qm` via SSH |

## Workflow: SSH Connection Fails

1. Parse SSH config to find the server's VM metadata
2. Identify hypervisor from the metadata tag
3. Check VM status using appropriate CLI
4. Start/resume VM if not running
5. Wait for VM to get IP (usually 10-30 seconds)
6. Retry SSH connection

## Resources

- `local-vm.md` -- Full VM management commands, SSH config format, troubleshooting
- `parallels-network-troubleshooting.md` -- Parallels-specific network fixes
- `scripts/server_info.py` -- SSH config metadata parser (CLI + programmatic)

## Do NOT

- Force-stop VMs without trying graceful shutdown first. WHY: force-stop risks filesystem corruption on the guest OS
- Start VMs without checking status first. WHY: starting an already-running VM causes errors or duplicates
- Modify SSH config without preserving metadata comments. WHY: metadata tags are the VM discovery mechanism
