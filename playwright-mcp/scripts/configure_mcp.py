#!/usr/bin/env python3
"""
Configure Claude Code MCP server for Playwright with Edge.

This script adds the Playwright MCP server configuration to Claude Code
with the specified extension token and Edge browser settings.
"""

import sys
import subprocess
import json


def configure_mcp(token, browser="msedge"):
    """
    Configure the Playwright MCP server for Claude Code.

    Args:
        token: The PLAYWRIGHT_MCP_EXTENSION_TOKEN from Edge extension
        browser: Browser to use (default: msedge)
    """
    # Build the MCP configuration JSON
    config = {
        "command": "npx",
        "args": ["@playwright/mcp@latest", f"--browser={browser}", "--extension"],
        "env": {
            "PLAYWRIGHT_MCP_EXTENSION_TOKEN": token
        }
    }

    config_json = json.dumps(config)

    # Use claude mcp add-json to configure
    cmd = ["claude", "mcp", "add-json", "playwright", config_json]

    print(f"Configuring Playwright MCP with browser: {browser}")
    print(f"Token (first 10 chars): {token[:10]}...")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Error configuring MCP: {result.stderr}")
        return False

    print("✅ Playwright MCP configured successfully!")
    print("\nVerifying configuration...")

    # Verify with claude mcp list
    verify_result = subprocess.run(
        ["claude", "mcp", "list"],
        capture_output=True,
        text=True
    )

    if verify_result.returncode == 0:
        print(verify_result.stdout)
    else:
        print("Note: Unable to verify configuration automatically.")

    print("\nNext steps:")
    print("1. Restart Claude Code for changes to take effect")
    print("2. Test with: 'Navigate to https://example.com'")

    return True


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: configure_mcp.py <EXTENSION_TOKEN> [browser]")
        print("\nExample:")
        print("  configure_mcp.py FZsOoFg4Z-fZ60LL7xisAMIrkuOv1eYAcHJdOdnCORE")
        print("  configure_mcp.py FZsOoFg4Z-fZ60LL7xisAMIrkuOv1eYAcHJdOdnCORE chrome")
        print("\nBrowser options: msedge (default), chrome, chromium")
        return 1

    token = sys.argv[1]
    browser = sys.argv[2] if len(sys.argv) > 2 else "msedge"

    if len(token) < 20:
        print("Error: Extension token seems too short. Please verify the token.")
        return 1

    if configure_mcp(token, browser):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
