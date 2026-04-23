#!/bin/bash
# Generate ZUGFeRD XML for a Google One invoice via collmex-cli.
# Usage: INVOICE_NUMBER=... INVOICE_DATE=YYYY-MM-DD DESCRIPTION=... NET_AMOUNT=... OUTPUT_PATH=... bash zugferd-create.sh

INVOICE_NUMBER="${INVOICE_NUMBER:?INVOICE_NUMBER is required}"
INVOICE_DATE="${INVOICE_DATE:?INVOICE_DATE (YYYY-MM-DD) is required}"
DESCRIPTION="${DESCRIPTION:?DESCRIPTION is required}"
NET_AMOUNT="${NET_AMOUNT:?NET_AMOUNT is required}"
OUTPUT_PATH="${OUTPUT_PATH:?OUTPUT_PATH is required}"
YEAR="${INVOICE_DATE:0:4}"

cd ~/code/finance-projects/collmex-cli && uv run collmex zugferd-create \
  --vendor-id 72163 \
  --invoice "$INVOICE_NUMBER" \
  --date "$INVOICE_DATE" \
  --desc "$DESCRIPTION" \
  --net "$NET_AMOUNT" \
  --tax-rate 19.0 \
  --buyer-id "9045-3453-2608" \
  --output "$OUTPUT_PATH"
