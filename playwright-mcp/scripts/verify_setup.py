#!/usr/bin/env python3
"""
Verify Playwright MCP setup for Edge on macOS.

This script checks if:
1. The extension is downloaded and extracted
2. The MCP server is configured in Claude Code
3. The configuration looks correct
"""

import sys
import subprocess
import json
from pathlib import Path


def check_extension():
    """Check if the extension is extracted and ready."""
    extension_path = Path("/tmp/playwright-mcp-extension")

    if not extension_path.exists():
        print("❌ Extension not found at /tmp/playwright-mcp-extension")
        print("   Run: python3 scripts/install_extension.py")
        return False

    # Check for manifest.json
    manifest = extension_path / "manifest.json"
    if not manifest.exists():
        print("❌ Extension directory exists but manifest.json not found")
        print("   The extension may be corrupted. Try reinstalling.")
        return False

    print(f"✅ Extension found at: {extension_path}")
    return True


def check_mcp_config():
    """Check if Playwright MCP is configured."""
    result = subprocess.run(
        ["claude", "mcp", "list"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("❌ Unable to check MCP configuration")
        print(f"   Error: {result.stderr}")
        return False

    output = result.stdout

    if "playwright" not in output.lower():
        print("❌ Playwright MCP not configured")
        print("   Run: python3 scripts/configure_mcp.py <TOKEN>")
        return False

    print("✅ Playwright MCP is configured")

    # Check if it shows as connected
    if "✓ Connected" in output or "Connected" in output:
        print("✅ MCP server is connected")
    else:
        print("⚠️  MCP server may not be connected")
        print("   Check the output below:")

    print("\nMCP Status:")
    print(output)

    return True


def check_edge():
    """Check if Edge is installed."""
    edge_paths = [
        "/Applications/Microsoft Edge.app",
        Path.home() / "Applications/Microsoft Edge.app"
    ]

    for path in edge_paths:
        if Path(path).exists():
            print(f"✅ Microsoft Edge found at: {path}")
            return True

    print("⚠️  Microsoft Edge not found in standard locations")
    print("   You can install it with: brew install --cask microsoft-edge")
    return False


def check_config_file():
    """Check the Claude Code config file for Playwright settings."""
    config_path = Path.home() / ".claude.json"

    if not config_path.exists():
        print("⚠️  Claude config file not found at ~/.claude.json")
        return False

    try:
        with open(config_path) as f:
            config = json.load(f)

        # Look for playwright in any project's mcpServers
        found_playwright = False
        projects = config.get("projects", {})

        for project_path, project_config in projects.items():
            mcp_servers = project_config.get("mcpServers", {})
            if "playwright" in mcp_servers:
                found_playwright = True
                pw_config = mcp_servers["playwright"]

                print(f"\n✅ Found Playwright config in project: {project_path}")
                print(f"   Browser: {[arg for arg in pw_config.get('args', []) if '--browser' in arg]}")

                token = pw_config.get("env", {}).get("PLAYWRIGHT_MCP_EXTENSION_TOKEN", "")
                if token:
                    print(f"   Token (first 10 chars): {token[:10]}...")
                else:
                    print("   ⚠️  No token found in config")

        if not found_playwright:
            print("⚠️  Playwright not found in ~/.claude.json")
            print("   Run: python3 scripts/configure_mcp.py <TOKEN>")
            return False

        return True

    except Exception as e:
        print(f"⚠️  Error reading config: {e}")
        return False


def main():
    """Main entry point."""
    print("Verifying Playwright MCP setup for Edge on macOS...\n")

    checks = [
        ("Edge Browser", check_edge),
        ("Extension Files", check_extension),
        ("MCP Configuration", check_mcp_config),
        ("Config File", check_config_file),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n--- Checking {name} ---")
        results.append(check_func())
        print()

    # Summary
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ All checks passed ({passed}/{total})")
        print("\nYour Playwright MCP setup looks good!")
        print("\nNext steps:")
        print("1. Make sure the extension is loaded in Edge (edge://extensions/)")
        print("2. Restart Claude Code")
        print("3. Test with: 'Navigate to https://example.com'")
        return 0
    else:
        print(f"⚠️  {passed}/{total} checks passed")
        print("\nPlease fix the issues above and run this script again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
