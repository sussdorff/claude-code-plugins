#!/bin/bash
# Create a new vendor in Collmex with all optional fields.
# Adjust placeholder values before running.

collmex vendor-create \
  --company "New Supplier GmbH" \
  --street "Musterstr. 1" \
  --zip "10115" \
  --city "Berlin" \
  --country DE \
  --email "info@supplier.de" \
  --iban "DE89370400440532013000" \
  --vat-id "DE123456789"
