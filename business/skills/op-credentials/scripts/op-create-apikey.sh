#!/bin/bash
# Template: Create an API Key credential in 1Password.
# Replace placeholder values, then run: eval $(op signin) && bash op-create-apikey.sh

op item create \
  --vault "API Keys" \
  --category "API Credential" \
  --title "<ServiceName>" \
  --url "<service-url>" \
  "API Key[password]=<the-api-key>"
