# Playwright MCP Setup for Edge on macOS

Complete guide to set up Playwright MCP with Microsoft Edge on macOS, enabling Claude Code to control your browser while preserving logged-in sessions.

## Prerequisites

- Microsoft Edge installed on macOS
- Claude Code installed

## Installation Steps

### Step 1: Install Microsoft Edge (if not already installed)

```bash
# Using Homebrew
brew install --cask microsoft-edge

# Or download from Microsoft
# https://www.microsoft.com/edge/download
```

### Step 2: Download Playwright MCP Bridge Extension

The extension can be downloaded manually or using the provided script:

**Using the script (recommended):**
```bash
python3 scripts/install_extension.py
```

**Manual download:**
```bash
cd /tmp
curl -L -o playwright-mcp-extension.zip https://github.com/microsoft/playwright-mcp/releases/latest/download/playwright-mcp-extension-0.0.43.zip
unzip -q playwright-mcp-extension.zip -d playwright-mcp-extension
```

**Note:** Check https://github.com/microsoft/playwright-mcp/releases for the latest version number.

### Step 3: Install Extension in Edge

1. Open Edge and navigate to: `edge://extensions/`
2. **Enable Developer mode** - Toggle the switch in the top-right corner
3. **Click "Load unpacked"** (or "Entpackte Erweiterung laden" in German)
4. Navigate to and select: `/tmp/playwright-mcp-extension`
5. **Verify installation** - You should see "Playwright MCP Bridge" in your extensions list

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

### Step 5: Configure Claude Code MCP Server

Configure Claude Code using the provided script or manually:

**Using the script (recommended):**
```bash
python3 scripts/configure_mcp.py YOUR-TOKEN-HERE
```

**Manual configuration:**
```bash
claude mcp add-json "playwright" '{"command":"npx","args":["@playwright/mcp@latest","--browser=msedge","--extension"],"env":{"PLAYWRIGHT_MCP_EXTENSION_TOKEN":"YOUR-TOKEN-HERE"}}'
```

Example with actual token:
```bash
claude mcp add-json "playwright" '{"command":"npx","args":["@playwright/mcp@latest","--browser=msedge","--extension"],"env":{"PLAYWRIGHT_MCP_EXTENSION_TOKEN":"FZsOoFg4Z-fZ60LL7xisAMIrkuOv1eYAcHJdOdnCORE"}}'
```

### Step 6: Verify Installation

**Using the script (recommended):**
```bash
python3 scripts/verify_setup.py
```

**Manual verification:**
```bash
claude mcp list
```

You should see:
```
playwright: npx @playwright/mcp@latest --browser=msedge --extension - ✓ Connected
```

### Step 7: Restart Claude Code

Restart Claude Code for the changes to take effect.

## Testing

Ask Claude Code to navigate to a webpage:

> "Navigate to https://example.com"

Claude Code should now be able to control Edge, extract content, and save it as markdown files.

## Configuration Location

MCP configuration is stored per-directory in: `~/.claude.json`

The configuration is nested under `.projects["/your/directory/path"]`.

To view current config:
```bash
# For current directory:
jq ".projects.\"/$(pwd)\".mcpServers.playwright" ~/.claude.json

# Find all directories with Playwright MCP configured:
jq '.projects | to_entries[] | select(.value.mcpServers.playwright) | .key' ~/.claude.json

# View the full config for a specific directory:
jq '.projects."/path/to/your/project".mcpServers.playwright' ~/.claude.json
```

## Use Cases

With this setup, you can:

- **Extract content from authenticated sites** (Notion, Google Docs, internal tools)
- **Download webpages as markdown** while preserving formatting
- **Automate browser tasks** through Claude Code
- **Navigate logged-in sessions** without re-authenticating

## Example Workflow

1. Log into your sites manually in Edge (using your MCP profile)
2. Ask Claude Code: "Navigate to [URL] and extract the content"
3. Claude Code will:
   - Open the page in your logged-in Edge session
   - Extract the content using JavaScript
   - Convert to markdown
   - Save to a local file
