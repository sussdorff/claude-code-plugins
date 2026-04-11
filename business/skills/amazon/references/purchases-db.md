# Purchases Database Reference

Local SQLite database for offline order lookups.

**Path:** `~/Library/Application Support/purchases/purchases.db`

## Schema

```sql
-- One row per item (not per order). An order with 3 items = 3 rows.
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,          -- e.g. "028-1302454-8881142"
    vendor TEXT NOT NULL,            -- "amazon"
    name TEXT NOT NULL,              -- product description
    price REAL NOT NULL,             -- per-item price (EUR)
    currency TEXT DEFAULT 'EUR',
    quantity INTEGER DEFAULT 1,
    purchase_date TEXT NOT NULL,     -- "YYYY-MM-DD"
    category TEXT,                   -- our category (smart-home, electronics, etc.)
    vendor_category TEXT,            -- Amazon's category hierarchy
    vendor_sku TEXT,                 -- ASIN
    order_url TEXT,
    item_url TEXT,
    is_digital INTEGER DEFAULT 0,
    is_consumable INTEGER DEFAULT 0,
    exported_to_vault INTEGER DEFAULT 0,
    UNIQUE(order_id, vendor_sku, vendor)
);
```

## Common Queries

```bash
# Find items by name
sqlite3 ~/Library/Application\ Support/purchases/purchases.db \
  "SELECT order_id, name, price, quantity, purchase_date FROM items WHERE name LIKE '%search%';"

# Order total (approximation — excludes shipping/discounts/tax)
sqlite3 ~/Library/Application\ Support/purchases/purchases.db \
  "SELECT order_id, SUM(price * quantity) as total, purchase_date, GROUP_CONCAT(name, ' + ')
   FROM items WHERE order_id = '028-1302454-8881142' GROUP BY order_id;"

# All orders in a date range
sqlite3 ~/Library/Application\ Support/purchases/purchases.db \
  "SELECT DISTINCT order_id, purchase_date, SUM(price * quantity) as total
   FROM items WHERE vendor='amazon' AND purchase_date BETWEEN '2024-01-01' AND '2024-12-31'
   GROUP BY order_id ORDER BY purchase_date;"

# Spending by category
sqlite3 ~/Library/Application\ Support/purchases/purchases.db \
  "SELECT category, COUNT(*), printf('%.2f', SUM(price * quantity)) as total
   FROM items WHERE vendor='amazon' GROUP BY category ORDER BY total DESC;"
```

## Price Limitations

- `price` is the **per-item price**, not the order total
- Order total = `SUM(price * quantity) GROUP BY order_id` — **approximation only**
- **Missing from DB:** shipping costs, discounts, coupons, tax breakdown
- **Actual total** only available on the invoice PDF or Amazon order details page

## Updating the Database

The purchases tool lives at `~/gastown/purchases/` with source at `~/gastown/purchases/crew/`.
Imports from Amazon's **Items CSV export**.

**How to get the CSV:**
1. Go to https://www.amazon.de/gp/b2b/reports (Amazon > Account > Bestellberichte)
2. Select date range and "Items" report type
3. Download the CSV

**How to import:**
```bash
purchases import amazon /path/to/amazon-items-YYYY.csv
```

**CSV columns:** `order id, order url, order date, quantity, description, item url, price, subscribe & save, ASIN, category`

**Note:** CSV does NOT contain invoice URLs. Invoices require browser automation.
