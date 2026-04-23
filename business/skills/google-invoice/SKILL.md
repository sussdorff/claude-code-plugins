---
name: google-invoice
model: sonnet
description: Download Google One AI Pro invoice from payments.google.com, generate ZUGFeRD XML, and send to accounting. Triggers on google rechnung, google invoice, google one beleg, google one rechnung.
disableModelInvocation: true
---

# Google Invoice Skill

Downloads the latest Google One invoice from payments.google.com via playwright-cli,
generates ZUGFeRD XML via collmex-cli, and creates a Mail draft to buchhaltung@cognovis.de.

**Session:** `google` (playwright-cli persistent session)
**Vendor:** Google Commerce Limited (Collmex vendor_id: 72163)

## When to Use

- Download and process latest Google One AI Pro invoice
- Monthly accounting workflow for Google subscriptions

Do NOT use for: YouTube Premium, Google Workspace, or other Google services.

## Prerequisites

- playwright-cli session `google` must be authenticated
  - If session expired: `playwright-cli -s=google open --headed "https://payments.google.com"` → login manually → close
- collmex-cli must have valid .env credentials

## Workflow

### Step 1: Open Google Payments Activity

```bash
playwright-cli -s=google open "https://payments.google.com/gp/w/home/activity"
```

Check snapshot: if redirected to accounts.google.com login page, STOP and tell user:
"Google Session abgelaufen. Bitte einmal manuell einloggen:
`playwright-cli -s=google open --headed https://payments.google.com/gp/w/home/activity`"

### Step 2: Find latest Google One transaction

Take a snapshot and look for rows containing "Google One" in the activity table.
The table is inside an iframe. Rows look like:

```
row "Google One 1. März · Google AI Pro (2 TB) (Google One) −21,99 €" [ref=XXXXX]
```

Click on the FIRST (most recent) Google One row.

### Step 3: Extract invoice details from detail panel

After clicking, a detail panel opens with:
- **Date**: e.g. "Sonntag, 1. März" → extract YYYY-MM-DD
- **Net amount**: from table row (e.g. "18,48 €")
- **VAT**: from "Umsatzsteuer" row (e.g. "3,51 €")
- **Total**: from "Gesamt" row (e.g. "21,99 €")
- **Description**: e.g. "Google AI Pro (2 TB) (Google One)"

Also find the **"Rechnung mit ausgewiesener Umsatzsteuer herunterladen"** button.

### Step 4: Download invoice PDF

```bash
playwright-cli -s=google click <download-button-ref>
```

The PDF downloads to `.playwright-cli/<filename>.pdf`.
The filename is the invoice number (e.g. `5756272823891336-4.pdf`).

Extract the invoice number from the filename (strip .pdf extension).

### Step 5: Copy PDF to Buchhaltung

```bash
cp .playwright-cli/<filename>.pdf "/Users/malte/Documents/cognovis/Buchhaltung/<YYYY>/<YYYY-MM-DD> - cognovis - beleg - google.pdf"
```

Where YYYY-MM-DD is the invoice date from Step 3.

### Step 6: Generate ZUGFeRD XML

See [`scripts/zugferd-create.sh`](scripts/zugferd-create.sh) for the full zugferd-create command with all required fields (vendor-id 72163, buyer-id, tax-rate 19.0).

### Step 7: Send to Buchhaltung via Apple Mail

Create a visible draft (never auto-send). See [`scripts/send-to-buchhaltung.sh`](scripts/send-to-buchhaltung.sh) for the full AppleScript Mail draft workflow (attaches both PDF and XML).

### Step 8: Close browser and report

```bash
playwright-cli -s=google close
```

Report summary:
- Invoice number, date, amount
- Files created (PDF + XML paths)
- Mail draft status

## Reference Data

| Field | Value |
|-------|-------|
| Vendor | Google Commerce Limited |
| Collmex vendor_id | 72163 |
| VAT ID | IE9825613N |
| Buyer ID (Billing ID) | 9045-3453-2608 |
| Tax rate | 19% (German VAT, charged by Google) |
| Product | Google AI Pro (2 TB) (Google One) |
| Monthly amount | ~21,99 EUR brutto / ~18,48 EUR netto |
| Payment | PayPal (malte.sussdorff@cognovis.de) |
| Buchhaltung target | buchhaltung@cognovis.de |
| File naming | `YYYY-MM-DD - cognovis - beleg - google.{pdf,xml}` |
| Storage | `/Users/malte/Documents/cognovis/Buchhaltung/YYYY/` |

## Date Parsing

Google Payments shows German month names. Map to month numbers:
- Jan.=01, Feb.=02, März=03, Apr.=04, Mai=05, Juni=06
- Juli=07, Aug.=08, Sept.=09, Okt.=10, Nov.=11, Dez.=12

If no year shown, assume current year.
