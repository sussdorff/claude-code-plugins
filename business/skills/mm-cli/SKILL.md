---
name: mm-cli
model: haiku
description: CLI for MoneyMoney macOS finance app via AppleScript. Use when querying accounts, balances, transactions, cashflow, or spending. Triggers on MoneyMoney, bank accounts, transactions, cashflow, spending, balance, portfolio, financial analysis.
disableModelInvocation: true
---

# mm-cli - MoneyMoney CLI

Command-line interface for [MoneyMoney](https://moneymoney-app.com/) on macOS. Communicates via AppleScript -- requires macOS and MoneyMoney running and unlocked.

## When to Use

- You want to check account balances, list transactions, or analyze spending patterns
- You need a cashflow overview, recurring subscription summary, or top merchant breakdown
- You want to export transactions for tax filing or financial reporting
- You need to re-categorize transactions, find uncategorized ones, or review category usage
- You want to initiate a SEPA transfer or check your investment portfolio

## Prerequisites

- **macOS only** (AppleScript dependency)
- MoneyMoney installed, **running**, and **unlocked**
- Python 3.14+, uv
- Repo: `~/code/finance-projects/mm-cli/`

Run commands with:

```bash
cd ~/code/finance-projects/mm-cli && uv run mm <command>
```

## Configuration

Run `uv run mm init` once to configure:
- **Transfer category**: Top-level category group for internal transfers (excluded from analysis by default)
- **Excluded account groups**: Groups hidden when using `--active` (e.g., closed accounts)

Config stored in `~/.config/mm-cli/config.toml`. Tool works without config, but analysis commands filter better with it.

## Output Formats

All commands support `--format table` (default), `--format json`, `--format csv`.

```bash
uv run mm accounts --format json | jq '.[].balance'
uv run mm transactions --from 2026-01-01 --format csv > export.csv
```

## Commands

### Accounts & Balances

```bash
uv run mm accounts                          # All accounts with balances
uv run mm accounts --hierarchy              # Grouped with subtotals
uv run mm accounts --active                 # Exclude closed/dissolved groups
uv run mm accounts --group Privat           # Filter by account group
uv run mm accounts -g Privat -g Business    # Multiple groups
```

### Transactions

Defaults to last 14 days if no date range given.

```bash
uv run mm transactions                                    # Last 14 days
uv run mm transactions --days 30                           # Last 30 days
uv run mm transactions --from 2026-01-01 --to 2026-01-31  # Date range
uv run mm transactions --category Lebensmittel             # By category
uv run mm transactions --uncategorized                     # Missing category
uv run mm transactions --account DE89...                   # By IBAN
uv run mm transactions --group Privat                      # By account group
uv run mm transactions --min-amount 50 --max-amount 500    # Amount range
uv run mm transactions --sort amount                       # Sort: date, amount, name
uv run mm transactions --sort date --reverse               # Newest first
uv run mm transactions --checkmark off                     # Unchecked only
```

### Categories

```bash
uv run mm categories                        # All categories with hierarchy
uv run mm category-usage                    # Categories by transaction count
uv run mm category-usage --limit 10         # Top 10 most used
```

### Analysis Commands

All analysis commands exclude internal transfers by default (both IBAN-matching and configured transfer category). Use `--include-transfers` to show everything, or `--transfers-only` to see only internal movements.

When using `--group`, cross-group transfers (e.g. salary from company to personal) are kept as real cashflow.

#### Spending by Category

```bash
uv run mm analyze spending                              # This month
uv run mm analyze spending --period last-month          # Last month
uv run mm analyze spending --period last-month --compare # vs. previous
uv run mm analyze spending --type expense --group Privat # Expenses only
uv run mm analyze spending --from 2026-01-01 --to 2026-01-31
```

Periods: `this-month`, `last-month`, `this-quarter`, `last-quarter`, `this-year`

#### Cashflow (Income vs Expenses)

```bash
uv run mm analyze cashflow --months 6                   # 6 months monthly
uv run mm analyze cashflow --months 12 --period quarterly
uv run mm analyze cashflow --group Privat
```

#### Recurring Transactions (Subscriptions)

```bash
uv run mm analyze recurring --months 12                 # Last 12 months
uv run mm analyze recurring --min-occurrences 4         # At least 4x
uv run mm analyze recurring --group Privat
```

#### Top Merchants (by Spend)

```bash
uv run mm analyze merchants                             # This month, expenses
uv run mm analyze merchants --period this-year --limit 30
uv run mm analyze merchants --type all                  # Income + expenses
```

#### Top Customers (Income by Counterparty)

```bash
uv run mm analyze top-customers                         # This month
uv run mm analyze top-customers --period this-year
uv run mm analyze top-customers --group Business
```

#### Balance History

```bash
uv run mm analyze balance-history --months 6
uv run mm analyze balance-history --account Girokonto
uv run mm analyze balance-history --group Hauptkonten
```

### Transaction Management

```bash
# Re-categorize a transaction
uv run mm set-category <transaction-id> Lebensmittel
uv run mm set-category <transaction-id> Lebensmittel --dry-run

# Checkmark (reconciliation)
uv run mm set-checkmark <transaction-id> on
uv run mm set-checkmark <transaction-id> off

# Comments
uv run mm set-comment <transaction-id> "Reviewed 2026-01"
uv run mm set-comment <transaction-id> ""                    # Clear
```

### Rule Suggestions

Analyzes uncategorized transactions against historical patterns:

```bash
uv run mm suggest-rules                      # Last 30 days
uv run mm suggest-rules --from 2026-01-01    # From specific date
uv run mm suggest-rules --history 12         # 12 months of history
```

### Export

Export to MT940/STA, CSV, OFX, CAMT.053, XLS, or Numbers:

```bash
uv run mm export --from 2025-01-01 --to 2025-12-31 --format csv -o ~/export.csv
uv run mm export --account "DE89..." --format sta
```

### Portfolio (Investments)

```bash
uv run mm portfolio                          # All depot accounts
uv run mm portfolio --account Depot          # Specific account
uv run mm portfolio --format json
```

### SEPA Transfers

```bash
uv run mm transfer -f Girokonto -t "Max Mustermann" -i DE89... -a 100.00 -p "Invoice 2026-001"
uv run mm transfer -f Girokonto -t "Max" -i DE89... -a 100 -p "Ref" --dry-run       # Preview only
uv run mm transfer -f Girokonto -t "Max" -i DE89... -a 100 -p "Ref" --outbox --confirm  # Queue without UI
```

## Error Handling

### MoneyMoney Not Running

```
MoneyMoney is not running. Please start the application first.
```

Fix: Open MoneyMoney.app. The CLI communicates via AppleScript and needs the app running.

### Database Locked

```
MoneyMoney is locked. Please unlock it first.
```

Fix: MoneyMoney requires a master password. Unlock it in the app before using CLI commands.

### AppleScript Timeout

Long operations (large exports, many transactions) can cause AppleScript timeouts. Break queries into smaller date ranges if needed.

### Permission Denied

On first use, macOS may prompt for Automation permissions. Grant Terminal (or iTerm/Warp) permission to control MoneyMoney in System Settings > Privacy & Security > Automation.

## Limitations

- **macOS only** -- AppleScript is the sole communication channel
- **MoneyMoney must be running and unlocked** -- no headless/background mode
- **No real-time sync** -- data is fetched on-demand from MoneyMoney's database
- **Transfer execution** requires MoneyMoney's banking connection (TAN may be needed). WHY: the CLI queues the transfer but the bank's TAN challenge must be completed in the MoneyMoney UI.
- **Large date ranges** can be slow due to AppleScript serialization overhead
- **Category rules** are managed in MoneyMoney's UI; `suggest-rules` only provides suggestions

## Do NOT

- Do NOT execute `uv run mm transfer` without `--dry-run` first AND explicit user confirmation. WHY: SEPA transfers are irreversible financial transactions -- a wrong IBAN or amount cannot be undone.
- Do NOT run analysis commands without `--group` when the user asks about a specific account group. WHY: mixing personal and business transactions produces misleading financial summaries.
- Do NOT use `set-category` without `--dry-run` first. WHY: re-categorization changes MoneyMoney's internal state and affects all future analysis reports.
- Do NOT assume MoneyMoney is running -- check for the "not running" or "locked" error before retrying commands. WHY: AppleScript calls to a locked/closed app hang silently or return cryptic errors.
- Do NOT query large date ranges (>1 year) in a single command. WHY: AppleScript serialization causes timeouts; break into smaller ranges and combine results.

## Output Format

Default output is formatted tables. Use `--format json` or `--format csv` for machine-readable export:
```
uv run mm accounts          # Table: Name, Balance, Currency
uv run mm transactions      # Table: Date, Payee, Amount, Category
uv run mm analyze cashflow --format csv    # CSV for spreadsheet import
```

## Useful Patterns

```bash
# Monthly spending summary as JSON
uv run mm analyze spending --format json | jq '.[] | select(.budget != null)'

# Find all uncategorized transactions this month
uv run mm transactions --uncategorized --format json | jq '.[].name'

# Export last year for tax filing
uv run mm export --from 2025-01-01 --to 2025-12-31 --format csv -o ~/taxes-2025.csv

# Check subscription costs
uv run mm analyze recurring --months 12 --format json | jq '[.[].amount] | add'
```
