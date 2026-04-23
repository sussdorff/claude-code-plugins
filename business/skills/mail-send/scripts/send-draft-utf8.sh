#!/bin/bash
# Create an Apple Mail draft reading body from a UTF-8 file (required for umlauts/special chars).
# Step 1: Write email body to /tmp/mail-body.txt using the Write tool (UTF-8 encoded).
# Step 2: Run this script to create the AppleScript file and execute it.
# Usage: SUBJECT="..." TO="recipient@example.com" SENDER="malte.sussdorff@cognovis.de" bash send-draft-utf8.sh

SUBJECT="${SUBJECT:?SUBJECT is required}"
TO="${TO:?TO is required}"
SENDER="${SENDER:-malte.sussdorff@cognovis.de}"

cat << EOF > /tmp/create-draft.applescript
tell application "Mail"
    activate
    set mailContent to read POSIX file "/tmp/mail-body.txt" as «class utf8»
    set newMessage to make new outgoing message with properties {subject:"$SUBJECT", content:mailContent, visible:true, sender:"$SENDER"}
    tell newMessage
        make new to recipient at end of to recipients with properties {address:"$TO"}
    end tell
end tell
EOF
osascript /tmp/create-draft.applescript
