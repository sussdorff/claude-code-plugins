#!/bin/bash
# Template: Create a Database credential in 1Password.
# Replace placeholder values, then run: eval $(op signin) && bash op-create-database.sh
# set -euo pipefail  # Uncomment after filling in all placeholder values

op item create \
  --vault "API Keys" \
  --category "Database" \
  --title "<ServiceName>" \
  --tags "<tag1>,<tag2>" \
  "username=<user>" \
  "password=<password>" \
  "hostname=<host>" \
  "port=<port>" \
  "database=<dbname>" \
  "notesPlain=<description>"
