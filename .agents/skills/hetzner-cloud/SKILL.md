---
name: hetzner-cloud
model: haiku
description: Manage Hetzner Cloud infrastructure via hcloud CLI and Robot. Use when creating/modifying DNS records, managing servers, switching projects, or transferring domains. Triggers on hetzner, hcloud, dns zone, domain transfer, nameserver.
---

# Hetzner Cloud

Manage Hetzner Cloud infrastructure: DNS zones, servers, and domain registration via API and Robot.

Triggers: hetzner, hetzner cloud, hetzner dns, hetzner robot, domain transfer, dns zone, nameserver

## When to Use

- Adding, updating, or removing DNS records for a domain
- Setting up a new domain with Fastmail MX/DKIM/SPF/DMARC records
- Switching between Hetzner Cloud projects (Default vs Shikigami)
- Transferring a .de domain to Hetzner Robot
- Migrating DNS zones from another provider (cPanel, etc.)

## Projects

| Project | Purpose | 1Password Item | Item ID |
|---------|---------|----------------|---------|
| **Default** | DNS zones, servers (erp4projects), general infra | `Hetzner Cloud - Default` | `xdxjwlnfkgjl2bnkwxq7rqf77u` |
| **Shikigami** | Dedicated project | `Hetzner Cloud - Shikigami` | `tmtmfkzwjtrf57bjpp44qiwloq` |

**Default project = Default.** All DNS zones and the erp4projects server live here. WHY: always verify active project before making changes — wrong project = wrong infrastructure.

## hcloud CLI & 1Password Shell Plugin

The `hcloud` CLI uses the **1Password Shell Plugin** for authentication. It does NOT use `HCLOUD_TOKEN` from the environment - it reads credentials from the plugin config.

**Plugin config:** `~/.config/op/plugins/hcloud.json`

### Check which token is active

```bash
# Show current 1Password item ID used by hcloud
jq -r '.credentials[0].item_id' ~/.config/op/plugins/hcloud.json
# Then look up the item name:
# xdxjwlnfkgjl2bnkwxq7rqf77u = Default
# tmtmfkzwjtrf57bjpp44qiwloq = Shikigami
```

### Switch between projects

```bash
# Switch to Default project
jq '.credentials[0].item_id = "xdxjwlnfkgjl2bnkwxq7rqf77u"' \
  ~/.config/op/plugins/hcloud.json > /tmp/hcloud.json \
  && mv /tmp/hcloud.json ~/.config/op/plugins/hcloud.json

# Switch to Shikigami project
jq '.credentials[0].item_id = "tmtmfkzwjtrf57bjpp44qiwloq"' \
  ~/.config/op/plugins/hcloud.json > /tmp/hcloud.json \
  && mv /tmp/hcloud.json ~/.config/op/plugins/hcloud.json

# Verify switch worked
hcloud server list
```

### Direct API calls (bypasses plugin)

```bash
# If you need to use a specific token regardless of plugin config:
HCLOUD_TOKEN=$(op item get xdxjwlnfkgjl2bnkwxq7rqf77u --vault "API Keys" --fields token --reveal)
curl -s -H "Authorization: Bearer ${HCLOUD_TOKEN}" "https://api.hetzner.cloud/v1/..."
```

## DNS Management via `hcloud zone` CLI

**Primary method: `hcloud zone` subcommands.** No separate DNS API token needed — uses
the same 1Password Shell Plugin as all other hcloud commands.

`hcloud zone` is aliased as `hcloud dns` and `hcloud zones`.

### CRITICAL: Record name format

**Names MUST be relative to the zone, NOT FQDNs:**
- `@` for zone apex (e.g., `cognovis.de` itself)
- `mail` not `mail.cognovis.de`
- `fm1._domainkey` not `fm1._domainkey.cognovis.de`
- `*.c4b` not `*.c4b.cognovis.de`
- `_imaps._tcp` not `_imaps._tcp.cognovis.de`

If you use FQDNs, the zone gets appended again → `mail.cognovis.de.cognovis.de` (broken!)

**Values for CNAME/SRV/MX MUST use trailing dot for FQDNs:**
- `production.cognovis.de.` (with dot)
- `imap.fastmail.com.` (with dot)

### List zones

```bash
hcloud zone list
```

### Create zone

```bash
hcloud zone create --name example.de --ttl 3600
```

### List records (RRSets)

```bash
# All records for a zone
hcloud zone rrset list 817812

# Filter by type
hcloud zone rrset list 817812 --type A
hcloud zone rrset list 817812 --type MX
hcloud zone rrset list 817812 --type CNAME
```

### Add records

```bash
# A record
hcloud zone add-records --record "80.147.143.115" --ttl 300 817812 comics A

# CNAME (trailing dot!)
hcloud zone add-records --record "example.de." --ttl 3600 817812 www CNAME

# MX (multiple records)
hcloud zone add-records \
  --record "10 in1-smtp.messagingengine.com." \
  --record "20 in2-smtp.messagingengine.com." \
  --ttl 3600 817812 @ MX

# TXT
hcloud zone add-records --record '"v=spf1 include:spf.messagingengine.com ?all"' --ttl 3600 817812 @ TXT

# SRV (priority weight port target)
hcloud zone add-records --record "0 1 993 imap.fastmail.com." --ttl 3600 817812 _imaps._tcp SRV
```

**Syntax:** `hcloud zone add-records --record <value> [--record <value>...] [--ttl <seconds>] <zone-id> <name> <type>`

If the RRSet doesn't exist yet, it is created automatically.

### Set records (replace all values)

```bash
# Replace ALL records for an RRSet (overwrites existing)
hcloud zone set-records --record "5.6.7.8" --ttl 3600 817812 mail A
```

**Use `set-records` to update/correct values** — it replaces the entire RRSet cleanly.

### Remove records

```bash
# Remove a specific value from an RRSet
hcloud zone remove-records --record "80.147.143.115" 817812 comics A
```

### Export/Import zone file (BIND format)

```bash
# Export
hcloud zone export-zonefile 817812

# Import (replaces ALL records!)
hcloud zone import-zonefile 817812 --file zone.txt
```

### Fallback: Direct API calls

Only use curl if `hcloud zone` doesn't support a specific operation:

```bash
HCLOUD_TOKEN=$(op item get xdxjwlnfkgjl2bnkwxq7rqf77u --vault "API Keys" --fields token --reveal)

# List RRSets via API
curl -s -H "Authorization: Bearer ${HCLOUD_TOKEN}" \
  "https://api.hetzner.cloud/v1/zones/817812/rrsets?per_page=100" \
  | jq '.rrsets[] | "\(.name) \(.type) \([.records[].value] | join(", "))"' -r

# Delete RRSet via API (if remove-records doesn't suffice)
curl -s -X DELETE -H "Authorization: Bearer ${HCLOUD_TOKEN}" \
  "https://api.hetzner.cloud/v1/zones/817812/rrsets/mail/A"
```

**WARNING (API only):** PUT often fails silently — returns HTTP 200 but keeps old values.
Prefer `hcloud zone set-records` over raw API PUT calls.

## DNS Verification

**Before NS delegation switch:** You CANNOT verify records via `dig @hydrogen.ns.hetzner.com` — Hetzner forwards to current authoritative NS. Only the API shows what's actually stored.

**After NS delegation switch:**
```bash
# Check DENIC delegation
dig @f.nic.de example.de NS +short

# Verify at Hetzner NS
dig @hydrogen.ns.hetzner.com example.de A +short
```

## Hetzner Nameservers

```
hydrogen.ns.hetzner.com
oxygen.ns.hetzner.com
helium.ns.hetzner.de
```

## Domain Registration (Robot)

**Robot URL:** https://robot.hetzner.com

### Domain transfer (.de)
1. Get Auth-Code from current registrar
2. Robot → Domains → New domain → Transfer
3. Enter domain + Auth-Code
4. DENIC processes in minutes to hours
5. NS set automatically from transfer request

### Current domains at Hetzner Robot
agilecastle.de, cognovis.de, erp4agencies.de, erp4projects.com, erp4translation.com, erp4translation.de, get-mira.de, getmira.de, ignis-ai.de, mira-pvs.de, openacs.de, playful-learning.de, shikigami.de, sussdorff.de, sussdorff.org

## DNS Zones (Cloud Console)

All in Default project:

| Zone | ID | Fastmail Account | MX | DKIM | SPF | DMARC | Notes |
|------|----|-----------------|-----|------|-----|-------|-------|
| agilecastle.de | 817794 | cognovis | OK | OK | OK | OK | |
| cognovis.de | 819365 | cognovis | OK | OK | OK | OK | Also M365, c4b cluster |
| erp4agencies.de | 817796 | cognovis | OK | OK | OK | OK | |
| erp4projects.com | 817798 | cognovis | OK | OK | OK | OK | |
| erp4translation.com | 817800 | cognovis | OK | OK | OK | OK | |
| erp4translation.de | 817802 | cognovis | OK | OK | OK | OK | |
| get-mira.de | 848667 | cognovis | OK | OK | OK | OK | MIRA product domain (hyphenated) |
| getmira.de | 848527 | cognovis | OK | OK | OK | OK | MIRA EHR/PVS Voice Assistant |
| ignis-ai.de | 848530 | cognovis | OK | OK | OK | OK | Ignis (MIRA Vorstufe) |
| mira-pvs.de | 848526 | cognovis | OK | OK | OK | OK | MIRA EHR/PVS Voice Assistant |
| openacs.de | 817805 | cognovis | OK | OK | OK | OK | |
| playful-learning.de | 817808 | cognovis | OK | OK | OK | OK | |
| shikigami.de | 848856 | cognovis | OK | OK | OK | OK | Personal brand domain |
| sussdorff.de | 817812 | sussdorff | OK | OK | OK | OK | Separate Fastmail account |
| sussdorff.org | 817814 | sussdorff | OK | OK | OK | OK | Separate Fastmail account |

**Fastmail MX config:** `10 in1-smtp.messagingengine.com.` / `20 in2-smtp.messagingengine.com.`
**DKIM pattern:** `fm{1,2,3}._domainkey` → `fm{1,2,3}.{domain}.dkim.fmhosted.com.`
**SPF:** `v=spf1 include:spf.messagingengine.com ?all`
**DMARC:** `v=DMARC1; p=none;` (at `_dmarc`)
**Fastmail SRV records** (for CardDAV/CalDAV/IMAP/SMTP autodiscovery in Apple Mail, iOS Contacts etc.):
```bash
hcloud zone add-records --record "0 1 993 imap.fastmail.com." 817812 _imaps._tcp SRV
hcloud zone add-records --record "0 1 465 smtp.fastmail.com." 817812 _submissions._tcp SRV
hcloud zone add-records --record "0 1 443 carddav.fastmail.com." 817812 _carddavs._tcp SRV
hcloud zone add-records --record "0 1 443 caldav.fastmail.com." 817812 _caldavs._tcp SRV
```
Without SRV records, clients attempt `.well-known/carddav` on the bare domain first — if nothing answers on port 443, autodiscovery hangs/times out.
**Last verified:** 2026-02-25

## DNS Changes + TLS Certificates

When changing A/CNAME records for domains served by Traefik (Let's Encrypt ACME TLS challenge):
- **DNS propagation delay**: Global resolvers cache old records (TTL typically 3600s). Let's Encrypt validates against its own resolvers, not yours.
- **Traefik auto-retries**: Failed ACME challenges are retried automatically — no manual intervention needed.
- **LE rate limits**: 5 failed authorizations per domain per hour. If you trigger this, wait for the cooldown (shown in Traefik error logs).
- **Verification**: Use `curl -k` to verify content is served while cert is pending. Check `docker logs netbird-traefik | grep -i acme` for cert status.

## Do NOT

- Do NOT use FQDNs as record names in `hcloud zone add-records`. WHY: the zone suffix gets appended automatically — `mail.cognovis.de` becomes `mail.cognovis.de.cognovis.de` (broken record).
- Do NOT use `hcloud zone import-zonefile` without exporting the current zone first. WHY: import replaces ALL records — any record not in the import file is permanently deleted.
- Do NOT use raw API PUT calls for DNS updates — use `hcloud zone set-records` instead. WHY: PUT often returns HTTP 200 but silently keeps old values — the CLI handles this correctly.
- Do NOT switch 1Password plugin config without verifying with `hcloud server list` after. WHY: the wrong project context means DNS changes go to the wrong zone — potentially breaking production domains.
- Do NOT forget trailing dots on CNAME/SRV/MX target values. WHY: without the trailing dot, the zone name gets appended to the target — creating a broken double-suffix record.
- Do NOT register a .de domain before the DNS zone is authoritative. WHY: DENIC runs a live pre-delegation check at registration time — if the zone isn't propagated to nameservers yet, registration fails with REFUSED/code 2305. Create the zone first, wait for propagation, then submit.
- Do NOT add a domain in Fastmail before setting DNS records. WHY: Fastmail verifies MX/DKIM/SPF/DMARC live on domain add — pre-set all records in Hetzner DNS first for instant verification.

## Reading DNS from cPanel (Serverprofis)

If migrating from a cPanel host, records are base64-encoded:

```bash
SP_TOKEN=$(op read "op://API Keys/SP-Server/Token")
curl -sk -H "Authorization: cpanel erpproje:${SP_TOKEN}" \
  "https://cp220.sp-server.net:2083/execute/DNS/parse_zone?zone=example.de" \
  | python3 -c '
import json, sys, base64
data = json.load(sys.stdin)
for r in data["data"]:
    if r["type"] != "record": continue
    name = base64.b64decode(r["dname_b64"]).decode()
    rtype = r["record_type"]
    vals = [base64.b64decode(v).decode() for v in r.get("data_b64", [])]
    if rtype == "SOA": continue
    print(f"{name:40s} {r.get(chr(116)+chr(116)+chr(108), chr(45)):>6} {rtype:6s} {chr(32).join(vals)}")
'
```
