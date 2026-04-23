#!/bin/bash
# init-brand.sh - Scaffold a new brand profile
# Usage: init-brand.sh [--local] [--type=voice|visual|combined] <brand-name>
#
# Creates a brand profile from template.
#
# Default: global brand in ~/.claude/brands/
# --local: project-specific brand in .claude/brands/

set -euo pipefail

GLOBAL_BRANDS_DIR="$HOME/.claude/brands"
LOCAL_BRANDS_DIR=".claude/brands"

# Defaults
LOCAL=false
BRAND_TYPE="voice"
BRAND_NAME=""

for arg in "$@"; do
    case "$arg" in
        --local)
            LOCAL=true
            ;;
        --type=*)
            BRAND_TYPE="${arg#--type=}"
            if [[ ! "$BRAND_TYPE" =~ ^(voice|visual|combined)$ ]]; then
                echo "Error: Type must be voice, visual, or combined."
                exit 1
            fi
            ;;
        --help|-h)
            echo "Usage: init-brand.sh [--local] [--type=voice|visual|combined] <brand-name>"
            echo ""
            echo "  brand-name   Kebab-case name (e.g., malte-professional, cognovis-proposals)"
            echo ""
            echo "Options:"
            echo "  --local              Create in .claude/brands/ (project-specific)"
            echo "                       Default: ~/.claude/brands/ (global)"
            echo "  --type=TYPE          voice (default), visual, or combined"
            echo ""
            echo "Examples:"
            echo "  init-brand.sh malte-professional"
            echo "  init-brand.sh --type=combined --local project-brand"
            exit 0
            ;;
        -*)
            echo "Error: Unknown option: $arg"
            echo "Use --help for usage."
            exit 1
            ;;
        *)
            if [ -n "$BRAND_NAME" ]; then
                echo "Error: Multiple brand names given: '$BRAND_NAME' and '$arg'"
                exit 1
            fi
            BRAND_NAME="$arg"
            ;;
    esac
done

if [ -z "$BRAND_NAME" ]; then
    echo "Usage: init-brand.sh [--local] [--type=voice|visual|combined] <brand-name>"
    exit 1
fi

# Validate kebab-case
if ! echo "$BRAND_NAME" | grep -qE '^[a-z][a-z0-9]*(-[a-z0-9]+)*$'; then
    echo "Error: Brand name must be kebab-case (lowercase letters, numbers, hyphens)."
    echo "  Valid:   malte-professional, cognovis-v2, my-brand"
    echo "  Invalid: My_Brand, my--brand, -leading, trailing-"
    exit 1
fi

# Determine target directory
if [ "$LOCAL" = true ]; then
    TARGET_DIR="$LOCAL_BRANDS_DIR"
    SCOPE="project-specific"
else
    TARGET_DIR="$GLOBAL_BRANDS_DIR"
    SCOPE="global"
fi

BRAND_FILE="$TARGET_DIR/$BRAND_NAME.md"

if [ -f "$BRAND_FILE" ]; then
    echo "Error: Brand already exists: $BRAND_FILE"
    exit 1
fi

# Create directory if needed
mkdir -p "$TARGET_DIR"

# Write template based on type
cat > "$BRAND_FILE" << TEMPLATE
---
name: $BRAND_NAME
type: $BRAND_TYPE
description: "TODO: 1-2 sentences describing this brand's purpose"
# inherits: parent-brand-name
version: 1
tags: []
---

# $BRAND_NAME

TODO: Brief overview of this brand identity.

TEMPLATE

# Add voice sections
if [[ "$BRAND_TYPE" == "voice" || "$BRAND_TYPE" == "combined" ]]; then
    cat >> "$BRAND_FILE" << 'VOICE'
## Voice Profile

### Tone & Register
- TODO: Formality level (du/Sie, casual/formal)
- TODO: Emotional register (warm, neutral, authoritative)
- TODO: Perspective (solution-oriented, analytical, empathetic)

### Vocabulary
#### Prefer
- TODO: "Term A" over "Term B" — reason

#### Avoid
- TODO: Term to avoid — use alternative instead

### Writing Rules
- TODO: Sentence structure preferences
- TODO: Paragraph length guidelines

### Examples

<example-good>
TODO: Example text that follows this brand's voice.
</example-good>

<example-bad>
TODO: Same content written poorly — violating the brand's rules.
</example-bad>

VOICE
fi

# Add visual sections
if [[ "$BRAND_TYPE" == "visual" || "$BRAND_TYPE" == "combined" ]]; then
    cat >> "$BRAND_FILE" << 'VISUAL'
## Visual Profile

### Colors
- TODO: Primary color (hex)
- TODO: Secondary color (hex)
- TODO: Accent color (hex)

### Typography
- TODO: Font families, sizes, weights

### Logo Rules
- TODO: Placement, minimum size, clear space

### Spacing
- TODO: Margins, padding conventions
VISUAL
fi

echo "Created $SCOPE brand: $BRAND_FILE"
echo ""
echo "Next steps:"
echo "  1. Edit $BRAND_FILE — fill in TODO markers"
echo "  2. Run brand-forge Review mode to validate quality"
echo "  3. Reference from skills with: <!-- brand: $BRAND_NAME -->"
