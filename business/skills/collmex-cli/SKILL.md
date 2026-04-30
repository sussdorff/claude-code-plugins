---
disable-model-invocation: true
name: collmex-cli
model: haiku
description: CLI wrapper for Collmex Buchhaltung Pro API. Use when managing vendors, invoices, open items, bookings, or generating ZUGFeRD XML. Triggers on Collmex, accounting, invoices, payables, vendors, Buchhaltung, Lieferanten, offene Posten.
requires_standards: [english-only]
---

# collmex-cli - Collmex Accounting CLI

LLM-friendly CLI wrapper for the Collmex Buchhaltung Pro API.

**Repo:** `~/code/finance-projects/collmex-cli/`

## When to Use

- Looking up vendors, open items, or bookings in Collmex
- Creating a vendor invoice or matching bank transactions to vendors
- Checking unmatched bank entries that need receipts or invoices
- Generating ZUGFeRD XML or sending invoices via email
- Querying accounting data with JSON output for further analysis

## Prerequisites

Environment variables (or `.env` file in working directory):

```bash
export COLLMEX_CUSTOMER_ID="your_customer_id"
export COLLMEX_COMPANY_ID="1"          # usually 1
export COLLMEX_USERNAME="your_username"
export COLLMEX_PASSWORD="your_password"
```

Additional optional config for SMTP (invoice-send) and ZUGFeRD (buyer info) -- see Configuration section below.

## Common Commands

### Test Connection

```bash
collmex test
```

### Vendors (Lieferanten)

| Task | Command |
|------|---------|
| List all vendors | `collmex vendors` |
| Search vendors | `collmex vendors --search "Amazon"` |
| Filter by ID | `collmex vendors --id 123` |
| JSON output | `collmex vendors --json` |
| Create vendor | `collmex vendor-create --company "Supplier GmbH" --city "Berlin" --email "info@supplier.de"` |
| Update vendor | `collmex vendor-update --vendor-id 123 --street "Neue Str. 1" --vat-id "DE123456789"` |

Full vendor-create options — see [`scripts/vendor-create.sh`](scripts/vendor-create.sh) for the complete multi-flag example.

### Vendor Matching

Match a vendor by IBAN, VAT ID, or name (fuzzy). Priority: IBAN > VAT ID > Name.

```bash
collmex vendor-match --iban "DE89370400440532013000"
collmex vendor-match --vat-id "DE123456789"
collmex vendor-match --name "Amazon" --json
```

### Open Items (Offene Posten)

| Task | Command |
|------|---------|
| Vendor open items | `collmex open-items --vendor` |
| Customer open items | `collmex open-items --customer` |
| Filter by vendor ID | `collmex open-items --vendor --vendor-id 123` |
| JSON output | `collmex open-items --vendor --json` |

### Bookings (Buchungen)

| Task | Command |
|------|---------|
| All bookings | `collmex bookings` |
| Filter by account | `collmex bookings --account 1200` |
| Filter by date range | `collmex bookings --from 2024-01-01 --to 2024-12-31` |
| Filter by vendor | `collmex bookings --vendor-id 123` |
| Search text | `collmex bookings --search "Amazon"` |
| Filter by year | `collmex bookings --year 2024` |
| JSON output | `collmex bookings --json` |

### Unmatched Bank Transactions

Find bank entries without matching invoices/receipts:

```bash
collmex unmatched                          # Default account 1200
collmex unmatched --account 1200           # Specific bank account
collmex unmatched --from 2024-01-01 --to 2024-03-31
collmex unmatched --json
```

### Vendor Invoices (Lieferantenrechnungen)

Create a vendor invoice (books expense in accounting) — see [`scripts/vendor-invoice.sh`](scripts/vendor-invoice.sh) for a full example with all options.

Optional flags: `--tax <amount>` (auto-calculated if empty), `--account <number>` (default: 3200), `--cost-center <name>`, `--json`.

### ZUGFeRD XML Generation

Generate EN 16931 compliant XML for a vendor invoice — see [`scripts/zugferd-create.sh`](scripts/zugferd-create.sh) for a full example.

Optional flags: `--qty <quantity>`, `--buyer-id <id>`, `--due 2024-02-15`, `--notes "..."`.

Requires buyer config (COLLMEX_BUYER_* environment variables).

### Send Invoice via Email

Send PDF (with optional ZUGFeRD XML) to accounting:

```bash
collmex invoice-send invoice.pdf
collmex invoice-send invoice.pdf --xml factur-x.xml
collmex invoice-send invoice.pdf --to buchhaltung@example.de --subject "Rechnung Jan"
```

Requires SMTP config (COLLMEX_SMTP_* environment variables).

### Bank Statements

Query bank transactions (requires playwright-cli auth state):

```bash
collmex bank-statements -a "<account>" --from DD.MM.YYYY --json
collmex bank-statements --all --status pending --json
```

Status values: `pending` (zu buchen), `deferred` (spaeter), `excluded` (nicht buchen), `booked`.

Useful for: finding EUR amounts for foreign currency invoices (USD etc.).

## Workflow: Matching Bank Transactions

1. Import bank statement (MT940) via Collmex Web UI
2. Find unmatched transactions:
   ```bash
   collmex unmatched --json
   ```
3. For each unmatched transaction, find or create the vendor:
   ```bash
   collmex vendor-match --iban "DE..." --json
   # If no match: collmex vendor-create --company "..." --iban "..."
   ```
4. Create vendor invoice:
   ```bash
   collmex vendor-invoice --vendor-id 123 --invoice "INV-001" --date 2024-01-15 --net 50.00
   ```

## Workflow: ZUGFeRD mit Vendor-Abgleich

1. PDF lesen, Rechnungsdaten + Vendor-Stammdaten extrahieren
2. Vendor matchen:
   ```bash
   collmex vendor-match --name "Tesla Germany" --json
   ```
3. **Vendor-Daten vergleichen** (Rechnung vs. Collmex):
   - Adresse, USt-IdNr, Firmenname pruefen
   - Fehlende Daten -> `vendor-update`
   - Kein Match -> `vendor-create` (mit User-Bestaetigung)
4. Bei Fremdwaehrung (USD): EUR-Betrag von Bank holen:
   ```bash
   collmex bank-statements -a "Fyrst" --from DD.MM.YYYY --json
   ```
5. ZUGFeRD erzeugen (validiert Pflichtfelder automatisch):
   ```bash
   collmex zugferd-create --vendor-id 123 --invoice "INV-001" --date 2024-01-15 --net 50.00
   ```

## JSON Output

All query commands support `--json` / `-j` for LLM-friendly output:

```bash
collmex vendors --json | jq '.[] | select(.city == "Berlin")'
collmex open-items --vendor --json | jq '.[] | select(.days_overdue > 30)'
collmex bookings --json | jq '[.[] | .amount] | add'
```

## Configuration Reference

### Required (API)

| Variable | Description |
|----------|-------------|
| `COLLMEX_CUSTOMER_ID` | Collmex customer ID |
| `COLLMEX_COMPANY_ID` | Company ID (usually `1`) |
| `COLLMEX_USERNAME` | API username |
| `COLLMEX_PASSWORD` | API password |

### Optional (SMTP - for invoice-send)

| Variable | Description |
|----------|-------------|
| `COLLMEX_SMTP_HOST` | SMTP server hostname |
| `COLLMEX_SMTP_PORT` | SMTP port (default: 587) |
| `COLLMEX_SMTP_USER` | SMTP username |
| `COLLMEX_SMTP_PASSWORD` | SMTP password |
| `COLLMEX_SMTP_FROM` | Sender email address |
| `COLLMEX_ACCOUNTING_EMAIL` | Default recipient for invoices |

### Optional (Buyer - for ZUGFeRD)

| Variable | Description |
|----------|-------------|
| `COLLMEX_BUYER_NAME` | Your company name |
| `COLLMEX_BUYER_STREET` | Street address |
| `COLLMEX_BUYER_ZIP` | Postal code |
| `COLLMEX_BUYER_CITY` | City |
| `COLLMEX_BUYER_COUNTRY` | Country code (default: DE) |
| `COLLMEX_BUYER_VAT_ID` | USt-IdNr |
| `COLLMEX_BUYER_EMAIL` | Contact email |

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `Authentication failed` | Wrong credentials | Check COLLMEX_USERNAME/PASSWORD |
| `Configuration error` | Missing env vars | Ensure COLLMEX_CUSTOMER_ID, USERNAME, PASSWORD are set |
| `Collmex API error` | API-level error | Check error message, verify parameters |
| `Buyer configuration missing` | ZUGFeRD without buyer | Set COLLMEX_BUYER_* env vars |
| `SMTP not configured` | invoice-send without SMTP | Set COLLMEX_SMTP_* env vars |

## API Coverage

| Record Type | API Identifier | Operations |
|-------------|---------------|------------|
| Vendors | `VENDOR_GET` / `CMXLIF` | Query, create |
| Vendor Invoices | `CMXLRN` | Create |
| Open Items | `OPEN_ITEMS_GET` / `OPEN_ITEM` | Query |
| Bookings | `ACCDOC_GET` / `ACCDOC` | Query |

## Do NOT

- Do NOT create vendor invoices (`collmex vendor-invoice`) without verifying the vendor-id exists first via `collmex vendors --id <id>`. WHY: Collmex silently accepts invalid vendor IDs and creates orphaned bookings that require manual cleanup in the web UI.
- Do NOT use `collmex vendor-create` without checking for duplicates first via `collmex vendor-match`. WHY: duplicate vendors cause split open items and inconsistent payment tracking.
- Do NOT send invoices via `collmex invoice-send` without explicit user confirmation of the recipient address. WHY: emails with financial documents sent to wrong addresses are a GDPR violation and cannot be recalled.
- Do NOT guess expense account numbers -- verify with `collmex bookings --account <number>` that the account exists and is appropriate. WHY: wrong account numbers (e.g., revenue instead of expense) corrupt the P&L and require manual correction by an accountant.
- Do NOT modify Collmex data for fiscal years that are already closed. WHY: closed fiscal years may have been submitted to the tax office; modifications create legal compliance issues.

## Output Format

Collmex API returns CSV with semicolons. The CLI wraps this as JSON with `--json`:
```
collmex vendors --json         # JSON array of vendor records
collmex open-items --vendor    # Table: Vendor, Invoice, Amount, Due
collmex bookings --json | jq '[.[] | .amount] | add'
```

## Limitations

- Read-only for bookings and open items (no modifications via CLI)
- Bank statement import (MT940) must be done via Collmex Web UI. WHY: the API does not support MT940 upload; only the web interface handles bank statement parsing.
- ZUGFeRD generation only for single-line-item invoices (multi-line requires scripting)
- No customer invoice creation (vendor-side only)
