# DNS and Networking Details

## Public DNS — Hetzner Cloud via `hcloud`

**All public DNS is managed via `hcloud` CLI.** There is no separate Hetzner DNS
Console editor — everything runs through the Hetzner Cloud API.

```bash
# List all zones
hcloud zone list

# List records for a zone (e.g. sussdorff.de = Zone ID 817812)
hcloud zone rrset list 817812
hcloud zone rrset list 817812 --type A    # filter by type

# Create A record
hcloud zone add-records --record "80.147.143.115" --ttl 300 817812 comics A

# Create CNAME record
hcloud zone add-records --record "example.com." 817812 alias CNAME

# Remove a record
hcloud zone remove-records --record "80.147.143.115" 817812 comics A

# Export full zone file (BIND format)
hcloud zone export-zonefile 817812
```

**Important:** `hcloud` is aliased through 1Password (`op plugin run -- hcloud`)
for secure token management. WHY: tokens are never stored in plaintext — 1Password injects them at runtime. No separate DNS API token needed.

## Key DNS Zones

| Zone ID | Domain | Purpose |
|---------|--------|---------|
| 817812 | sussdorff.de | Personal/Elysium services |
| 819365 | cognovis.de | Business |
| 817794 | agilecastle.de | Agile coaching |

**Elysium services** (all A records -> 80.147.143.115, Caddy handles TLS):
photos, media, books, audiobooks, paperless, comics

## NetBird (Reverse Proxy)

Remote access via NetBird VPN with reverse proxy on sussdorff.org.

- **Reverse proxy config is UI-only** — no API endpoint for managing routes/policies. Services must be configured manually in the NetBird dashboard.
- **Custom domains require wildcard CNAME** (`*.sussdorff.org` -> NetBird VPS). Individual A-records per subdomain do NOT pass NetBird domain validation.
- **Subdomain strategy**: Use individual clean subdomains on sussdorff.org (dedicated reverse proxy domain) instead of wildcard on the primary business domain (cognovis.de).
