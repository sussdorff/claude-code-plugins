#!/usr/bin/env python3
"""
Download and extract the Playwright MCP extension for Edge.

This script downloads the latest Playwright MCP extension and extracts it
to /tmp for loading into Edge as an unpacked extension.
"""

import sys
import subprocess
import urllib.request
from pathlib import Path


def check_dependencies():
    """Check if required commands are available."""
    try:
        subprocess.run(["curl", "--version"], capture_output=True, check=True)
        subprocess.run(["unzip", "-v"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_latest_version():
    """
    Fetch the latest version from GitHub releases.
    Returns version string or None if unable to determine.
    """
    try:
        url = "https://api.github.com/repos/microsoft/playwright-mcp/releases/latest"
        with urllib.request.urlopen(url) as response:
            import json
            data = json.loads(response.read())
            return data.get("tag_name", "0.0.43").lstrip("v")
    except Exception:
        # Fallback to known version
        return "0.0.43"


def download_and_extract(version=None):
    """Download and extract the Playwright MCP extension."""
    if version is None:
        print("Fetching latest version...")
        version = get_latest_version()

    print(f"Using version: {version}")

    extension_dir = Path("/tmp/playwright-mcp-extension")
    zip_file = Path("/tmp/playwright-mcp-extension.zip")

    # Clean up existing files
    if extension_dir.exists():
        print(f"Removing existing extension directory: {extension_dir}")
        subprocess.run(["rm", "-rf", str(extension_dir)], check=True)

    if zip_file.exists():
        print(f"Removing existing zip file: {zip_file}")
        zip_file.unlink()

    # Download
    download_url = f"https://github.com/microsoft/playwright-mcp/releases/download/v{version}/playwright-mcp-extension-{version}.zip"
    print(f"Downloading from: {download_url}")

    result = subprocess.run(
        ["curl", "-L", "-o", str(zip_file), download_url],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Error downloading: {result.stderr}")
        return False

    # Extract
    print(f"Extracting to: {extension_dir}")
    result = subprocess.run(
        ["unzip", "-q", str(zip_file), "-d", str(extension_dir)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Error extracting: {result.stderr}")
        return False

    print("✅ Extension downloaded and extracted successfully!")
    print(f"\nExtension location: {extension_dir}")
    print("\nNext steps:")
    print("1. Open Edge and go to: edge://extensions/")
    print("2. Enable 'Developer mode' (toggle in top-right)")
    print("3. Click 'Load unpacked'")
    print(f"4. Select: {extension_dir}")

    return True


def main():
    """Main entry point."""
    if not check_dependencies():
        print("Error: Required commands 'curl' and 'unzip' not found.")
        print("Please install them first.")
        return 1

    version = sys.argv[1] if len(sys.argv) > 1 else None

    if download_and_extract(version):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
