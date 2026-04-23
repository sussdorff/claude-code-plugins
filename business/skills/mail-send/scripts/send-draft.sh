#!/bin/bash
# Create a visible Apple Mail draft with a single recipient and attachment.
# Usage: SUBJECT="..." BODY="..." TO="recipient@example.com" ATTACHMENT="/abs/path/file.pdf" SENDER="malte.sussdorff@cognovis.de" bash send-draft.sh

SUBJECT="${SUBJECT:?SUBJECT is required}"
BODY="${BODY:?BODY is required}"
TO="${TO:?TO is required}"
ATTACHMENT="${ATTACHMENT:?ATTACHMENT is required}"
SENDER="${SENDER:-malte.sussdorff@cognovis.de}"

osascript << APPLESCRIPT
tell application "Mail"
    activate
    set newMessage to make new outgoing message with properties {subject:"$SUBJECT", content:"$BODY", visible:true, sender:"$SENDER"}
    tell newMessage
        make new to recipient at end of to recipients with properties {address:"$TO"}
        make new attachment with properties {file name:POSIX file "$ATTACHMENT"}
    end tell
end tell
APPLESCRIPT
