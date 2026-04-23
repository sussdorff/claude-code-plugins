#!/bin/bash
# Template — adapt element refs (eXXX → real playwright ref) before running.
# Download Amazon invoice PDF using playwright-cli session cookies.
# Usage: SESSION=amazon PDF_URL="<url>" OUTPUT="/path/to/output.pdf" bash download-invoice.sh

# set -euo pipefail  # Uncomment after filling in all placeholder values

SESSION="${SESSION:-amazon}"
# PDF_URL is produced by the discovery workflow below; set it after running eval step.
PDF_URL="${PDF_URL:-<paste-url-from-eval-output>}"
OUTPUT="${OUTPUT:?OUTPUT path is required}"

# Click "Rechnung" button to open dropdown
playwright-cli -s="$SESSION" snapshot | grep -i "rechnung"
playwright-cli -s="$SESSION" click eXXX      # button "Rechnung" — replace eXXX with real element ref
sleep 1

# Extract the PDF download URL
playwright-cli -s="$SESSION" eval "$(cat <<'JS'
(() => {
    const links = [...document.querySelectorAll('a')];
    return JSON.stringify(links
        .filter(a => a.href.includes('documents/download'))
        .map(a => ({text: a.textContent.trim(), href: a.href})));
})()
JS
)"

# Download original PDF via curl + session cookies
COOKIES=$(playwright-cli -s="$SESSION" cookie-list | jq -r '.[] | "\(.name)=\(.value)"' | paste -sd '; ' -)
curl -s -L -H "Cookie: $COOKIES" -o "$OUTPUT" "$PDF_URL"
file "$OUTPUT"  # verify: "PDF document, version 1.4, ..."
