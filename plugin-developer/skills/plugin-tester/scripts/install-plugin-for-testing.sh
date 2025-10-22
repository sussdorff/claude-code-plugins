#!/usr/bin/env bash
# Install a plugin for local testing by copying to .claude directories
set -euo pipefail

PLUGIN_NAME="$1"

if [[ -z "$PLUGIN_NAME" ]]; then
    echo "Error: Usage: install-plugin-for-testing.sh <plugin-name>" >&2
    exit 1
fi

# Detect PROJECT_ROOT based on repository structure
# Case 1: Current directory is the plugin itself (has .claude-plugin/plugin.json)
if [[ -f ".claude-plugin/plugin.json" ]]; then
    # We're in a single plugin repository
    PROJECT_ROOT="$(pwd)"
    PLUGIN_DIR="${PROJECT_ROOT}"
    # Verify the plugin name matches
    ACTUAL_NAME=$(jq -r '.name' .claude-plugin/plugin.json)
    if [[ "$ACTUAL_NAME" != "$PLUGIN_NAME" ]]; then
        echo "Warning: Plugin name '$PLUGIN_NAME' doesn't match actual name '$ACTUAL_NAME' in plugin.json" >&2
        echo "Using actual name: $ACTUAL_NAME" >&2
        PLUGIN_NAME="$ACTUAL_NAME"
    fi
# Case 2: Marketplace/multi-plugin repository (plugin is a subdirectory)
else
    PROJECT_ROOT="$(pwd)"
    PLUGIN_DIR="${PROJECT_ROOT}/${PLUGIN_NAME}"
fi

# Validation
if [[ ! -d "$PLUGIN_DIR" ]]; then
    echo "Error: Plugin directory not found: $PLUGIN_DIR" >&2
    exit 1
fi

if [[ ! -f "${PLUGIN_DIR}/.claude-plugin/plugin.json" ]]; then
    echo "Error: Plugin metadata not found: ${PLUGIN_DIR}/.claude-plugin/plugin.json" >&2
    echo "This doesn't appear to be a valid plugin." >&2
    exit 1
fi

# Read plugin metadata
PLUGIN_VERSION=$(jq -r '.version' "${PLUGIN_DIR}/.claude-plugin/plugin.json")
PLUGIN_DESC=$(jq -r '.description' "${PLUGIN_DIR}/.claude-plugin/plugin.json")

echo "📦 Installing plugin: ${PLUGIN_NAME} (v${PLUGIN_VERSION})"
echo "   ${PLUGIN_DESC}"
echo ""

# Track what was installed
INSTALLED_COMMANDS=false
INSTALLED_SKILLS=false
COMMANDS_COUNT=0
SKILLS_COUNT=0

# Install commands to .claude/commands/
if [[ -d "${PLUGIN_DIR}/commands" ]]; then
    COMMANDS_DIR="${PROJECT_ROOT}/.claude/commands"
    mkdir -p "$COMMANDS_DIR"

    # Copy all command files
    if compgen -G "${PLUGIN_DIR}/commands/*.md" > /dev/null; then
        echo "📋 Installing commands..."
        for cmd_file in "${PLUGIN_DIR}/commands/"*.md; do
            cmd_basename=$(basename "$cmd_file")
            cp "$cmd_file" "${COMMANDS_DIR}/${cmd_basename}"
            echo "   ✓ $(basename "$cmd_file" .md)"
            ((COMMANDS_COUNT++))
        done
        INSTALLED_COMMANDS=true
        echo ""
    fi
fi

# Install skills to .claude/skills/
if [[ -d "${PLUGIN_DIR}/skills" ]]; then
    SKILLS_DIR="${PROJECT_ROOT}/.claude/skills"
    mkdir -p "$SKILLS_DIR"

    echo "🧠 Installing skills..."
    # Copy each skill directory
    for skill_dir in "${PLUGIN_DIR}/skills/"*/; do
        if [[ -d "$skill_dir" ]]; then
            skill_name=$(basename "$skill_dir")

            # Check if new or update
            if [[ -d "${SKILLS_DIR}/${skill_name}" ]]; then
                echo "   🔄 Updating: ${skill_name}"
            else
                echo "   ✨ New: ${skill_name}"
            fi

            # Copy skill directory
            rsync -a --delete "${skill_dir}" "${SKILLS_DIR}/${skill_name}/"
            ((SKILLS_COUNT++))
        fi
    done
    INSTALLED_SKILLS=true
    echo ""
fi

# Summary
echo "✅ Plugin installed successfully"
echo ""
echo "📊 Summary:"
if [[ "$INSTALLED_COMMANDS" == "true" ]]; then
    echo "   Commands: ${COMMANDS_COUNT} installed to .claude/commands/"
fi
if [[ "$INSTALLED_SKILLS" == "true" ]]; then
    echo "   Skills: ${SKILLS_COUNT} installed to .claude/skills/"
fi
echo ""

# Next steps guidance
if [[ "$INSTALLED_COMMANDS" == "true" ]] || [[ "$INSTALLED_SKILLS" == "true" ]]; then
    echo "⚠️  RESTART REQUIRED"
    echo "   Commands and skills are loaded at Claude Code startup."
    echo ""
    echo "   Steps:"
    echo "   1. Exit this Claude Code session: exit"
    echo "   2. Start a new session: claude"
    if [[ "$INSTALLED_COMMANDS" == "true" ]]; then
        echo "   3. Test commands: /<command-name>"
    fi
    if [[ "$INSTALLED_SKILLS" == "true" ]]; then
        echo "   3. Skills will be auto-invoked based on their descriptions"
    fi
    echo ""
fi

echo "📍 Plugin source: ${PLUGIN_DIR}"
echo "📍 Commands: ${PROJECT_ROOT}/.claude/commands/"
echo "📍 Skills: ${PROJECT_ROOT}/.claude/skills/"
