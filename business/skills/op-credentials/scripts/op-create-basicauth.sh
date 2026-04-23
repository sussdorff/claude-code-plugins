#!/bin/bash
# Template: Create a Basic Auth credential in 1Password.
# Replace placeholder values, then run: eval $(op signin) && bash op-create-basicauth.sh
# set -euo pipefail  # Uncomment after filling in all placeholder values

op item create \
  --vault "API Keys" \
  --category "Login" \
  --title "<ServiceName>" \
  --url "<service-url>" \
  --generate-password='20,letters,digits' \
  "username=<username>"
