---
name: playwright-mcp-usage
description: This skill should be used when using the Playwright MCP server with Microsoft Edge for browser automation. Use when the user wants to extract content from websites, handle lazy loading, fill forms, manage browser sessions, or needs guidance on browser interaction patterns. This skill is NOT for writing Playwright scripts to run locally - it's specifically for using the Playwright MCP server through Claude Code. For installation and setup, use the /install-playwright command instead.
---

# Playwright MCP Usage

## Overview

Use Playwright MCP server to enable Claude Code to control Microsoft Edge for browser automation tasks. This skill provides installation guidance, configuration management, and best practices for browser interactions including content extraction, form filling, and handling dynamic pages.

**Key Capabilities:**
- Install and configure Playwright MCP with Edge
- Check which directories have Playwright+Edge configured
- Navigate pages and extract content (including large content without context limits)
- Handle lazy loading and dynamic content
- Fill forms and interact with elements
- Manage browser sessions with preserved logins
- Extract large web content directly to files (bypasses all MCP/context limits)

---

## When to Use This Skill

Use this skill when:
- User asks to enable/install/setup/configure Playwright MCP with Edge
- User wants to see which directories have Playwright configured
- User needs to extract content from websites (especially authenticated sites)
- User needs to extract LARGE content (>10KB) without hitting context limits
- User wants to automate browser tasks (filling forms, clicking buttons)
- User asks about handling lazy loading or dynamic content
- User needs guidance on Playwright MCP tools and patterns
- Building agents that need to extract web content (Notion, Substack, Medium, etc.)

**Do NOT use for:**
- Writing Playwright scripts for local execution (this is about MCP server usage)
- Screenshot-based automation (Playwright MCP uses accessibility trees)
- General web scraping without browser automation needs

---

## Quick Start

### Install Playwright MCP with Edge

Use the automated installation script:

```bash
scripts/install-playwright-edge.sh
```

**Smart Installation Features:**
- Detects if already configured for current project
- Automatically reuses tokens from other projects (selects most recently active)
- Uses git commit dates for git repos, file modification dates for non-git folders
- Skips extension download if token already exists
- Only prompts for manual steps when truly necessary

Or follow the manual installation steps in `references/edge-installation-guide.md`.

**Critical:** After installation, restart Claude Code for changes to take effect.

### Check Configured Directories

List all directories with Playwright MCP configured for Edge:

```bash
scripts/check-edge-configs.sh
```

View configuration for current directory:

```bash
jq ".projects.\"/$(pwd)\".mcpServers.playwright" ~/.claude.json
```

---

## Core Workflows

### Workflow 1: Navigate and Extract Content

**Use when:** Extracting articles, documentation, or any web content.

**Steps:**

1. **Navigate to URL:**
   ```
   mcp__playwright__browser_navigate({ url: "https://example.com" })
   ```

2. **CRITICAL: Wait for content to load:**
   ```
   mcp__playwright__browser_wait_for({ time: 3 })
   ```

   **Why:** Prevents 40K+ token overflow from incomplete snapshots. Dynamic pages (Notion, Substack) require longer waits (5-7 seconds).

3. **Extract content using JavaScript:**
   ```javascript
   mcp__playwright__browser_evaluate({
     function: "() => {
       const article = document.querySelector('article, main, [role=\"main\"]');
       return {
         title: document.title,
         content: article.innerText,
         wordCount: article.innerText.split(/\\s+/).length
       };
     }"
   })
   ```

4. **Write content immediately** to avoid token accumulation

5. **Close browser when done:**
   ```
   mcp__playwright__browser_close()
   ```

**Best Practice:** For large extractions (multiple pages), use subagents to isolate contexts. Main agent spawns subagent for each page, subagent extracts and writes files, returns only metadata (~500 tokens).

---

### Workflow 1B: Extract Large PUBLIC Content Without Context Limits

**Use when:** Extracting large articles, documentation, or any **PUBLIC** (non-authenticated) content >10KB that would overflow context.

**⚠️ IMPORTANT LIMITATION:** This script works ONLY for **public websites that don't require authentication**. For paywalled or authenticated content (Substack paid articles, private Notion pages, etc.), you MUST use MCP tools with your logged-in browser session.

**Key Difference:** This uses a **standalone Python script** that launches its own Playwright instance. It does NOT use the MCP server, so it bypasses all context and token limits.

**Requirements:**
- This skill must be installed (provides the script)
- Python 3 with playwright library installed
- Edge browser

**Steps:**

1. **Determine site-specific selectors:**
   - For known sites (Notion, Substack, Medium), consult `references/site-presets.md`
   - For unknown sites, use MCP browser tools to inspect and find selectors first

2. **Call the extraction script:**
   ```bash
   python scripts/extract_web_content.py "$URL" "$OUTPUT_FILE" \
       --selectors "main" "article" "[role=main]" \
       --wait-time 5000 \
       --cookie-button "Accept"
   ```

3. **Parse the JSON result:**
   ```bash
   # Script outputs JSON on last line
   RESULT=$(... | tail -1)
   # Contains: success, output_file, char_count, line_count, title, selector_used
   ```

4. **Read the extracted file if needed for processing:**
   ```bash
   Read "$OUTPUT_FILE"
   ```

**Advantages over MCP browser_evaluate:**
- ✅ No 25K token response limit from `browser_evaluate`
- ✅ No Write tool size limits (writes directly to filesystem)
- ✅ Zero tokens in LLM context (content never passes through)
- ✅ Can extract unlimited content size (tested with 110KB+ files)
- ✅ Completely independent of MCP server
- ✅ Faster than MCP for public content (no extension overhead)

**Limitations:**
- ❌ Cannot access paywalled/authenticated content
- ❌ No access to logged-in browser sessions
- ❌ Cannot interact with pages (clicking, forms, etc.)

**Example - Extract PUBLIC Notion page:**
```bash
python scripts/extract_web_content.py \
    "https://notion.so/public-page-id" \
    "notion-content.txt" \
    --selectors "main" "[role=main]" \
    --wait-time 7000
```

**Example - Extract FREE Substack article:**
```bash
python scripts/extract_web_content.py \
    "https://example.substack.com/p/free-post" \
    "article.txt" \
    --selectors ".available-content" ".post-content" "article" \
    --wait-time 3000 \
    --cookie-button "Accept"
```

**When to use script vs MCP tools:**
- **Use standalone script**: Large PUBLIC content extraction (>10KB), no auth required, want to bypass context limits
- **Use MCP tools**: Authenticated content, paywalled sites, interactive browsing, clicking, form filling, or when logged-in session is needed

**Site Presets Available:**
See `references/site-presets.md` for recommended selectors, wait times, and cookie handling for:
- Notion (notion.so)
- Substack (*.substack.com)
- Medium (medium.com)
- Generic sites

---

### Workflow 2: Handle Lazy Loading Content

**Use when:** Pages load content dynamically on scroll or after delay.

**Steps:**

1. Navigate and wait for initial load
2. **Scroll to trigger lazy loading:**
   ```javascript
   mcp__playwright__browser_evaluate({
     function: "() => window.scrollTo(0, document.body.scrollHeight)"
   })
   ```

3. **Wait for specific elements to appear:**
   ```
   mcp__playwright__browser_wait_for({
     selector: '.lazy-content',
     state: 'visible'
   })
   ```

4. **For infinite scroll, loop until no new content:**
   ```javascript
   mcp__playwright__browser_evaluate({
     function: "() => {
       let previousHeight = 0;
       let currentHeight = document.body.scrollHeight;
       const results = [];

       while (currentHeight > previousHeight) {
         window.scrollTo(0, currentHeight);
         // Collect visible items
         results.push(...document.querySelectorAll('.item'));
         previousHeight = currentHeight;
         currentHeight = document.body.scrollHeight;
       }

       return { count: results.length };
     }"
   })
   ```

**Wait Time Guide:**
- Standard pages: 2-3 seconds
- Dynamic content (Substack): 3-5 seconds
- Heavy JS apps (Notion): 7+ seconds
- After interactions (clicks): 1-2 seconds

---

### Workflow 3: Fill and Submit Forms

**Use when:** Automating form submissions, testing login flows.

**Steps:**

1. **Get snapshot to find element references:**
   ```
   mcp__playwright__browser_snapshot()
   ```

2. **Type into form fields:**
   ```
   mcp__playwright__browser_type({
     element: "Email input",
     ref: "ref-from-snapshot",
     text: "user@example.com"
   })
   ```

3. **Select dropdown options:**
   ```
   mcp__playwright__browser_select_option({
     element: "Country dropdown",
     ref: "ref-from-snapshot",
     value: "US"
   })
   ```

4. **Click submit button:**
   ```
   mcp__playwright__browser_click({
     element: "Submit button",
     ref: "ref-from-snapshot"
   })
   ```

5. **Wait for navigation/response:**
   ```
   mcp__playwright__browser_wait_for({ time: 2 })
   ```

**Best Practice:** Always get fresh snapshots before interactions to ensure element refs are current.

---

### Workflow 4: Extract from Authenticated Sites

**Use when:** Accessing Notion pages, Google Docs, internal tools requiring login.

**Key Advantage:** Playwright MCP with Edge preserves your logged-in browser sessions.

**Steps:**

1. **Log in manually first** (one-time setup):
   - Open Edge normally
   - Log into the sites you need to access
   - Sessions are preserved for MCP usage

2. **Navigate to authenticated page:**
   ```
   mcp__playwright__browser_navigate({ url: "https://notion.so/page" })
   ```

3. **Wait longer for dynamic content:**
   ```
   mcp__playwright__browser_wait_for({ time: 7 })
   ```

4. **Extract using appropriate selectors:**
   ```javascript
   mcp__playwright__browser_evaluate({
     function: "() => {
       const content = document.querySelector(
         '[data-content-editable-root=\"true\"], main, [role=\"main\"]'
       );
       return { text: content?.innerText || 'Content not found' };
     }"
   })
   ```

**Troubleshooting:**
- **401/403 errors:** Log in manually in Edge first
- **Content not loading:** Increase wait time to 10+ seconds
- **Wrong content extracted:** Check selectors in references/playwright-mcp-tools-api.md

---

### Workflow 5: Multi-Tab Operations

**Use when:** Extracting content from multiple pages within the same authenticated session.

**Steps:**

1. **List existing tabs:**
   ```
   mcp__playwright__browser_tabs({ action: "list" })
   ```

2. **Create new tabs for each page:**
   ```
   mcp__playwright__browser_tabs({ action: "new", url: "https://example.com/page1" })
   mcp__playwright__browser_tabs({ action: "new", url: "https://example.com/page2" })
   mcp__playwright__browser_tabs({ action: "new", url: "https://example.com/page3" })
   ```

3. **Process each tab sequentially:**
   ```
   mcp__playwright__browser_tabs({ action: "select", index: 1 })
   mcp__playwright__browser_wait_for({ time: 2 })
   // Extract content from tab 1

   mcp__playwright__browser_tabs({ action: "select", index: 2 })
   mcp__playwright__browser_wait_for({ time: 2 })
   // Extract content from tab 2
   ```

4. **Clean up tabs:**
   ```
   mcp__playwright__browser_tabs({ action: "close", index: 2 })
   mcp__playwright__browser_tabs({ action: "close", index: 1 })
   ```

**Important Notes:**
- All tabs share the same authentication context (logged-in state)
- Tab indices are 0-based (first tab = 0)
- Tabs are processed sequentially, not concurrently
- Useful for batch extraction from authenticated sites

---

### Workflow 6: Detect Authentication Requirements

**Use when:** Attempting to extract content from sites that may require login.

**Steps:**

1. **Navigate to page:**
   ```
   mcp__playwright__browser_navigate({ url: "https://example.com" })
   mcp__playwright__browser_wait_for({ time: 3 })
   ```

2. **Check for authentication indicators:**
   ```javascript
   mcp__playwright__browser_evaluate({
     function: "() => {
       const hasPasswordInput = !!document.querySelector('input[type=\"password\"]');
       const hasLoginForm = !!document.querySelector('form[action*=\"login\"]');
       const isAuthPage = /login|signin|auth/i.test(window.location.href);

       return {
         requiresAuth: hasPasswordInput || hasLoginForm || isAuthPage,
         currentUrl: window.location.href,
         pageTitle: document.title
       };
     }"
   })
   ```

3. **If authentication required, inform user:**
   - Display clear message that login is needed
   - Provide the URL they need to visit
   - Explain that they should log in manually in Edge
   - Confirm that login will be preserved for future operations

4. **Retry after user logs in:**
   - User logs in manually in Edge
   - Retry the extraction workflow
   - Authentication will now be available

**Best Practice:** Always check for authentication before bulk extraction operations. This provides better user experience and clearer error messages.

---

## Browser Capabilities & Limitations

### Single Browser Instance

**Important:** Playwright MCP with Edge runs a **single browser instance** at a time.

**What this means:**
- You cannot run multiple independent browser sessions concurrently
- All tabs share the same cookies, sessions, and authentication
- Operations are sequential, not truly parallel

**Workarounds:**
- **Use tabs** for managing multiple pages within same session (see Workflow 5)
- **Use subagents** for token isolation during large extractions
- **Alternative:** For true concurrency, consider `concurrent-browser-mcp` (github.com/sailaoda/concurrent-browser-mcp) which supports up to 20 parallel instances

### Tab Management vs Concurrent Instances

| Feature | Browser Tabs | Concurrent Instances |
|---------|-------------|---------------------|
| Implementation | Built-in `browser_tabs` | Requires concurrent-browser-mcp |
| Authentication | Shared across all tabs | Isolated per instance |
| Use Case | Multiple pages, same site | Multiple sites, isolated sessions |
| Execution | Sequential | Truly parallel |
| Setup | No additional config | Separate MCP server |

---

## Headless Mode & Session Persistence

### Running in Headless Mode

Playwright MCP supports headless mode where the browser runs without a visible window:

**Configuration:**
```json
{
  "command": "npx",
  "args": [
    "@playwright/mcp@latest",
    "--browser=msedge",
    "--headless",
    "--extension"
  ],
  "env": {
    "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "your-token"
  }
}
```

**Important:** Headless mode with extension may have limitations. Test with visible browser first.

### Preserving Authentication in Headless Mode

**YES! Authentication persists in headless mode using:**

1. **Persistent Profile (Default):**
   - Browser stores cookies, local storage, auth tokens across sessions
   - Works automatically with extension mode
   - Login once, reuse indefinitely

2. **Storage State Files:**
   ```json
   {
     "args": [
       "@playwright/mcp@latest",
       "--browser=msedge",
       "--storage-state=/path/to/state.json"
     ]
   }
   ```
   - Saves cookies and storage to file
   - Can be shared across projects
   - Useful for reproducible setups

3. **Extension Mode (Recommended):**
   - Connects to existing Edge profile
   - Preserves all logged-in sessions
   - Works with both headed and headless modes

**Best Practice:** Use extension mode with persistent profile for most reliable authentication preservation.

---

## Best Practices

### Token Management

**⚠️ Critical:** Always use `browser_wait_for` after `browser_navigate` before extracting content.

```javascript
// ❌ BAD: Returns 40K+ tokens
mcp__playwright__browser_navigate({ url: "..." })
mcp__playwright__browser_snapshot()

// ✅ GOOD: Manageable token count
mcp__playwright__browser_navigate({ url: "..." })
mcp__playwright__browser_wait_for({ time: 3 })
mcp__playwright__browser_snapshot()
```

**For large multi-page extractions:**
- Main agent: Navigate, extract metadata, write files, spawn subagents
- Subagents: Extract individual pages, write immediately, return metadata only
- Result: 77% token reduction (65K → 15K)

### Element Selection Strategy

**Priority order:**
1. Use snapshot refs (most reliable)
2. Semantic selectors (`main`, `article`, `[role="main"]`)
3. Data attributes (`[data-testid="..."]`)
4. Class names (less reliable)
5. Text content matching (last resort)

**Example selector fallbacks:**
```javascript
const selectors = [
  '[data-content-editable-root="true"]',  // Specific
  'main',                                  // Semantic
  '[role="main"]',                         // ARIA
  '.main-content'                          // Class (last resort)
];
```

### JavaScript Evaluation Guidelines

**✅ DO:**
- Use arrow function format: `"() => { }"`
- Return JSON-serializable objects
- Include try-catch for error handling
- Validate elements exist before accessing

**❌ DON'T:**
- Use async functions (use Promises instead)
- Return DOM elements (return data instead)
- Assume elements exist (check first)
- Forget to handle null/undefined

### Error Handling

**Common errors and solutions:**

| Error | Cause | Solution |
|-------|-------|----------|
| Token overflow | Navigation without wait | Add `browser_wait_for({ time: 3 })` |
| Element not found | Stale snapshot | Get fresh snapshot |
| Content not loading | Insufficient wait | Increase wait time or wait for selector |
| Private page (403) | Not logged in | Log in manually in Edge first |
| Empty extraction | Wrong selector | Check references for selector patterns |

---

## Available Tools

Playwright MCP provides these core tools (see `references/playwright-mcp-tools-api.md` for complete details):

**Navigation & Inspection:**
- `browser_navigate` - Navigate to URL
- `browser_snapshot` - Get accessibility tree
- `browser_wait_for` - Wait for time/selector/state
- `browser_console_messages` - Get console output

**Content Extraction:**
- `browser_evaluate` - Execute JavaScript

**Interactions:**
- `browser_click` - Click elements
- `browser_type` - Type text
- `browser_select_option` - Select dropdown options
- `browser_press_key` - Press keyboard keys
- `browser_drag` - Drag and drop
- `browser_handle_dialog` - Handle alerts/confirms

**Session Management:**
- `browser_close` - Close browser
- `browser_tabs` - List, create, close, or select tabs

**80% of tasks use:** navigate, wait_for, evaluate, click, type, close, browser_tabs

---

## Common Patterns

### Pattern: Find All Links

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

### Pattern: Filter Noise Content

```javascript
const noisePatterns = [
  /^Subscribe$/i,
  /^Sign in$/i,
  /^Share$/i,
  /^View comments/i
];

const isNoise = (text) => {
  return noisePatterns.some(pattern => pattern.test(text.trim()));
};
```

### Pattern: Deduplicate Content

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

---

## Resources

### Scripts

**`scripts/install-playwright-edge.sh`**
Smart installation script for Playwright MCP with Edge. Features:
- Detects existing configuration and exits early if already properly set up
- Searches other projects for existing tokens and automatically reuses from most recent project
- Uses git commit dates (git repos) or file modification dates (non-git folders) to determine recency
- Handles extension download only when needed
- Provides step-by-step prompts for manual steps only when no token can be reused
- Configures Claude Code MCP server with proper Edge and extension settings

**`scripts/check-edge-configs.sh`**
List all directories where Playwright MCP is configured with Edge browser. Useful for verifying configuration and finding existing setups.

**`scripts/extract_web_content.py`** (NEW!)
Standalone content extraction script that bypasses all MCP and context limits. Features:
- **Launches its own Playwright instance** (does NOT use MCP server)
- Site-agnostic design - calling agent specifies selectors and parameters
- Extracts unlimited content size directly to files (tested with 110KB+)
- Zero token usage in LLM context
- Returns JSON metadata for programmatic processing
- Supports cookie popup handling
- Configurable wait times for dynamic content

Usage:
```bash
python scripts/extract_web_content.py <url> <output_file> \
    --selectors "main" "article" "[role=main]" \
    --wait-time 5000 \
    --cookie-button "Accept"
```

**When agents should use this script:**
- Building notion-extractor, substack-extractor, or similar content extraction agents
- Need to extract >10KB content without context overflow
- Want zero token usage for large content
- Need deterministic extraction that always works the same way

See `references/site-presets.md` for recommended parameters for common sites.

### References

**`references/playwright-mcp-tools-api.md`** (COMPREHENSIVE)
Complete API reference for all Playwright MCP tools with:
- Detailed parameter documentation
- Common usage patterns for each tool
- Wait strategies for different scenarios
- Token management best practices
- Error handling strategies
- Selector strategies and examples
- Advanced techniques (deduplication, noise filtering, infinite scroll)

**Read this reference when:**
- Need details on specific tool parameters
- Troubleshooting extraction issues
- Learning advanced patterns
- Optimizing token usage

**`references/edge-installation-guide.md`**
Step-by-step installation guide covering:
- Manual installation steps
- Configuration management commands
- Troubleshooting common issues
- Security considerations
- Advanced configuration (separate profiles, multiple configs)
- Example workflows and use cases

**Read this reference when:**
- Installing Playwright MCP for the first time
- Troubleshooting installation issues
- Need configuration management commands
- Setting up advanced configurations

**`references/site-presets.md`** (NEW!)
Site-specific extraction parameters for the standalone extraction script. Provides:
- Recommended CSS selectors for common sites (Notion, Substack, Medium)
- Optimal wait times for different site types
- Cookie handling strategies
- Debugging guidance for failed extractions
- Custom site examples (Reddit, Wikipedia, Hacker News)
- Agent workflow patterns

**Read this reference when:**
- Building content extraction agents
- Using `extract_web_content.py` for specific sites
- Extraction fails and need alternative selectors
- Need guidance on wait times and cookie handling

---

## Configuration Management

### View Configuration

```bash
# Current directory
jq ".projects.\"/$(pwd)\".mcpServers.playwright" ~/.claude.json

# Specific directory
jq '.projects."/path/to/project".mcpServers.playwright' ~/.claude.json

# All Playwright configs
jq '.projects | to_entries[] | select(.value.mcpServers.playwright) | .key' ~/.claude.json

# Only Edge configs
scripts/check-edge-configs.sh
```

### Modify Configuration

```bash
# Remove configuration
claude mcp remove playwright

# Re-add with new token
claude mcp add-json "playwright" '{"command":"npx","args":["@playwright/mcp@latest","--browser=msedge","--extension"],"env":{"PLAYWRIGHT_MCP_EXTENSION_TOKEN":"NEW-TOKEN"}}'
```

---

## Security Notes

⚠️ **Important:**
- Extension has access to browsing sessions and cookies
- Token provides control over your browser
- Keep tokens private (never commit to git)
- Consider using separate Edge profile for automation
- Only install on trusted devices

---

## Troubleshooting Quick Reference

| Problem | Quick Fix |
|---------|-----------|
| Wrong browser opens | Check `--browser=msedge` in args |
| Token invalid | Re-extract from edge://extensions/ → status.html |
| Content not loading | Increase wait time to 7+ seconds |
| Element not found | Get fresh snapshot before interaction |
| 40K+ token response | Add browser_wait_for after navigate |
| Empty extraction | Check selector patterns in API reference |
| 403 error | Log into site manually in Edge first |

For detailed troubleshooting, see `references/edge-installation-guide.md` and `references/playwright-mcp-tools-api.md`.
