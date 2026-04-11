#!/bin/bash
# scan-brands.sh - List all brand profiles with metadata
# Usage: scan-brands.sh [--verbose]
#
# Scans ~/.claude/brands/ (global) and .claude/brands/ (project)
# Outputs a table of brand names, types, and descriptions.

set -euo pipefail

GLOBAL_BRANDS_DIR="$HOME/.claude/brands"
LOCAL_BRANDS_DIR=".claude/brands"
VERBOSE=false

for arg in "$@"; do
    case "$arg" in
        --verbose|-v) VERBOSE=true ;;
        --help|-h)
            echo "Usage: scan-brands.sh [--verbose]"
            echo ""
            echo "Lists all brand profiles from global (~/.claude/brands/) and"
            echo "project (.claude/brands/) directories."
            echo ""
            echo "Options:"
            echo "  --verbose, -v   Show additional details (tags, inherits, word count)"
            exit 0
            ;;
    esac
done

# Extract frontmatter field from a file
extract_field() {
    local file="$1" field="$2"
    sed -n '/^---$/,/^---$/p' "$file" | grep "^${field}:" | head -1 | sed "s/^${field}: *//; s/^\"//; s/\"$//" || true
}

found=0

scan_dir() {
    local dir="$1" scope="$2"
    if [ ! -d "$dir" ]; then return; fi

    for file in "$dir"/*.md; do
        [ -f "$file" ] || continue
        found=$((found + 1))

        name=$(extract_field "$file" "name")
        type=$(extract_field "$file" "type")
        desc=$(extract_field "$file" "description")
        inherits=$(extract_field "$file" "inherits")
        words=$(wc -w < "$file" | tr -d ' ')
        tokens=$((words * 13 / 10))

        # Truncate description
        if [ ${#desc} -gt 60 ]; then
            desc="${desc:0:57}..."
        fi

        if [ "$VERBOSE" = true ]; then
            printf "%-25s %-10s %-8s %4d tok  %-15s %s\n" \
                "${name:-$(basename "$file" .md)}" "$type" "$scope" "$tokens" \
                "${inherits:---}" "$desc"
        else
            printf "%-25s %-10s %-8s %s\n" \
                "${name:-$(basename "$file" .md)}" "$type" "$scope" "$desc"
        fi
    done
}

if [ "$VERBOSE" = true ]; then
    printf "%-25s %-10s %-8s %8s  %-15s %s\n" "NAME" "TYPE" "SCOPE" "SIZE" "INHERITS" "DESCRIPTION"
    printf "%-25s %-10s %-8s %8s  %-15s %s\n" "----" "----" "-----" "----" "--------" "-----------"
else
    printf "%-25s %-10s %-8s %s\n" "NAME" "TYPE" "SCOPE" "DESCRIPTION"
    printf "%-25s %-10s %-8s %s\n" "----" "----" "-----" "-----------"
fi

scan_dir "$GLOBAL_BRANDS_DIR" "global"
scan_dir "$LOCAL_BRANDS_DIR" "project"

if [ "$found" -eq 0 ]; then
    echo "(no brands found)"
    echo ""
    echo "Create one with: init-brand.sh <brand-name>"
fi
