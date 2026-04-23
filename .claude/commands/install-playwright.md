---
description: Install and verify Playwright MCP with Microsoft Edge browser automation. Handles extension installation, token extraction, Claude Code configuration, and comprehensive verification. Use when setting up Playwright MCP for the first time or troubleshooting installation issues.
---

# Install Playwright MCP

Guide the user through installing and configuring Playwright MCP with Microsoft Edge for browser automation.

## Task Overview

You are helping the user set up Playwright MCP, which enables Claude Code to control Microsoft Edge for browser automation tasks like content extraction, form filling, and authenticated browsing.

## Installation Workflow

Follow these steps in sequence. Use the bundled scripts from the plugin's scripts directory for automated installation.

### Step 1: Check Current Configuration

First, check if Playwright MCP is already configured:

```bash
jq ".projects.\"/$(pwd)\".mcpServers.playwright" ~/.claude.json
```

If configuration exists and includes `"browser":"msedge"` and `PLAYWRIGHT_MCP_EXTENSION_TOKEN`, ask the user if they want to:
- Skip installation (already configured)
- Verify existing setup
- Reconfigure/reinstall

### Step 2: Install Extension

Use the automated installation script:

```bash
python3 ~/.claude/plugins/marketplaces/*/playwright-mcp/scripts/install_extension.py
```

Or if installed locally:
```bash
python3 playwright-mcp/scripts/install_extension.py
```

The script will:
- Download the latest Playwright MCP extension from GitHub
- Extract it to `/tmp/playwright-mcp-extension`
- Provide next steps for loading in Edge

**Then guide the user to:**
1. Open Microsoft Edge
2. Navigate to `edge://extensions/`
3. Enable "Developer mode" (toggle in top-right corner)
4. Click "Load unpacked"
5. Select `/tmp/playwright-mcp-extension`
6. Verify "Playwright MCP Bridge" appears in extensions list

### Step 3: Extract Extension Token

Guide the user to extract the extension token:

1. In Edge, ensure you're still at `edge://extensions/`
2. Find "Playwright MCP Bridge" extension
3. Click "Details" on the extension
4. Look for "Inspect views" section
5. Click on `status.html` to open the extension status page
6. Copy the token from the displayed configuration (40+ character string after `PLAYWRIGHT_MCP_EXTENSION_TOKEN`)

**Troubleshooting:**
- If `status.html` isn't visible, refresh the extensions page
- If you see ERR_BLOCKED_BY_CLIENT, ensure extension is loaded as "unpacked" with developer mode enabled

### Step 4: Configure Claude Code

Once the user provides the token, configure Claude Code:

```bash
python3 ~/.claude/plugins/marketplaces/*/playwright-mcp/scripts/configure_mcp.py <TOKEN>
```

Or if installed locally:
```bash
python3 playwright-mcp/scripts/configure_mcp.py <TOKEN>
```

Replace `<TOKEN>` with the actual token from Step 3.

The script will:
- Add Playwright MCP server configuration to Claude Code
- Set browser to `msedge`
- Include the extension token in environment variables
- Verify configuration was added successfully

### Step 5: Verify Setup

Run comprehensive verification:

```bash
python3 ~/.claude/plugins/marketplaces/*/playwright-mcp/scripts/verify_setup.py
```

Or if installed locally:
```bash
python3 playwright-mcp/scripts/verify_setup.py
```

The verification checks:
- Edge browser installation
- Extension files presence
- MCP server configuration
- Connection status
- Configuration file integrity

Review the output and address any issues identified.

### Step 6: Restart and Test

**Critical:** Inform the user they MUST restart Claude Code for the MCP server to load.

After restart, test with a simple operation:
```
"Navigate to https://example.com using the browser"
```

Verify that Edge opens and navigates to the page.

## Troubleshooting

If issues occur, consult the troubleshooting reference in the `playwright-setup` skill:

**Common Issues:**
- **Extension not loading:** Check Developer mode is enabled, files exist at `/tmp/playwright-mcp-extension`
- **Token not working:** Verify token is 40+ characters, copied correctly from status.html
- **Wrong browser opens:** Ensure `--browser=msedge` in configuration, may need to remove and re-add config
- **Connection timeout:** Verify extension is enabled, token is correct, Claude Code was restarted
- **401/403 errors:** User needs to log into websites manually in Edge first

For detailed troubleshooting steps, reference the bundled documentation:
`playwright-mcp/references/troubleshooting.md`

## Manual Approach

If automated scripts fail, the user can follow manual installation steps from:
`playwright-mcp/references/edge-setup.md`

## Expected Outcome

After successful installation:
- Playwright MCP extension loaded in Edge
- Claude Code configured with extension token
- `claude mcp list` shows: `playwright: npx @playwright/mcp@latest --browser=msedge --extension - ✓ Connected`
- Browser automation commands work correctly
- User can proceed to use Playwright MCP for content extraction and automation tasks

## Next Steps

After installation, inform the user:
- The `playwright-mcp-usage` skill provides comprehensive usage guidance for the Playwright MCP server
- They can extract content from websites, including authenticated sites
- Edge browser sessions are preserved (stay logged in)
- Reference documentation is available for all MCP tools and workflows
