#!/bin/bash
# init-skill.sh - Scaffold a new Claude Code skill directory
# Usage: init-skill.sh [--local] <skill-name>
#
# Creates the skill directory structure with a template SKILL.md.
#
# Default: global skill in ~/.claude/skills/ (override with SKILL_FORGE_GLOBAL_DIR)
# --local: project-specific skill in .claude/skills/

set -euo pipefail

GLOBAL_SKILLS_DIR="${SKILL_FORGE_GLOBAL_DIR:-$HOME/.claude/skills}"
LOCAL_SKILLS_DIR=".claude/skills"

# Parse flags
LOCAL=false
SKILL_NAME=""

for arg in "$@"; do
    case "$arg" in
        --local)
            LOCAL=true
            ;;
        --help|-h)
            echo "Usage: init-skill.sh [--local] <skill-name>"
            echo ""
            echo "  skill-name   Kebab-case name (e.g., code-reviewer, deploy-checker)"
            echo ""
            echo "Options:"
            echo "  --local      Create in .claude/skills/ (project-specific)"
            echo "               Default: ~/.claude/skills/ (global)"
            echo ""
            echo "Environment:"
            echo "  SKILL_FORGE_GLOBAL_DIR   Override global skills directory"
            echo "                           (default: ~/.claude/skills/)"
            echo ""
            echo "Examples:"
            echo "  init-skill.sh my-tool          # global skill"
            echo "  init-skill.sh --local my-tool   # project-specific skill"
            exit 0
            ;;
        -*)
            echo "Error: Unknown option: $arg"
            echo "Use --help for usage."
            exit 1
            ;;
        *)
            if [ -n "$SKILL_NAME" ]; then
                echo "Error: Multiple skill names given: '$SKILL_NAME' and '$arg'"
                exit 1
            fi
            SKILL_NAME="$arg"
            ;;
    esac
done

if [ -z "$SKILL_NAME" ]; then
    echo "Usage: init-skill.sh [--local] <skill-name>"
    echo ""
    echo "  --local   Create in .claude/skills/ (project-specific)"
    echo "  Default:  ~/.claude/skills/ (global)"
    exit 1
fi

# Validate kebab-case
if ! echo "$SKILL_NAME" | grep -qE '^[a-z][a-z0-9]*(-[a-z0-9]+)*$'; then
    echo "Error: Skill name must be kebab-case (lowercase letters, numbers, hyphens)."
    echo "  Valid:   code-reviewer, deploy-v2, my-skill"
    echo "  Invalid: Code_Reviewer, my--skill, -leading, trailing-"
    exit 1
fi

# Determine target directory
if [ "$LOCAL" = true ]; then
    TARGET_DIR="$LOCAL_SKILLS_DIR"
    SCOPE="project-specific"
else
    TARGET_DIR="$GLOBAL_SKILLS_DIR"
    SCOPE="global"
fi

SKILL_DIR="$TARGET_DIR/$SKILL_NAME"

if [ -d "$SKILL_DIR" ]; then
    echo "Error: Directory already exists: $SKILL_DIR"
    exit 1
fi

# Verify target parent exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Target directory does not exist: $TARGET_DIR"
    if [ "$LOCAL" = true ]; then
        echo "Hint: Are you in a project root with .claude/skills/?"
    else
        echo "Hint: Global skills dir missing. Expected: $GLOBAL_SKILLS_DIR"
    fi
    exit 1
fi

# Create structure
mkdir -p "$SKILL_DIR/references"
mkdir -p "$SKILL_DIR/scripts"

# Write SKILL.md template
cat > "$SKILL_DIR/SKILL.md" << 'TEMPLATE'
---
name: SKILL_NAME_PLACEHOLDER
description: >
  TODO: [Function verb phrase]. Use when [trigger scenario 1], [trigger scenario 2],
  or [trigger scenario 3]. Triggers on "keyword1", "keyword2", "keyword3".
  Do NOT use for [exclusion] (use [alternative] instead).
---

# SKILL_NAME_PLACEHOLDER

TODO: One-line overview of what this skill does.

## When to Use

- TODO: Scenario 1 where this skill applies
- TODO: Scenario 2
- TODO: Scenario 3

## Workflow

### 1. TODO: First Step

Description of what to do.

### 2. TODO: Second Step

Description of what to do.

## Do NOT

- TODO: Common mistake to avoid
- TODO: Out-of-scope action
- TODO: Safety boundary

## Resources

- `references/` -- TODO: describe reference files when added
- `scripts/` -- TODO: describe scripts when added
TEMPLATE

# Replace placeholder with actual name
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/SKILL_NAME_PLACEHOLDER/$SKILL_NAME/g" "$SKILL_DIR/SKILL.md"
else
    sed -i "s/SKILL_NAME_PLACEHOLDER/$SKILL_NAME/g" "$SKILL_DIR/SKILL.md"
fi

echo "Created $SCOPE skill: $SKILL_DIR/"
echo ""
echo "  $SKILL_DIR/"
echo "  ├── SKILL.md           (template -- fill in TODO markers)"
echo "  ├── references/        (add detailed docs here)"
echo "  └── scripts/           (add automation scripts here)"
echo ""
echo "Next steps:"
echo "  1. Edit $SKILL_DIR/SKILL.md -- fill in description and workflow"
echo "  2. Add reference files if needed"
echo "  3. Run skill-forge Review mode to validate quality"
echo "  4. Test with /skill-name invocation"
