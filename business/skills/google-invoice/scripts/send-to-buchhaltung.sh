#!/bin/bash
# Create an Apple Mail draft for the Google invoice and send to Buchhaltung.
# Usage: MONTH=... YEAR=... TOTAL=... PDF_PATH=... XML_PATH=... bash send-to-buchhaltung.sh
set -euo pipefail

MONTH="${MONTH:?MONTH is required (e.g. März)}"
YEAR="${YEAR:?YEAR is required}"
TOTAL="${TOTAL:?TOTAL amount is required}"
PDF_PATH="${PDF_PATH:?PDF_PATH is required}"
XML_PATH="${XML_PATH:?XML_PATH is required}"

# NOTE: MONTH, YEAR, TOTAL, PDF_PATH, and XML_PATH are expanded in this heredoc.
# Values must not contain unescaped: $ ` "
osascript << APPLESCRIPT
tell application "Mail"
    activate
    set newMessage to make new outgoing message with properties {subject:"Google AI Pro Rechnung $MONTH $YEAR", content:"Rechnung Google AI Pro (Google One) $MONTH $YEAR - EUR $TOTAL brutto", visible:true, sender:"malte.sussdorff@cognovis.de"}
    tell newMessage
        make new to recipient at end of to recipients with properties {address:"buchhaltung@cognovis.de"}
        make new attachment with properties {file name:POSIX file "$PDF_PATH"}
        make new attachment with properties {file name:POSIX file "$XML_PATH"}
    end tell
end tell
APPLESCRIPT
