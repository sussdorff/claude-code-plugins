# Site-Specific Extraction Presets

This reference provides recommended extraction parameters for common sites when using the `extract_web_content.py` script.

## Usage Pattern

```bash
python scripts/extract_web_content.py <url> <output_file> \
    --selectors <selector1> <selector2> ... \
    --wait-time <milliseconds> \
    --cookie-button "<button_text>"
```

## Common Site Presets

### Notion (notion.so, notion.site)

**Selectors**: `"main"` `"[role=main]"`
**Wait Time**: `7000` ms (Notion is slow to load)
**Cookie Button**: None

**Example**:
```bash
python scripts/extract_web_content.py \
    "https://notion.so/page-id" \
    "output.md" \
    --selectors "main" "[role=main]" \
    --wait-time 7000
```

**Notes**:
- Notion pages use React/dynamic loading and need longer wait times
- Main content is always in `<main>` or `[role=main]` element
- No cookie popup in most cases
- Works for both public pages and pages requiring login (if browser is logged in)

---

### Substack (*.substack.com)

**Selectors**: `".available-content"` `".post-content"` `"article"`
**Wait Time**: `3000` ms
**Cookie Button**: `"Accept"` or `"Accept cookies"`

**Example**:
```bash
python scripts/extract_web_content.py \
    "https://example.substack.com/p/post-title" \
    "output.md" \
    --selectors ".available-content" ".post-content" "article" \
    --wait-time 3000 \
    --cookie-button "Accept"
```

**Notes**:
- Substack uses `.available-content` for the main article body
- Often has GDPR cookie popup that needs to be accepted
- Archive pages use different structure - use `"article"` as fallback
- Free vs paid content may use different selectors

---

### Medium (medium.com, *.medium.com)

**Selectors**: `"article"` `".postArticle-content"` `"main"`
**Wait Time**: `3000` ms
**Cookie Button**: None (usually handled automatically)

**Example**:
```bash
python scripts/extract_web_content.py \
    "https://medium.com/@author/article-title" \
    "output.md" \
    --selectors "article" ".postArticle-content" "main" \
    --wait-time 3000
```

**Notes**:
- Medium uses semantic `<article>` tag
- Older posts may use `.postArticle-content` class
- Cookie handling is usually transparent
- Member-only content requires logged-in browser

---

### Generic Blog/Article Sites

**Selectors**: `"article"` `"main"` `"[role=main]"` `".content"` `"#content"`
**Wait Time**: `3000` ms
**Cookie Button**: Varies (try `"Accept"`, `"Accept all"`, `"I agree"`)

**Example**:
```bash
python scripts/extract_web_content.py \
    "https://example.com/blog/post" \
    "output.md" \
    --selectors "article" "main" "[role=main]" ".content" "#content" \
    --wait-time 3000 \
    --cookie-button "Accept"
```

**Notes**:
- Try multiple selectors in order of likelihood
- `<article>` is the HTML5 semantic standard
- `.content` and `#content` are common class/id names
- Cookie button text varies widely by region and site

---

## Debugging Failed Extractions

If extraction fails with "No selector returned content > 100 chars":

1. **Increase wait time**: Site may need more time to load
   ```bash
   --wait-time 10000  # Try 10 seconds
   ```

2. **Try different selectors**: Use browser DevTools to inspect the page
   - Right-click on the main content → Inspect
   - Look for the parent element containing the text
   - Note the tag name, class, or id

3. **Check for authentication**: Some content requires login
   - Run the script visibly (default) to see the page
   - Check if there's a login prompt or paywall

4. **Check for JavaScript requirements**: Some sites need JS to render
   - The script waits for `domcontentloaded` which should handle most cases
   - If content still doesn't appear, the site may use heavy client-side rendering

5. **Handle cookie popup differently**: Try different button text
   ```bash
   --cookie-button "Accept all cookies"
   --cookie-button "I agree"
   --cookie-button "OK"
   ```

---

## Custom Site Examples

### Hacker News

**Selectors**: `".fatitem"` `".comment"`
**Wait Time**: `2000` ms

```bash
python scripts/extract_web_content.py \
    "https://news.ycombinator.com/item?id=12345" \
    "hn-thread.md" \
    --selectors ".fatitem" ".comment" \
    --wait-time 2000
```

### Reddit

**Selectors**: `"[data-test-id=post-content]"` `".Post"` `"article"`
**Wait Time**: `5000` ms
**Cookie Button**: `"Accept all"`

```bash
python scripts/extract_web_content.py \
    "https://reddit.com/r/programming/comments/xyz" \
    "reddit-post.md" \
    --selectors "[data-test-id=post-content]" ".Post" "article" \
    --wait-time 5000 \
    --cookie-button "Accept all"
```

### Wikipedia

**Selectors**: `"#mw-content-text"` `".mw-parser-output"` `"article"`
**Wait Time**: `2000` ms

```bash
python scripts/extract_web_content.py \
    "https://en.wikipedia.org/wiki/Article_Name" \
    "wikipedia-article.md" \
    --selectors "#mw-content-text" ".mw-parser-output" "article" \
    --wait-time 2000
```

---

## Agent Workflow

When using this script in an agent (e.g., `notion-extractor`, `substack-extractor`):

1. **Identify the site type** from the URL
2. **Look up the preset** in this reference file
3. **Call the script** with the appropriate parameters
4. **Handle the result**:
   - On success: The script outputs JSON with metadata and writes content to file
   - On failure: The script reports which selectors were attempted
5. **Read the extracted file** using the Read tool if further processing is needed

**Example agent usage**:
```bash
# Extract Notion page
python scripts/extract_web_content.py "$NOTION_URL" "$OUTPUT_FILE" \
    --selectors "main" "[role=main]" \
    --wait-time 7000

# Parse the JSON output for metadata
RESULT=$(... | tail -1)  # Last line is JSON

# Read the file for processing
Read "$OUTPUT_FILE"
```

---

## Benefits Over MCP browser_evaluate

This script bypasses MCP context limits by:

1. **No 25K token limit**: Can extract unlimited content size
2. **No Write tool limits**: Writes directly to filesystem
3. **Zero token usage**: Content never passes through LLM context
4. **Deterministic**: Same extraction every time
5. **Reusable**: Can be called multiple times without context buildup

When to use this script vs MCP browser tools:
- **Use this script**: For extracting large content (>10KB) to files
- **Use MCP tools**: For interactive browsing, clicking, form filling, screenshots
