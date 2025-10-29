# Playwright MCP Tools - Complete API Reference

## Overview

Playwright MCP uses **structured accessibility snapshots** instead of screenshots, making it LLM-friendly and deterministic. All tools operate on element references extracted from the accessibility tree.

**Key Principle:** The server provides browser automation through text-based accessibility trees, not visual/pixel-based input.

---

## Core Navigation & Inspection Tools

### `mcp__playwright__browser_navigate`

Navigate to a specified URL.

**Parameters:**
- `url` (string, required): The URL to navigate to

**Returns:** Navigation result with status

**Example:**
```
mcp__playwright__browser_navigate({ url: "https://example.com" })
```

**Best Practice:** Always call `browser_wait_for` immediately after navigation to ensure page is fully loaded before extracting content.

---

### `mcp__playwright__browser_snapshot`

Capture structured accessibility snapshot of the current page state.

**Parameters:** None (operates on current page)

**Returns:** Accessibility tree representation of the page

**Use Cases:**
- Inspect current page structure
- Identify element references for other actions
- Verify page state after actions

**Best Practice:** Use snapshots to understand page structure before performing actions. The accessibility tree shows element refs needed for clicks, types, etc.

---

### `mcp__playwright__browser_wait_for`

Wait for a specified time or condition.

**Parameters:**
- `time` (number, optional): Seconds to wait
- `selector` (string, optional): CSS selector to wait for
- `state` (string, optional): Element state to wait for ('visible', 'hidden', 'attached')

**Examples:**
```
mcp__playwright__browser_wait_for({ time: 3 })
mcp__playwright__browser_wait_for({ selector: '.content', state: 'visible' })
```

**Critical Usage:**
- **After navigation:** Wait 3-7 seconds for dynamic content to load
- **Before extraction:** Ensure elements are visible before reading
- **Lazy loading:** Wait for specific selectors to appear

**Common Patterns:**
```javascript
// After navigation (MANDATORY for dynamic pages)
mcp__playwright__browser_navigate({ url: "..." })
mcp__playwright__browser_wait_for({ time: 7 })  // Notion, Substack, etc.

// Wait for specific element
mcp__playwright__browser_wait_for({ selector: '.lazy-content', state: 'visible' })

// Wait for network idle (via evaluate)
mcp__playwright__browser_evaluate({
  function: "() => new Promise(resolve => setTimeout(resolve, 2000))"
})
```

---

## Content Extraction & JavaScript Execution

### `mcp__playwright__browser_evaluate`

Execute JavaScript code in the browser context.

**Parameters:**
- `function` (string, required): JavaScript code as arrow function
  - Format: `"() => { /* code */ }"` for page-level execution
  - Format: `"(element) => { /* code */ }"` for element-level execution
- `element` (string, optional): Human-readable element description
- `ref` (string, optional): Exact element reference from snapshot

**Returns:** Result of JavaScript execution

**Examples:**

**Extract page content:**
```javascript
mcp__playwright__browser_evaluate({
  function: "() => {
    const article = document.querySelector('article');
    return {
      title: document.title,
      content: article.innerText,
      wordCount: article.innerText.split(/\\s+/).length
    };
  }"
})
```

**Extract from specific element:**
```javascript
mcp__playwright__browser_evaluate({
  function: "(element) => element.innerText",
  element: "main article",
  ref: "ref-from-snapshot"
})
```

**Find all links in article:**
```javascript
mcp__playwright__browser_evaluate({
  function: "() => {
    const links = Array.from(document.querySelectorAll('article a[href]'));
    return links.map(link => ({
      url: link.href,
      text: link.textContent.trim()
    }));
  }"
})
```

**Best Practices:**
- ✅ Use arrow function format: `"() => { }"`
- ✅ Return JSON-serializable objects
- ✅ Use `try-catch` for error handling
- ✅ Validate elements exist before accessing
- ❌ Don't use `async` functions (use Promises instead)
- ❌ Don't return DOM elements (return data instead)

---

### `mcp__playwright__browser_console_messages`

Retrieve console output from the page.

**Parameters:**
- `onlyErrors` (boolean, optional): Filter to show only error messages

**Returns:** Array of console messages

**Use Cases:**
- Debugging page issues
- Checking for JavaScript errors
- Monitoring API calls logged to console

---

## Interaction Tools

### `mcp__playwright__browser_click`

Click on an element.

**Parameters:**
- `element` (string, required): Human-readable description for permission
- `ref` (string, required): Exact element reference from snapshot
- `doubleClick` (boolean, optional): Perform double-click
- `button` (string, optional): Mouse button ('left', 'right', 'middle')
- `modifiers` (array, optional): Modifier keys (['Control', 'Shift', 'Alt', 'Meta'])

**Example:**
```
mcp__playwright__browser_click({
  element: "Submit button",
  ref: "ref-123"
})
```

**Best Practice:** Always get the `ref` from a snapshot first to ensure you're clicking the correct element.

---

### `mcp__playwright__browser_type`

Type text into an input field.

**Parameters:**
- `element` (string, required): Human-readable description
- `ref` (string, required): Exact element reference
- `text` (string, required): Text to type

**Example:**
```
mcp__playwright__browser_type({
  element: "Search input",
  ref: "ref-456",
  text: "search query"
})
```

---

### `mcp__playwright__browser_select_option`

Select an option from a dropdown.

**Parameters:**
- `element` (string, required): Human-readable description
- `ref` (string, required): Exact element reference
- `value` (string, required): Option value to select

---

### `mcp__playwright__browser_press_key`

Press a keyboard key.

**Parameters:**
- `key` (string, required): Key name ('Enter', 'Escape', 'ArrowDown', etc.)

**Common Keys:** 'Enter', 'Tab', 'Escape', 'Backspace', 'ArrowDown', 'ArrowUp', 'PageDown', 'PageUp'

---

### `mcp__playwright__browser_drag`

Perform drag-and-drop operation.

**Parameters:**
- `startElement` (string, required): Source element description
- `startRef` (string, required): Source element reference
- `endElement` (string, required): Target element description
- `endRef` (string, required): Target element reference

---

### `mcp__playwright__browser_handle_dialog`

Respond to browser dialogs (alert, confirm, prompt).

**Parameters:**
- `action` (string, required): 'accept' or 'dismiss'
- `text` (string, optional): Text for prompt dialogs

---

## Session Management

### `mcp__playwright__browser_close`

Close the browser session.

**Parameters:** None

**Best Practice:** Always close the browser when done to free resources.

---

### `mcp__playwright__browser_tabs`

Manage browser tabs: list, create, close, or select tabs.

**Parameters:**
- `action` (string, required): Operation to perform - "list", "new", "close", or "select"
- `index` (number, optional): Tab index for close/select operations (0-based). If omitted for close, current tab is closed.
- `url` (string, optional): URL to navigate to when creating new tab (only for action="new")

**Returns:**
- For "list": Array of open tabs with indices and titles
- For "new": Success message with new tab index
- For "select": Success message
- For "close": Success message

**Examples:**

**List all tabs:**
```
mcp__playwright__browser_tabs({ action: "list" })
```

**Create new tab:**
```
mcp__playwright__browser_tabs({ action: "new" })
mcp__playwright__browser_tabs({ action: "new", url: "https://example.com" })
```

**Select specific tab:**
```
mcp__playwright__browser_tabs({ action: "select", index: 0 })
```

**Close tab:**
```
mcp__playwright__browser_tabs({ action: "close", index: 2 })
mcp__playwright__browser_tabs({ action: "close" })  // Closes current tab
```

**Important Notes:**
- All tabs share the same browser context (cookies, sessions, authentication)
- Tab indices are 0-based (first tab = 0, second tab = 1, etc.)
- Closing the last tab will close the browser
- Use tab management for parallel content extraction within same authenticated session

---

## Common Patterns & Best Practices

### Pattern 1: Navigate and Extract Content

```javascript
// 1. Navigate
mcp__playwright__browser_navigate({ url: "https://example.com" })

// 2. CRITICAL: Wait for content to load
mcp__playwright__browser_wait_for({ time: 3 })

// 3. Extract content
mcp__playwright__browser_evaluate({
  function: "() => {
    return {
      title: document.title,
      content: document.querySelector('main').innerText
    };
  }"
})

// 4. Close browser
mcp__playwright__browser_close()
```

### Pattern 2: Handle Lazy Loading

```javascript
// Navigate to page
mcp__playwright__browser_navigate({ url: "..." })

// Wait for initial load
mcp__playwright__browser_wait_for({ time: 2 })

// Scroll to trigger lazy loading
mcp__playwright__browser_evaluate({
  function: "() => window.scrollTo(0, document.body.scrollHeight)"
})

// Wait for lazy content to appear
mcp__playwright__browser_wait_for({ selector: '.lazy-loaded', state: 'visible' })

// Extract content
mcp__playwright__browser_evaluate({ function: "() => { /* extraction */ }" })
```

### Pattern 3: Fill and Submit Form

```javascript
// Get snapshot to find element refs
mcp__playwright__browser_snapshot()

// Fill form fields
mcp__playwright__browser_type({ element: "Email", ref: "ref-1", text: "user@example.com" })
mcp__playwright__browser_type({ element: "Password", ref: "ref-2", text: "password" })

// Submit
mcp__playwright__browser_click({ element: "Submit", ref: "ref-3" })

// Wait for navigation
mcp__playwright__browser_wait_for({ time: 2 })
```

### Pattern 4: Handle Dynamic Content (Notion, Substack)

```javascript
// Navigate
mcp__playwright__browser_navigate({ url: "https://notion.so/page" })

// MANDATORY: Wait longer for dynamic content
mcp__playwright__browser_wait_for({ time: 7 })

// Extract when ready
mcp__playwright__browser_evaluate({
  function: "() => {
    const content = document.querySelector('[data-content-editable-root=\"true\"]');
    return { text: content.innerText };
  }"
})
```

### Pattern 5: Multi-Tab Parallel Extraction

```javascript
// List existing tabs
const tabs = mcp__playwright__browser_tabs({ action: "list" })

// Create new tabs for parallel content extraction
mcp__playwright__browser_tabs({ action: "new", url: "https://example.com/article1" })
mcp__playwright__browser_tabs({ action: "new", url: "https://example.com/article2" })
mcp__playwright__browser_tabs({ action: "new", url: "https://example.com/article3" })

// Wait for all pages to load
mcp__playwright__browser_wait_for({ time: 3 })

// Process each tab
mcp__playwright__browser_tabs({ action: "select", index: 1 })
mcp__playwright__browser_wait_for({ time: 2 })
const content1 = mcp__playwright__browser_evaluate({
  function: "() => ({ title: document.title, content: document.body.innerText })"
})

mcp__playwright__browser_tabs({ action: "select", index: 2 })
mcp__playwright__browser_wait_for({ time: 2 })
const content2 = mcp__playwright__browser_evaluate({
  function: "() => ({ title: document.title, content: document.body.innerText })"
})

// Clean up tabs
mcp__playwright__browser_tabs({ action: "close", index: 2 })
mcp__playwright__browser_tabs({ action: "close", index: 1 })
```

**Important:** All tabs share the same authentication context. This pattern is useful for:
- Extracting multiple pages from the same authenticated site
- Comparing content across related pages
- Pre-loading pages while processing others
- NOT for true concurrent/parallel execution (tabs are processed sequentially)

---

## Token Management Best Practices

### ⚠️ Avoid Token Overflow

**Problem:** Initial navigation can return 40K+ tokens in snapshots.

**Solution:** Always call `browser_wait_for` after `browser_navigate` before using snapshots.

```javascript
// ❌ BAD: Immediate snapshot after navigation
mcp__playwright__browser_navigate({ url: "..." })
mcp__playwright__browser_snapshot()  // Returns 40K+ tokens!

// ✅ GOOD: Wait before snapshot
mcp__playwright__browser_navigate({ url: "..." })
mcp__playwright__browser_wait_for({ time: 3 })
mcp__playwright__browser_snapshot()  // Returns reasonable token count
```

### 📦 Use Subagents for Large Extractions

When extracting multiple pages (e.g., newsletter + linked resources), use subagents to isolate contexts:

**Main Agent:**
1. Navigate to main page
2. Extract metadata only
3. Write file immediately
4. Spawn subagents for each linked resource

**Subagent (per resource):**
1. Navigate to resource
2. Extract full content
3. Write files immediately
4. Return metadata only (~500 tokens)

**Result:** 77% token reduction (65K → 15K tokens)

---

## Error Handling

### Common Errors & Solutions

**Navigation Token Overflow**
- **Error:** `browser_navigate` returns 40K+ tokens
- **Fix:** Use `browser_wait_for` before snapshot

**Element Not Found**
- **Error:** Cannot find element reference
- **Fix:** Get fresh snapshot and verify element exists

**Private/403 Pages**
- **Error:** Cannot access Notion/authenticated page
- **Fix:** Log in manually in Edge first (MCP preserves sessions)

**Lazy Loading Timeout**
- **Error:** Content not appearing
- **Fix:** Increase wait time or scroll to trigger loading

**Empty Metadata**
- **Error:** Title/author extraction fails
- **Fix:** Use fallback strategies (meta tags, URL parsing)

---

## Wait Strategies Cheat Sheet

| Scenario | Wait Strategy |
|----------|--------------|
| After navigation | `browser_wait_for({ time: 3-7 })` |
| Lazy loaded images | `browser_wait_for({ selector: 'img.lazy', state: 'visible' })` |
| Dynamic content (Notion) | `browser_wait_for({ time: 7 })` |
| Form submission | `browser_wait_for({ time: 2 })` after click |
| Infinite scroll | Scroll + wait in loop until no new content |
| Network idle | Use evaluate with Promise.race and network monitoring |

---

## Selector Strategies

### Finding Elements

**Priority order:**
1. Use snapshot refs (most reliable)
2. Semantic selectors (`main`, `article`, `[role="main"]`)
3. Data attributes (`[data-testid="..."]`)
4. Class names (less reliable if dynamic)
5. Text content matching (last resort)

**Example for Notion pages:**
```javascript
const selectors = [
  '[data-content-editable-root="true"]',  // Primary
  'main',                                   // Fallback 1
  '[role="main"]',                          // Fallback 2
  '.notion-page-content'                    // Fallback 3
];
```

**Example for Substack:**
```javascript
const selectors = [
  'article .available-content',   // Primary
  'article .body',                // Fallback 1
  'main article',                 // Fallback 2
  '.post-content'                 // Fallback 3
];
```

---

## Advanced Techniques

### Deduplication

When extracting content, use Sets to avoid duplicates:

```javascript
const seenTexts = new Set();
elements.forEach(el => {
  const text = el.textContent.trim();
  if (!seenTexts.has(text)) {
    seenTexts.add(text);
    // Process element
  }
});
```

### Noise Filtering

Filter out UI elements that aren't content:

```javascript
const noisePatterns = [
  /^Subscribe$/i,
  /^Sign in$/i,
  /^Share$/i,
  /^Like \\(\\d+\\)$/,
  /^View comments/i
];

const isNoise = (text) => {
  return noisePatterns.some(pattern => pattern.test(text.trim()));
};
```

### Progressive Loading

For infinite scroll pages:

```javascript
let previousHeight = 0;
let currentHeight = document.body.scrollHeight;

while (currentHeight > previousHeight) {
  window.scrollTo(0, currentHeight);
  await new Promise(resolve => setTimeout(resolve, 1000));
  previousHeight = currentHeight;
  currentHeight = document.body.scrollHeight;
}
```

### Authentication Detection

Detect when a page requires authentication before attempting content extraction:

```javascript
// Pattern 1: Check for login page indicators
mcp__playwright__browser_evaluate({
  function: "() => {
    // Check for login forms and buttons
    const hasPasswordInput = !!document.querySelector('input[type=\"password\"]');
    const hasLoginForm = !!document.querySelector('form[action*=\"login\"], form[action*=\"signin\"], form[action*=\"auth\"]');
    const hasSignInButton = Array.from(document.querySelectorAll('button, a')).some(
      el => /sign in|log in|login/i.test(el.textContent)
    );

    // Check URL patterns
    const isAuthPage = /\\/login|\\/signin|\\/auth|authenticate/i.test(window.location.href);

    // Check for common auth-required messages
    const authMessages = Array.from(document.querySelectorAll('*')).some(
      el => /please (log in|sign in)|unauthorized|access denied/i.test(el.textContent)
    );

    return {
      requiresAuth: hasPasswordInput || hasLoginForm || hasSignInButton || isAuthPage || authMessages,
      indicators: {
        hasPasswordInput,
        hasLoginForm,
        hasSignInButton,
        isAuthPage,
        authMessages
      },
      currentUrl: window.location.href,
      pageTitle: document.title
    };
  }"
})
```

**Pattern 2: Check HTTP response codes**

Use `browser_console_messages` or network monitoring to detect:
- 401 Unauthorized responses
- 403 Forbidden responses
- Redirects to login pages

**Pattern 3: Inform user when authentication needed**

```javascript
// After detection
if (authCheck.requiresAuth) {
  // Inform user to log in manually
  console.log("Authentication required for this site.");
  console.log("Please:");
  console.log("1. Open Edge browser manually");
  console.log("2. Navigate to: " + authCheck.currentUrl);
  console.log("3. Log in to the site");
  console.log("4. Return to Claude Code and retry");
  console.log("");
  console.log("Your login will be preserved for future MCP operations.");
}
```

**Best Practice:** Always check for authentication requirements before attempting bulk content extraction. This saves time and provides clear guidance to users.
