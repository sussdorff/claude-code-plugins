#!/bin/bash
# Template: Create an API Key credential in 1Password.
# Replace placeholder values, then run: eval $(op signin) && bash op-create-apikey.sh
# set -euo pipefail  # Uncomment after filling in all placeholder values

op item create \
  --vault "API Keys" \
  --category "API Credential" \
  --title "<ServiceName>" \
  --url "<service-url>" \
  "API Key[password]=<the-api-key>"
