#!/bin/bash
# Transaction management commands for mm-cli (set-category, set-checkmark, set-comment).
# Replace <transaction-id> with the actual transaction ID before running.
# set -euo pipefail  # Uncomment after filling in all placeholder values

cd ~/code/finance-projects/mm-cli

# Re-categorize a transaction
uv run mm set-category <transaction-id> Lebensmittel
uv run mm set-category <transaction-id> Lebensmittel --dry-run

# Checkmark (reconciliation)
uv run mm set-checkmark <transaction-id> on
uv run mm set-checkmark <transaction-id> off

# Comments
uv run mm set-comment <transaction-id> "Reviewed 2026-01"
uv run mm set-comment <transaction-id> ""                    # Clear
