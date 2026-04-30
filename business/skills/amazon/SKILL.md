---
name: amazon
model: sonnet
description: Amazon.de automation via playwright-cli with local purchases database. Use for downloading invoices, searching order history, or querying past purchases. Triggers on amazon rechnung, amazon bestellung, amazon order, was habe ich gekauft.
disableModelInvocation: true
requires_standards: [english-only]
---

# Amazon Skill

Authenticated Amazon.de automation via playwright-cli, with local purchases database for offline queries.

**Profile:** `~/.local/share/playwright-cli/profiles/amazon-privat/`
**DB:** `~/Library/Application Support/purchases/purchases.db`

## When to Use

- Download invoice/Rechnung for a specific order
- Search order history by product name or price
- Look up past purchases (offline via DB, or live on Amazon)
- Check order details, reviews, prices

Do NOT use for: creating Amazon accounts, entering payment info, or purchasing items without explicit user confirmation.

## Workflow: Find Purchase and Download Invoice

### Step 0: Check local database first

```bash
sqlite3 ~/Library/Application\ Support/purchases/purchases.db \
  "SELECT order_id, name, price, quantity, price*quantity as total, purchase_date
   FROM items WHERE name LIKE '%search_term%' AND vendor='amazon';"
```

WHY: Faster than browser, works offline, identifies order_id for direct URL access.

### Step 1: Open order on Amazon

```bash
# Direct by order ID (preferred)
playwright-cli -s=amazon open --profile=~/.local/share/playwright-cli/profiles/amazon-privat \
  "https://www.amazon.de/gp/your-account/order-details?orderID=028-1234567-8901234"

# Or search via order history
playwright-cli -s=amazon open --profile=~/.local/share/playwright-cli/profiles/amazon-privat \
  "https://www.amazon.de/gp/css/order-history"
# Then: snapshot | grep searchbox, fill, press Enter
```

### Step 2: Download invoice

See [`scripts/download-invoice.sh`](scripts/download-invoice.sh) for the full download workflow (click Rechnung button, extract PDF URL via JS eval, download via curl + session cookies).

WHY: `playwright-cli pdf` renders Chromium's PDF viewer, not the original. curl + cookies gets the actual Amazon PDF.

See `references/invoice-download.md` for detailed steps and fallback options.

### File naming convention

```
YYYY-MM-DD - privat - amazon - <beschreibung> rechnung <bestellnummer>.pdf
```

## URL Patterns

| Works | Broken |
|-------|--------|
| `/gp/your-account/order-details?orderID=...` | `/your-orders/order-details?orderID=...` |
| `/gp/css/order-history` | Direct search URLs with `opt=ab` |

Always use `/gp/` prefixed URLs.

## Gotchas

- **Rate limits:** Add `sleep 2-3` between navigations to avoid "Tut uns Leid" errors.
- **Session switching:** Amazon may invalidate sessions when switching headed/headless. Stay in one mode when possible.
- **Search is broad:** Matches across full order, not just product names.

## Resources

- `references/purchases-db.md` — Schema, common queries, price limitations, DB import
- `references/invoice-download.md` — Detailed download steps, curl+cookies method, playwright-cli pdf fallback
