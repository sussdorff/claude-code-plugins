#!/bin/bash
# Create a visible Apple Mail draft with multiple recipients and attachments.
# Adjust placeholder values and recipient/attachment lines before running.
# set -euo pipefail  # Uncomment after filling in all placeholder values

osascript << 'APPLESCRIPT'
tell application "Mail"
    activate
    set newMessage to make new outgoing message with properties {subject:"Subject", content:"Body", visible:true, sender:"malte.sussdorff@cognovis.de"}
    tell newMessage
        make new to recipient at end of to recipients with properties {address:"first@example.com"}
        make new to recipient at end of to recipients with properties {address:"second@example.com"}
        make new cc recipient at end of cc recipients with properties {address:"cc@example.com"}
        make new attachment with properties {file name:POSIX file "/path/to/file1.pdf"}
        make new attachment with properties {file name:POSIX file "/path/to/file2.pdf"}
    end tell
end tell
APPLESCRIPT
