#!/usr/bin/env zsh
# Install a skill from the development directory to .claude/skills/ for testing

# Reset to known ZSH defaults
emulate -LR zsh

# Enable strict error handling
setopt ERR_EXIT       # Exit on error
setopt ERR_RETURN     # Return on error in functions
setopt NO_UNSET       # Error on undefined variables
setopt PIPE_FAIL      # Fail if any command in pipeline fails

# Script metadata (read-only constants)
typeset -r SCRIPT_DIR="${0:A:h}"
typeset -r PROJECT_ROOT="${SCRIPT_DIR:h:h}"

usage() {
  cat <<EOF
Usage: $(basename "$0") <skill-name>

Install a skill from the project directory to .claude/skills/ for testing.

Arguments:
  skill-name    Name of the skill directory (e.g., jira-context-fetcher)

Examples:
  $(basename "$0") jira-context-fetcher
  $(basename "$0") screenshot-analyzer

The script will:
  1. Check if skill exists in project
  2. Check if skill already exists in .claude/skills/
  3. Copy skill files to .claude/skills/
  4. Report whether Claude restart is needed
EOF
  exit 1
}

# Check arguments
if [[ $# -ne 1 ]]; then
  usage
fi

# Parse arguments
typeset skill_name="$1"
typeset -r source_dir="${PROJECT_ROOT}/${skill_name}"
typeset -r target_dir="${PROJECT_ROOT}/.claude/skills/${skill_name}"

# Validate source exists
if [[ ! -d "$source_dir" ]]; then
  echo "❌ Error: Skill directory not found: $source_dir"
  echo ""
  echo "Available skills:"
  find "$PROJECT_ROOT" -maxdepth 1 -type d -name "*-*" ! -name ".*" -exec basename {} \; | sort
  exit 1
fi

# Check if SKILL.md exists
if [[ ! -f "${source_dir}/SKILL.md" ]]; then
  echo "❌ Error: SKILL.md not found in $source_dir"
  echo "This doesn't appear to be a valid skill directory."
  exit 1
fi

# Check if skill is new or updated
typeset skill_is_new=false
if [[ ! -d "$target_dir" ]]; then
  skill_is_new=true
  echo "📦 Installing new skill: $skill_name"
else
  echo "🔄 Updating existing skill: $skill_name"
fi

# Create target directory if needed
mkdir -p "${target_dir:h}"

# Copy skill files
echo "📋 Copying files..."
rsync -av --delete "$source_dir/" "$target_dir/"

# Report success
echo ""
echo "✅ Skill installed to: $target_dir"
echo ""

if [[ "$skill_is_new" == "true" ]]; then
  echo "⚠️  NEW SKILL DETECTED"
  echo "   Skills are loaded at Claude Code session start."
  echo "   You must EXIT and RESTART Claude Code for this skill to be available."
  echo ""
  echo "   Steps:"
  echo "   1. Exit this Claude Code session (Ctrl+D or 'exit')"
  echo "   2. Start a new session: claude"
  echo "   3. Test the skill with: \"Test ${skill_name}\""
else
  echo "ℹ️  SKILL UPDATED"
  echo "   This skill was already installed. Changes are available."
  echo "   If changes don't appear, restart Claude Code session."
fi

echo ""
echo "📍 Skill location: ${target_dir#$HOME/}"
