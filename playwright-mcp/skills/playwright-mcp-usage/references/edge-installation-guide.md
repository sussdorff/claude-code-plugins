# Playwright MCP + Edge Installation Guide

Complete guide to set up Playwright MCP with Microsoft Edge on macOS, enabling Claude Code to control your browser while preserving logged-in sessions.

---

## Why Use Edge with Playwright MCP?

**Key Benefits:**
- **Preserve logged-in sessions:** Control your actual browser with existing logins
- **Access authenticated content:** Extract from Notion, Google Docs, internal tools
- **No re-authentication:** Use your existing browser profile
- **Better compatibility:** Some sites work better with Edge than headless Chrome

---

## Prerequisites

- Microsoft Edge installed on macOS
- Claude Code installed
- Basic terminal/command-line knowledge

---

## Installation Steps

### Step 1: Install Microsoft Edge

```bash
# Using Homebrew
brew install --cask microsoft-edge

# Or download from Microsoft
# https://www.microsoft.com/edge/download
```

---

### Step 2: Download Playwright MCP Bridge Extension

```bash
# Download and extract the latest extension
cd /tmp
curl -L -o playwright-mcp-extension.zip https://github.com/microsoft/playwright-mcp/releases/latest/download/playwright-mcp-extension-0.0.43.zip
unzip -q playwright-mcp-extension.zip -d playwright-mcp-extension
```

**Note:** Check https://github.com/microsoft/playwright-mcp/releases for the latest version number.

**Alternative:** Use the automated installation script:
```bash
scripts/install-playwright-edge.sh
```

---

### Step 3: Install Extension in Edge

1. Open Edge and navigate to: `edge://extensions/`

2. **Enable Developer mode** - Toggle the switch in the top-right corner

3. **Click "Load unpacked"** (or "Entpackte Erweiterung laden" in German)

4. Navigate to and select: `/tmp/playwright-mcp-extension`

5. **Verify installation** - You should see "Playwright MCP Bridge" in your extensions list

---

### Step 4: Get the Extension Token

1. In Edge, navigate to: `edge://extensions/`

2. Find "Playwright MCP Bridge" in your extensions list

3. Under "Ansichten überprüfen" (Inspect views) or "Inspectable views", **click on `status.html`**
   - This will open the extension's status page directly

4. Look for the configuration block that shows:
   ```json
   {
     "mcpServers": {
       "playwright": {
         "command": "npx",
         "args": ["@playwright/mcp@latest", "--extension"],
         "env": {
           "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "YOUR-TOKEN-HERE"
         }
       }
     }
   }
   ```

5. **Copy the token value** from `PLAYWRIGHT_MCP_EXTENSION_TOKEN`

---

### Step 5: Configure Claude Code MCP Server

Run this command, replacing `YOUR-TOKEN-HERE` with the token from Step 4:

```bash
claude mcp add-json "playwright" '{"command":"npx","args":["@playwright/mcp@latest","--browser=msedge","--extension"],"env":{"PLAYWRIGHT_MCP_EXTENSION_TOKEN":"YOUR-TOKEN-HERE"}}'
```

Example with actual token:
```bash
claude mcp add-json "playwright" '{"command":"npx","args":["@playwright/mcp@latest","--browser=msedge","--extension"],"env":{"PLAYWRIGHT_MCP_EXTENSION_TOKEN":"FZsOoFg4Z-fZ60LL7xisAMIrkuOv1eYAcHJdOdnCORE"}}'
```

**Important:** The `--browser=msedge` flag is critical for opening Edge instead of Chrome.

---

### Step 6: Verify Installation

```bash
claude mcp list
```

You should see:
```
playwright: npx @playwright/mcp@latest --browser=msedge --extension - ✓ Connected
```

---

### Step 7: Restart Claude Code

Restart Claude Code for the changes to take effect.

---

## Testing

Ask Claude Code to navigate to a webpage:

> "Navigate to https://example.com"

Claude Code should now be able to control Edge, extract content, and save it as markdown files.

---

## Troubleshooting

### Extension pages blocked (ERR_BLOCKED_BY_CLIENT)
- Make sure you loaded the extension as "unpacked" in developer mode
- Try removing and reinstalling the extension

### Extension connection timeout
- Verify the token is correct in your MCP configuration
- Make sure you used `--browser=msedge` in the args
- Restart Claude Code after configuration changes

### Wrong browser opens (Chrome instead of Edge)
- Ensure `--browser=msedge` is in the args array
- Remove and re-add the MCP configuration with:
  ```bash
  claude mcp remove playwright
  claude mcp add-json "playwright" '{"command":"npx","args":["@playwright/mcp@latest","--browser=msedge","--extension"],"env":{"PLAYWRIGHT_MCP_EXTENSION_TOKEN":"YOUR-TOKEN"}}'
  ```

### 401 errors in console
- Some Notion pages or authenticated content may require you to be logged in
- The extension preserves your browser sessions, so log in manually first

### Token appears invalid
- Re-extract the token from edge://extensions/ → Playwright MCP Bridge → status.html
- Make sure you copied the entire token string
- Remove and re-add the MCP configuration with the new token

---

## Configuration Management

### View Current Configuration

```bash
# For current directory:
jq ".projects.\"/$(pwd)\".mcpServers.playwright" ~/.claude.json

# View full config for specific directory:
jq '.projects."/path/to/your/project".mcpServers.playwright' ~/.claude.json
```

### Find All Directories with Playwright MCP

```bash
# All Playwright configs:
jq '.projects | to_entries[] | select(.value.mcpServers.playwright) | .key' ~/.claude.json

# Only Edge configs (using the bundled script):
scripts/check-edge-configs.sh
```

### Remove Configuration

```bash
# Remove from Claude Code:
claude mcp remove playwright

# Or manually edit ~/.claude.json for specific directory
```

---

## Use Cases

With this setup, you can:

- **Extract content from authenticated sites** (Notion, Google Docs, internal tools)
- **Download webpages as markdown** while preserving formatting
- **Automate browser tasks** through Claude Code
- **Navigate logged-in sessions** without re-authenticating
- **Fill forms and submit data** on websites
- **Test web applications** with your logged-in sessions

---

## Example Workflows

### Extract Authenticated Notion Page

1. Log into Notion manually in Edge
2. Ask Claude Code: "Navigate to [Notion URL] and extract the content as markdown"
3. Claude Code will:
   - Open the page in your logged-in Edge session
   - Wait for dynamic content to load
   - Extract the content using JavaScript
   - Convert to markdown
   - Save to a local file

### Download Newsletter with Resources

1. Ask: "Extract this Substack newsletter and all linked resources"
2. Claude Code will:
   - Navigate to the newsletter
   - Extract the main article
   - Find all linked Notion pages, Google Drive files, downloads
   - Extract each resource in separate contexts
   - Organize everything into a structured directory

### Automated Testing

1. Ask: "Test the login flow on [URL]"
2. Claude Code will:
   - Navigate to the page
   - Fill in credentials
   - Submit the form
   - Verify successful login
   - Report results

---

## Security Considerations

⚠️ **Important Security Notes:**

- The extension has access to your browsing session and cookies
- Only install on trusted devices
- Token provides access to control your browser
- Keep your token private (never commit to git)
- Consider using a separate Edge profile for automation
- Review extension permissions in edge://extensions/

---

## Advanced Configuration

### Using a Separate Profile

To isolate automation from your personal browsing:

1. Create a new Edge profile: Settings → Profiles → Add profile
2. Install the extension in the new profile
3. Get a new token from the new profile
4. Configure Claude Code with the profile-specific token

### Multiple Configurations

You can have different configurations per directory. Claude Code stores MCP configs per-project in `~/.claude.json` under `.projects["/path/to/project"]`.

---

**Created:** 2025-10-24
**Tested on:** macOS 14.6 (Sonoma)
**Edge Version:** Latest stable
**Claude Code:** Latest stable
**Extension Version:** 0.0.43
