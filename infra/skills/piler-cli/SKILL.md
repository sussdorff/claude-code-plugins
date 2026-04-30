---
disable-model-invocation: true
name: piler-cli
model: haiku
description: CLI for searching and reading emails from Mailpiler archive on Proxmox. Use when querying archived emails, searching mail history, or reading past messages. Triggers on mailpiler, mail archive, piler search, alte mails, mail suchen, email archiv.
requires_standards: [english-only]
---

# piler-cli

CLI to search, read, and export emails from the Mailpiler archive running on Proxmox LXC 111.

## When to Use

- You need to find an old email by subject, sender, or keyword in the mail archive
- You want to read the full content of an archived email including attachments
- You need to check archive statistics or IMAP import job status
- You want to search emails within a specific date range or from a specific domain

## Do NOT

- Do NOT modify or delete archived emails — the archive is read-only
- Do NOT use for current mailbox management — use Fastmail MCP instead

## Output Format

Search results list emails with metadata. Use `piler read` for full content:
```
piler search "invoice"    # List: Date, From, Subject, Size
piler read <id>           # Full email body + attachment list
```

## Location

```
~/code/piler-cli/
```

## Commands

Run via: `scripts/piler-commands.sh <stats|search|list|read> [args...]`

Or invoke `uv run piler <command>` directly from `~/code/piler-cli`:
```bash
uv run piler stats
uv run piler search "rechnung"
uv run piler list --from cognovis.de --limit 20
uv run piler read 115022
```

## Search Tips

- **Email addresses in search**: Manticore tokenizes `@` and `.` to spaces. Search for name parts instead: `"malte sussdorff"` not `"malte@sussdorff.de"`
- **Field-specific search**: Use `-f sender`, `-f rcpt`, `-f subject`, `-f body`
- **List vs search**: `list` queries MySQL (exact filters, date ranges). `search` queries Manticore (full-text, fuzzy matching).
- **Domains in list**: `--from cognovis.de` filters by fromdomain. `--from malte@cognovis.de` filters by exact sender.

## Architecture

- Transport: local Mac → SSH to Proxmox host (192.168.2.3) → pct exec 111 → docker exec
- Search engine: Manticore Search (MySQL protocol, port 9306)
- Metadata DB: MariaDB in mysql_piler container
- Email retrieval: `pilerget` binary decrypts stored emails
- Queries are base64-encoded to avoid nested shell quoting issues

## Import Status

`piler stats` shows IMAP import jobs. Status meanings:
- PENDING (0): Not started yet
- RUNNING (1): Downloading emails (progress shows downloaded/total after pilerimport runs)
- FINISHED (2): Complete

Note: During IMAP download phase, "imported" stays at 0 because pilerimport only runs after ALL emails are downloaded from IMAP.

## Known Limitations

- No REST API — all access is via SSH/Docker exec chain
- Read requires SSH connectivity to Proxmox host
- Large result sets from Manticore may be truncated (default LIMIT 20)
- EML parsing strips HTML tags but doesn't render them perfectly
