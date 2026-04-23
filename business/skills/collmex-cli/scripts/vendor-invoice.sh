#!/bin/bash
# Create a vendor invoice (books expense in accounting).
# Adjust placeholder values before running.
# Optional flags: --tax <amount>, --account <number>, --cost-center <name>, --json

collmex vendor-invoice \
  --vendor-id 123 \
  --invoice "INV-2024-001" \
  --date 2024-01-15 \
  --net 100.00 \
  --text "Office supplies"
