#!/usr/bin/env bash
# Commit staged changes with a conventional commit message.
# Usage: commit.sh "<type>(<scope>): <description>" "<body>" "<ticket-id>"
# Example: commit.sh "feat(auth): add token refresh" "Adds retry logic on expiry" "CCP-abc"
set -euo pipefail

SUBJECT="${1:-}"
BODY="${2:-}"
TICKET="${3:-}"

if [[ -z "$SUBJECT" ]]; then
    echo "Usage: commit.sh \"<type>(<scope>): <description>\" \"<body>\" \"<ticket-id>\"" >&2
    exit 1
fi

git add -A
git commit -m "$(cat <<EOF
${SUBJECT}

${BODY}

Refs: ${TICKET}
EOF
)"
