# Playwright MCP Troubleshooting Guide

Common issues and solutions for Playwright MCP setup with Edge on macOS.

## Extension Installation Issues

### Extension pages blocked (ERR_BLOCKED_BY_CLIENT)

**Symptoms:**
- Cannot access extension pages
- Error message when trying to open status.html

**Solutions:**
- Make sure you loaded the extension as "unpacked" in developer mode
- Try removing and reinstalling the extension
- Clear browser cache and restart Edge

### Extension not appearing in Extensions list

**Symptoms:**
- Extension installed but not visible in edge://extensions/

**Solutions:**
- Verify the extension directory exists at `/tmp/playwright-mcp-extension`
- Check that manifest.json exists in the extension directory
- Enable Developer mode in Edge before loading
- Try downloading a different version from GitHub releases

### Cannot find status.html

**Symptoms:**
- No "Inspectable views" or "status.html" link in extension details

**Solutions:**
- Refresh the edge://extensions/ page
- Click on "Details" for the Playwright MCP Bridge extension
- Look under "Inspect views" section
- If still missing, try reinstalling the extension

## Connection and Configuration Issues

### Extension connection timeout

**Symptoms:**
- MCP server shows as not connected
- Timeout errors when trying to use Playwright

**Solutions:**
- Verify the token is correct in your MCP configuration
- Make sure you used `--browser=msedge` in the args
- Check that the extension is enabled in Edge
- Restart Claude Code after configuration changes
- Restart Edge browser

### Wrong browser opens (Chrome instead of Edge)

**Symptoms:**
- Chrome launches instead of Edge when using Playwright
- Can't connect to logged-in Edge sessions

**Solutions:**
- Ensure `--browser=msedge` is in the args array
- Remove and re-add the MCP configuration:
  ```bash
  claude mcp remove playwright
  python3 scripts/configure_mcp.py YOUR-TOKEN
  ```
- Verify configuration with:
  ```bash
  jq ".projects.\"/$(pwd)\".mcpServers.playwright" ~/.claude.json
  ```

### 401 Unauthorized errors in console

**Symptoms:**
- 401 errors when trying to access pages
- Authentication failures

**Solutions:**
- Some Notion pages or authenticated content may require you to be logged in
- The extension preserves your browser sessions, so log in manually first
- Make sure you're using the same Edge profile where the extension is installed
- Clear cookies and log in again if sessions expired

### Token not recognized

**Symptoms:**
- "Invalid token" or similar authentication errors
- Extension shows as disconnected

**Solutions:**
- Verify you copied the full token from status.html
- Token should be 40+ characters long
- Make sure there are no extra spaces or quotes
- Get a fresh token by:
  1. Going to edge://extensions/
  2. Clicking on Playwright MCP Bridge → status.html
  3. Copying the token again
- Reconfigure with the new token:
  ```bash
  python3 scripts/configure_mcp.py NEW-TOKEN
  ```

## Claude Code Integration Issues

### MCP server not listed

**Symptoms:**
- `claude mcp list` doesn't show Playwright
- Configuration seems missing

**Solutions:**
- Check if configuration file exists: `~/.claude.json`
- Verify configuration is present:
  ```bash
  jq '.projects' ~/.claude.json
  ```
- Reconfigure using the script:
  ```bash
  python3 scripts/configure_mcp.py YOUR-TOKEN
  ```
- Make sure you're in the correct project directory

### MCP server shows as disconnected

**Symptoms:**
- Playwright appears in `claude mcp list` but shows as disconnected
- Red X or "Not connected" status

**Solutions:**
- Restart Claude Code completely
- Verify the extension is running in Edge (visit edge://extensions/)
- Check that npx and Node.js are installed:
  ```bash
  npx --version
  node --version
  ```
- If not installed, install Node.js:
  ```bash
  brew install node
  ```
- Try removing and reconfiguring:
  ```bash
  claude mcp remove playwright
  python3 scripts/configure_mcp.py YOUR-TOKEN
  ```

### Commands not working

**Symptoms:**
- Claude Code doesn't respond to Playwright commands
- "Navigate to..." doesn't open browser

**Solutions:**
- Verify setup with the verification script:
  ```bash
  python3 scripts/verify_setup.py
  ```
- Make sure Claude Code was restarted after configuration
- Check that the MCP server is connected in `claude mcp list`
- Try a simple test command:
  ```bash
  # In Claude Code conversation:
  "Use Playwright to navigate to https://example.com"
  ```

## Verification Checklist

Use this checklist to verify your setup is correct:

- [ ] Edge is installed on macOS
- [ ] Extension is downloaded to `/tmp/playwright-mcp-extension`
- [ ] Extension is loaded in Edge as "unpacked"
- [ ] Extension shows in edge://extensions/ as enabled
- [ ] Token has been copied from status.html
- [ ] MCP server is configured with correct token and `--browser=msedge`
- [ ] `claude mcp list` shows Playwright as connected
- [ ] Claude Code has been restarted
- [ ] Test navigation command works

Run the verification script to check all of these automatically:
```bash
python3 scripts/verify_setup.py
```

## Getting Help

If you're still experiencing issues after trying these solutions:

1. Check the latest GitHub issues: https://github.com/microsoft/playwright-mcp/issues
2. Verify you're using the latest extension version
3. Check Claude Code logs for error messages
4. Try the complete reinstallation process from scratch

## Complete Reinstallation

If nothing else works, try a complete clean reinstall:

```bash
# 1. Remove MCP configuration
claude mcp remove playwright

# 2. Remove extension files
rm -rf /tmp/playwright-mcp-extension
rm /tmp/playwright-mcp-extension.zip

# 3. Remove extension from Edge
# Go to edge://extensions/ and click "Remove"

# 4. Restart Edge completely

# 5. Start fresh installation
python3 scripts/install_extension.py
# Then follow the setup guide in edge-setup.md
```
