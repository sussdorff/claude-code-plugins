#!/bin/bash
# Install Playwright MCP Bridge Extension for Edge and configure Claude Code
# Smart detection: checks if already installed, reuses tokens from other projects

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

CURRENT_DIR="$(pwd)"
CLAUDE_CONFIG="$HOME/.claude.json"
CLAUDE_CMD="${HOME}/.claude/local/claude"

echo -e "${BLUE}=== Playwright MCP + Edge Setup ===${NC}"
echo ""

# Step 0: Check if already configured for this project
echo -e "${BLUE}[0/6]${NC} Checking current project configuration..."
CURRENT_CONFIG=$(jq -r ".projects.\"$CURRENT_DIR\".mcpServers.playwright?" "$CLAUDE_CONFIG" 2>/dev/null || echo "null")

if [ "$CURRENT_CONFIG" != "null" ]; then
  # Check if it's properly configured with Edge and token
  BROWSER_ARG=$(echo "$CURRENT_CONFIG" | jq -r '.args[]? | select(. == "--browser=msedge")' 2>/dev/null || echo "")
  TOKEN=$(echo "$CURRENT_CONFIG" | jq -r '.env.PLAYWRIGHT_MCP_EXTENSION_TOKEN? // empty' 2>/dev/null || echo "")

  if [ -n "$BROWSER_ARG" ] && [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓${NC} Playwright MCP is already properly configured for this project"
    echo ""
    echo "Configuration details:"
    echo "$CURRENT_CONFIG" | jq '.'
    echo ""
    echo -e "${GREEN}You're all set! The MCP server is ready to use.${NC}"
    exit 0
  elif [ -z "$BROWSER_ARG" ]; then
    echo -e "${YELLOW}⚠${NC} Playwright MCP is configured but not using Edge browser"
    echo "   Will reconfigure with Edge support..."
  elif [ -z "$TOKEN" ]; then
    echo -e "${YELLOW}⚠${NC} Playwright MCP is configured but missing extension token"
    echo "   Will add token from another project or prompt for manual setup..."
  fi
else
  echo -e "${YELLOW}⚠${NC} Playwright MCP not configured for this project"
fi
echo ""

# Step 1: Find existing tokens from other projects
echo -e "${BLUE}[1/6]${NC} Searching for existing Playwright MCP configurations..."
EXISTING_TOKENS=$(jq -r '
  .projects
  | to_entries[]
  | select(.value.mcpServers.playwright?.env.PLAYWRIGHT_MCP_EXTENSION_TOKEN?)
  | {path: .key, token: .value.mcpServers.playwright.env.PLAYWRIGHT_MCP_EXTENSION_TOKEN}
  | @json
' "$CLAUDE_CONFIG" 2>/dev/null || echo "")

if [ -z "$EXISTING_TOKENS" ]; then
  echo -e "${YELLOW}⚠${NC} No existing tokens found in other projects"
  REUSE_TOKEN=""
else
  echo -e "${GREEN}✓${NC} Found existing token(s) in other projects"
  echo ""

  # Find most recently active project
  echo "Determining most recent project..."
  BEST_PROJECT=""
  BEST_DATE=""
  BEST_TOKEN=""

  while IFS= read -r config; do
    if [ -z "$config" ]; then continue; fi

    PROJECT_PATH=$(echo "$config" | jq -r '.path')
    PROJECT_TOKEN=$(echo "$config" | jq -r '.token')

    # Check if it's a git repo
    if [ -d "$PROJECT_PATH/.git" ]; then
      LAST_DATE=$(cd "$PROJECT_PATH" && git log -1 --format="%ai" 2>/dev/null || echo "1970-01-01 00:00:00 +0000")
    else
      # Use most recent file modification in directory
      LAST_DATE=$(find "$PROJECT_PATH" -type f -exec stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S +0000" {} \; 2>/dev/null | sort -r | head -1 || echo "1970-01-01 00:00:00 +0000")
    fi

    # Compare dates (simple string comparison works for ISO format)
    if [ -z "$BEST_DATE" ] || [[ "$LAST_DATE" > "$BEST_DATE" ]]; then
      BEST_DATE="$LAST_DATE"
      BEST_PROJECT="$PROJECT_PATH"
      BEST_TOKEN="$PROJECT_TOKEN"
    fi
  done <<< "$EXISTING_TOKENS"

  if [ -n "$BEST_TOKEN" ]; then
    echo -e "${GREEN}✓${NC} Most recent project: $BEST_PROJECT"
    echo "   Last activity: $BEST_DATE"
    echo "   Will reuse token from this project"
    REUSE_TOKEN="$BEST_TOKEN"
  fi
fi
echo ""

# Step 2: Check if Edge is installed
echo -e "${BLUE}[2/6]${NC} Checking for Microsoft Edge..."
if [ -d "/Applications/Microsoft Edge.app" ]; then
  echo -e "${GREEN}✓${NC} Microsoft Edge is installed"
else
  echo -e "${YELLOW}⚠${NC} Microsoft Edge not found"
  echo "Install with: brew install --cask microsoft-edge"
  echo "Or download from: https://www.microsoft.com/edge/download"
  exit 1
fi
echo ""

# Step 3: Check if extension is installed (if we have a token to test)
if [ -n "$REUSE_TOKEN" ]; then
  echo -e "${BLUE}[3/6]${NC} Extension appears to be installed (found existing token)"
  echo "   Skipping extension download..."
  SKIP_EXTENSION_INSTALL=true
else
  echo -e "${BLUE}[3/6]${NC} Checking for Playwright MCP Bridge Extension..."

  # Check if extension already exists in /tmp
  if [ -d "/tmp/playwright-mcp-extension" ]; then
    echo -e "${GREEN}✓${NC} Extension found at: /tmp/playwright-mcp-extension"
    echo "   Skipping download..."
    SKIP_EXTENSION_INSTALL=false
  else
    echo "Downloading Playwright MCP Bridge Extension..."
    cd /tmp

    # Download extension
    curl -L -o playwright-mcp-extension.zip "https://github.com/microsoft/playwright-mcp/releases/latest/download/playwright-mcp-extension-0.0.43.zip"

    # Check if download was successful and file is valid
    if [ ! -f "playwright-mcp-extension.zip" ] || [ ! -s "playwright-mcp-extension.zip" ]; then
      echo -e "${RED}✗${NC} Download failed or file is empty"
      exit 1
    fi

    # Try to unzip
    if ! unzip -q playwright-mcp-extension.zip -d playwright-mcp-extension 2>/dev/null; then
      echo -e "${RED}✗${NC} Failed to extract extension (file may be corrupted)"
      echo "Please download manually from: https://github.com/microsoft/playwright-mcp/releases"
      exit 1
    fi

    echo -e "${GREEN}✓${NC} Extension downloaded to: /tmp/playwright-mcp-extension"
    SKIP_EXTENSION_INSTALL=false
  fi
fi
echo ""

# Step 4: Get token (reuse or prompt)
if [ -n "$REUSE_TOKEN" ]; then
  echo -e "${BLUE}[4/6]${NC} Using token from existing project"
  TOKEN="$REUSE_TOKEN"
elif [ "$SKIP_EXTENSION_INSTALL" = true ]; then
  # This shouldn't happen, but handle it
  echo -e "${RED}✗${NC} No token available and extension not installed"
  exit 1
else
  # Need to install extension and get token manually
  echo -e "${BLUE}[4/6]${NC} Load Extension in Edge"
  echo -e "${YELLOW}Manual steps required:${NC}"
  echo "1. Open Edge and navigate to: edge://extensions/"
  echo "2. Enable 'Developer mode' (toggle in top-right)"
  echo "3. Click 'Load unpacked'"
  echo "4. Select directory: /tmp/playwright-mcp-extension"
  echo "5. Verify 'Playwright MCP Bridge' appears in extensions list"
  echo ""
  read -p "Press Enter when you've completed these steps..."
  echo ""

  echo -e "${BLUE}Get Extension Token${NC}"
  echo -e "${YELLOW}Manual steps required:${NC}"
  echo "1. In Edge, go to: edge://extensions/"
  echo "2. Find 'Playwright MCP Bridge'"
  echo "3. Click 'status.html' under 'Inspect views'"
  echo "4. Copy the token from PLAYWRIGHT_MCP_EXTENSION_TOKEN field"
  echo ""
  read -p "Paste your token here: " TOKEN
  echo ""

  if [ -z "$TOKEN" ]; then
    echo -e "${RED}✗${NC} No token provided. Exiting."
    exit 1
  fi
fi
echo ""

# Step 5: Configuration options
echo -e "${BLUE}[5/6]${NC} Configuration Options"
echo ""

# Ask about headless mode
read -p "Enable headless mode (browser runs without visible window)? [y/N]: " HEADLESS
HEADLESS=${HEADLESS:-n}

# Ask about storage state
read -p "Specify storage state file path for session persistence? [leave empty for default]: " STORAGE_STATE

# Build args array
ARGS="[\"@playwright/mcp@latest\",\"--browser=msedge\",\"--extension\""

if [[ "$HEADLESS" =~ ^[Yy]$ ]]; then
  ARGS="${ARGS},\"--headless\""
  echo -e "${GREEN}✓${NC} Headless mode enabled"
fi

if [ -n "$STORAGE_STATE" ]; then
  ARGS="${ARGS},\"--storage-state=$STORAGE_STATE\""
  echo -e "${GREEN}✓${NC} Storage state: $STORAGE_STATE"
fi

ARGS="${ARGS}]"
echo ""

# Step 6: Configure Claude Code MCP server
echo -e "${BLUE}[6/6]${NC} Configuring Claude Code..."

# Remove existing config if present
if "$CLAUDE_CMD" mcp list 2>/dev/null | grep -q playwright; then
  echo "Removing existing playwright configuration..."
  "$CLAUDE_CMD" mcp remove playwright >/dev/null 2>&1 || true
fi

"$CLAUDE_CMD" mcp add-json "playwright" "{\"command\":\"npx\",\"args\":${ARGS},\"env\":{\"PLAYWRIGHT_MCP_EXTENSION_TOKEN\":\"${TOKEN}\"}}"
echo -e "${GREEN}✓${NC} Claude Code MCP server configured"
echo ""

# Verify installation
echo -e "${BLUE}Verifying installation...${NC}"
if "$CLAUDE_CMD" mcp list | grep -q playwright; then
  echo -e "${GREEN}✓${NC} Playwright MCP server verified"
else
  echo -e "${YELLOW}⚠${NC} Verification failed - please check manually with: $CLAUDE_CMD mcp list"
fi
echo ""

echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo "Next steps:"
echo "1. ${YELLOW}IMPORTANT: Restart Claude Code${NC}"
echo "2. Test with: 'Navigate to https://example.com'"
echo ""
if [ "$SKIP_EXTENSION_INSTALL" != true ]; then
  echo -e "${YELLOW}Note:${NC} Extension location is /tmp/playwright-mcp-extension"
  echo "      Consider moving it to a permanent location if needed"
  echo ""
fi
