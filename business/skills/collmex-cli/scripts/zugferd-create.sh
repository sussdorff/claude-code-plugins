#!/bin/bash
# Generate EN 16931 compliant ZUGFeRD XML for a vendor invoice.
# Adjust placeholder values before running.
# Optional flags: --qty <quantity>, --buyer-id <id>, --due 2024-02-15, --notes "..."

collmex zugferd-create \
  --vendor-id 123 \
  --invoice "INV-2024-001" \
  --date 2024-01-15 \
  --desc "Consulting services" \
  --net 500.00 \
  --tax-rate 19.0 \
  --output invoice.xml
