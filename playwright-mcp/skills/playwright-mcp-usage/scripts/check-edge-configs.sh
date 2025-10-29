#!/bin/bash
# Check which directories have Playwright MCP configured with Edge

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "Searching for Playwright MCP configurations with Edge..."
echo ""

# Use jq to extract directories with playwright configured with msedge
jq -r '
  .projects
  | to_entries[]
  | select(.value.mcpServers.playwright?)
  | select(.value.mcpServers.playwright.args | any(contains("edge")))
  | .key
' ~/.claude.json 2>/dev/null | while read -r path; do
  echo -e "${GREEN}✓${NC} ${BLUE}${path}${NC}"
done

# Count total
count=$(jq -r '
  .projects
  | to_entries[]
  | select(.value.mcpServers.playwright?)
  | select(.value.mcpServers.playwright.args | any(contains("edge")))
  | .key
' ~/.claude.json 2>/dev/null | wc -l | tr -d ' ')

echo ""
echo "Found ${count} directories with Playwright MCP configured for Edge"
