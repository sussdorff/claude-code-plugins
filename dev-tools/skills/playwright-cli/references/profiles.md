# Playwright-CLI Profiles

Persistent Chromium profiles store cookies/sessions across runs.

**Location:** `~/.local/share/playwright-cli/profiles/<name>/`

> **Note:** Old `~/.agent-browser-profiles/` profiles are NOT compatible (Chrome version/flag mismatch causes SIGTRAP crash). New profiles must be created fresh.

**Profiles to create (re-auth needed):**
- `agenticcoding` - AgenticCoding.school (authenticated member area)
- `amazon-privat` - Amazon.de (authenticated, order history + invoices)
- `audiobookshelf` - Audiobookshelf (authenticated)
- `calibre` - Calibre-web (authenticated)
- `excalidraw` - Excalidraw (diagram export)
- `grafana` - Grafana monitoring (authenticated)
- `hetzner-dns` - Hetzner DNS console (authenticated)
- `immich` - Immich photo management (authenticated)
- `jellyfin` - Jellyfin media server (authenticated)
- `linkedin` - LinkedIn (authenticated)
- `mailpiler` - Mailpiler email archive (authenticated)
- `paperless` - Paperless-ngx (authenticated)
- `substack` - Substack (authenticated, paywalled content)

## Using a Profile

```bash
# Profile must be set at launch
playwright-cli open --profile=~/.local/share/playwright-cli/profiles/<name> <url>

# Named session with profile
playwright-cli -s=amazon open --profile=~/.local/share/playwright-cli/profiles/amazon-privat https://www.amazon.de

# Close before switching profiles
playwright-cli close
playwright-cli open --profile=~/.local/share/playwright-cli/profiles/linkedin https://www.linkedin.com
```

## Creating a New Profile

```bash
# 1. Create directory
mkdir -p ~/.local/share/playwright-cli/profiles/<name>
# 2. Open headed for manual login
playwright-cli open --headed --profile=~/.local/share/playwright-cli/profiles/<name> <login-url>
# 3. User logs in manually (NEVER enter passwords)
# 4. Session persists for future headless use
```
