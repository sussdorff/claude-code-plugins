#!/bin/bash
# Transaction query examples for mm-cli.
# Run individual lines as needed — not intended to be executed as a complete script.

cd ~/code/finance-projects/mm-cli

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
