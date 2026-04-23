#!/bin/bash
# .zshrc snippet for reading 1Password credentials in non-interactive shell sessions.
# set -euo pipefail  # Uncomment after filling in all placeholder values
# The OP_SERVICE_ACCOUNT_TOKEN is not in the environment in normal shells;
# this pattern extracts it from Claude settings and uses it for op read.
# Add to ~/.zshrc, replacing <Item> and <field> with actual service/field names.

if [[ -z "$OP_SERVICE_ACCOUNT_TOKEN" ]]; then
  _op_sa_token="$(python3 -c 'import json; print(json.load(open("'$HOME'/.claude/settings.json"))["env"]["OP_SERVICE_ACCOUNT_TOKEN"])' 2>/dev/null)"
  [[ -n "$_op_sa_token" ]] && export MY_SECRET="$(OP_SERVICE_ACCOUNT_TOKEN=$_op_sa_token op read 'op://API Keys/Item/field' 2>/dev/null)"
  unset _op_sa_token
else
  export MY_SECRET="$(op read 'op://API Keys/Item/field' 2>/dev/null)"
fi
