# Playwright MCP Plugin

Complete toolkit for browser automation with Playwright MCP and Microsoft Edge - includes installation, configuration, comprehensive usage guidance, and reference documentation for content extraction, form filling, and authenticated browsing.

## Overview

This plugin enables Claude Code to control Microsoft Edge for browser automation tasks through the Playwright MCP (Model Context Protocol) server. It provides everything you need from initial setup through advanced usage patterns.

The plugin preserves logged-in browser sessions, allowing Claude to interact with authenticated websites (Notion, Google Docs, internal tools, paywalled content) without re-authenticating.

## Features

### Installation & Setup
- **Automated installation** - Scripts to download, configure, and verify Playwright MCP with Edge
- **Token extraction** - Guided workflow to extract and configure extension tokens
- **Configuration management** - Tools to view, modify, and troubleshoot MCP configurations
- **Comprehensive verification** - Health checks for all components
- **Troubleshooting guides** - Solutions for common installation issues

### Browser Automation
- **Content extraction** - Extract articles, documentation, and web content (including authenticated sites)
- **Form automation** - Fill forms, select dropdowns, submit data
- **Dynamic content handling** - Lazy loading, infinite scroll, AJAX content
- **Multi-tab operations** - Manage multiple pages within same authenticated session
- **Session preservation** - Keep logged-in sessions across browser sessions
- **Large content extraction** - Bypass context limits with standalone extraction scripts

### Documentation
- **Complete API reference** - All Playwright MCP tools with parameters and examples
- **Site-specific presets** - Optimized selectors and wait times for Notion, Substack, Medium
- **Best practices** - Token management, element selection, error handling
- **Common patterns** - Reusable code snippets for frequent operations

## Installation

Install the plugin from your marketplace:

```bash
/plugin install playwright-mcp@your-marketplace
```

Or install from local source for development:

```bash
/plugin install playwright-mcp@local-dev
```

## Quick Start

### 1. Install Playwright MCP

Run the installation command:

```bash
/install-playwright
```

This will guide you through:
1. Installing the Playwright MCP extension for Edge
2. Extracting the extension token
3. Configuring Claude Code
4. Verifying the setup
5. Testing the connection

**Important:** You must restart Claude Code after installation for the MCP server to load.

### 2. Test the Setup

After restarting, test with a simple navigation:

```
Navigate to https://example.com using the browser
```

Edge should open and navigate to the page.

### 3. Extract Content from a Website

Try extracting content from an article:

```
Extract the main content from https://example.com/article
```

Claude will use the `playwright-usage` skill to navigate, wait for content, and extract the text.

## Usage Examples

### Extract Content from Authenticated Site

For sites requiring login (Notion, Google Docs):

1. **Log in manually first** (one-time):
   - Open Edge normally
   - Log into the site
   - Your session is preserved for MCP usage

2. **Extract content**:
   ```
   Extract content from my Notion page: https://notion.so/My-Page-123
   ```

### Fill and Submit a Form

```
Navigate to https://example.com/contact and fill out the form with:
- Name: John Doe
- Email: john@example.com
- Message: Hello from Claude Code
Then submit the form
```

### Extract Large Content (>10KB)

For very large pages that would overflow context:

```
Use the standalone extraction script to extract all content from
https://longform-article.com/post to a file
```

### Handle Lazy Loading Content

```
Navigate to https://example.com/feed, scroll to load all content,
then extract all article titles and links
```

## Components

### Commands

- **`/install-playwright`** - Install and verify Playwright MCP with Microsoft Edge - guides through extension installation, token extraction, Claude Code configuration, and verification

### Skills

- **`playwright-mcp-usage`** - Comprehensive usage guidance for browser automation with the Playwright MCP server - includes workflows for content extraction, form filling, lazy loading, multi-tab operations, and authenticated browsing

### Scripts (Plugin Root)

**Setup & Installation:**
- `install_extension.py` - Download and extract Playwright MCP extension
- `configure_mcp.py` - Configure Claude Code with extension token
- `verify_setup.py` - Comprehensive setup verification

**Usage (in playwright-mcp-usage skill):**
- `install-playwright-edge.sh` - Smart installation with token reuse across projects
- `check-edge-configs.sh` - List all Edge configurations
- `extract_web_content.py` - Standalone content extraction bypassing MCP limits

### References

**Plugin Root (Setup):**
- `edge-setup.md` - Complete manual setup guide
- `troubleshooting.md` - Comprehensive troubleshooting solutions

**Skill: playwright-mcp-usage:**
- `playwright-mcp-tools-api.md` - Complete API reference for all MCP tools
- `edge-installation-guide.md` - Installation and configuration management
- `site-presets.md` - Site-specific extraction parameters (Notion, Substack, Medium)

## Configuration

### View Current Configuration

```bash
# Current directory
jq ".projects.\"/$(pwd)\".mcpServers.playwright" ~/.claude.json

# All Playwright configurations
jq '.projects | to_entries[] | select(.value.mcpServers.playwright) | .key' ~/.claude.json

# Only Edge configurations
~/.claude/skills/playwright-usage/scripts/check-edge-configs.sh
```

### Modify Configuration

```bash
# Remove configuration
claude mcp remove playwright

# Re-add with new token
claude mcp add-json "playwright" '{"command":"npx","args":["@playwright/mcp@latest","--browser=msedge","--extension"],"env":{"PLAYWRIGHT_MCP_EXTENSION_TOKEN":"NEW-TOKEN"}}'
```

## Requirements

- **macOS** (Linux/Windows may work but are untested)
- **Microsoft Edge** browser
- **Python 3** (for installation scripts)
- **Node.js** (for running the MCP server)
- **Claude Code** with MCP support

## Troubleshooting

### Installation Issues

Run the verification script:

```bash
python3 ~/.claude/skills/playwright-setup/scripts/verify_setup.py
```

Common fixes:
- **Extension not loading:** Enable Developer mode in Edge, load extension as "unpacked"
- **Token invalid:** Re-extract from `edge://extensions/` → status.html
- **Wrong browser opens:** Check `--browser=msedge` in configuration

### Usage Issues

- **Content not loading:** Increase wait time to 7+ seconds for dynamic sites
- **Element not found:** Get fresh snapshot before interaction
- **403 errors:** Log into site manually in Edge first
- **40K+ token overflow:** Always use `browser_wait_for` after navigation

Consult the troubleshooting reference:
`~/.claude/skills/playwright-setup/references/troubleshooting.md`

## Security Notes

⚠️ **Important:**
- Extension has access to browsing sessions and cookies
- Token provides control over your browser
- Keep tokens private (never commit to git)
- Consider using separate Edge profile for automation
- Only install on trusted devices

## Advanced Usage

### Multi-Tab Operations

Extract content from multiple pages in one session:

```
Open tabs for these 3 URLs, then extract the title and main content from each:
- https://example.com/page1
- https://example.com/page2
- https://example.com/page3
```

### Subagent Pattern for Large Extractions

For extracting many pages without token overflow:

```
Create a subagent to extract content from these 10 Notion pages,
writing each to a separate file and returning only metadata
```

### Standalone Script for Public Content

For large public content (no authentication):

```bash
python ~/.claude/skills/playwright-usage/scripts/extract_web_content.py \
    "https://example.com/article" \
    "output.txt" \
    --selectors "main" "article" "[role=main]" \
    --wait-time 5000
```

## Best Practices

1. **Always wait after navigation** - Use `browser_wait_for({ time: 3 })` minimum
2. **Log in manually first** - For authenticated sites, log in once in Edge
3. **Use semantic selectors** - Prefer `main`, `article`, `[role="main"]` over classes
4. **Write immediately** - For large extractions, write to files immediately to avoid token buildup
5. **Close browser when done** - Use `browser_close()` to clean up
6. **Check configuration scope** - Playwright MCP is configured per-directory in Claude Code

## Contributing

To improve this plugin:

1. Report issues or suggest features
2. Submit pull requests with enhancements
3. Share new site presets for common websites
4. Document additional usage patterns

## License

MIT

## Resources

- [Playwright MCP Documentation](https://github.com/microsoft/playwright)
- [Claude Code MCP Guide](https://docs.claude.com/en/docs/claude-code/)
- [Edge Extensions Developer Guide](https://docs.microsoft.com/en-us/microsoft-edge/extensions-chromium/)
