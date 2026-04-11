# Invoice Download Reference

## Standard Download (via curl + session cookies)

Navigate to the invoice page, extract the PDF URL, then download via curl with session cookies.
WHY: `playwright-cli pdf` renders Chromium's PDF viewer into a new PDF (not the original). `eval` doesn't support async, so in-browser fetch+base64 also fails.

```bash
# Open order details
playwright-cli -s=amazon open --profile=~/.local/share/playwright-cli/profiles/amazon-privat \
  "https://www.amazon.de/gp/your-account/order-details?orderID=..."
sleep 3

# Click "Rechnung" button (opens dropdown)
playwright-cli -s=amazon snapshot | grep -i "rechnung"
# -> button "Rechnung" [ref=eXXX]
playwright-cli -s=amazon click eXXX
sleep 1

# Find the PDF download URL in the dropdown
playwright-cli -s=amazon snapshot | grep -i "rechnung"
# -> link "Rechnung" [ref=eYYY]  (URL contains /documents/download/.../invoice.pdf)

# Extract the direct PDF URL
playwright-cli -s=amazon eval "$(cat <<'JS'
(() => {
    const links = [...document.querySelectorAll('a')];
    return JSON.stringify(links
        .filter(a => a.href.includes('documents/download'))
        .map(a => ({text: a.textContent.trim(), href: a.href})));
})()
JS
)"
# -> [{"text":"Rechnung","href":"https://www.amazon.de/documents/download/<uuid>/invoice.pdf"}]
```

### Download with curl + cookies

```bash
# Extract session cookies from the browser
COOKIES=$(playwright-cli -s=amazon cookie-list | jq -r '.[] | "\(.name)=\(.value)"' | paste -sd '; ' -)

# Download the original PDF
curl -s -L \
  -H "Cookie: $COOKIES" \
  -o "/path/to/output.pdf" \
  "https://www.amazon.de/documents/download/<uuid>/invoice.pdf"

# Verify
file "/path/to/output.pdf"  # -> "PDF document, version 1.4, ..."
```

## Fallback: playwright-cli pdf (lower quality)

If curl fails (e.g. cookie extraction issues), `playwright-cli pdf` produces a usable but lower-quality PDF (Chromium re-render of the PDF viewer, ~85KB vs ~100KB original).

```bash
# Click the PDF link to navigate to it
playwright-cli -s=amazon click eYYY
sleep 2
# Capture Chromium's rendering of the PDF
playwright-cli -s=amazon pdf --filename="/path/to/output.pdf"
```

Note: This wraps the original PDF inside Chromium's print-to-PDF output. Usable but not the original document.

## Extracting order details via JS

For structured data from search results:

```bash
playwright-cli -s=amazon eval "$(cat <<'JS'
(() => {
    const lines = document.body.innerText.split('\n').filter(l => l.trim().length > 0);
    const results = [];
    let block = [];
    for (const line of lines) {
        const l = line.trim();
        if (l.match(/Bestellt am|Bestelldetails/i)) {
            if (block.length > 0) results.push(block.join(' | '));
            block = [l];
        } else if (block.length > 0 && block.length < 12) {
            block.push(l);
        }
    }
    if (block.length > 0) results.push(block.join(' | '));
    return JSON.stringify(results);
})()
JS
)"
```
