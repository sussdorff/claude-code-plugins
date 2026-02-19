#!/bin/bash
# scan-skills.sh - Discover and measure Claude Code skills
# Usage: scan-skills.sh [additional-paths...]
#
# Scans default skill locations and any additional paths provided.
# Outputs a table with skill metrics for audit mode.

set -euo pipefail

# Collect skill directories
skill_files=()

# Default search locations
default_paths=(
    "$HOME/.claude/skills"
    ".claude/skills"
)

# Add argument paths
for arg in "$@"; do
    default_paths+=("$arg")
done

# Find SKILL.md files
for base in "${default_paths[@]}"; do
    if [ -d "$base" ]; then
        while IFS= read -r f; do
            skill_files+=("$f")
        done < <(find "$base" -maxdepth 2 -name "SKILL.md" -type f 2>/dev/null)
    fi
done

if [ ${#skill_files[@]} -eq 0 ]; then
    echo "No skills found in searched paths."
    echo "Searched: ${default_paths[*]}"
    exit 0
fi

# Print header
printf "%-25s %6s %8s %5s %7s %5s\n" "SKILL" "LINES" "TOKENS~" "REFS" "SCRIPTS" "DESC"
printf "%-25s %6s %8s %5s %7s %5s\n" "-------------------------" "------" "--------" "-----" "-------" "-----"

for skill_file in "${skill_files[@]}"; do
    skill_dir="$(dirname "$skill_file")"
    skill_name="$(basename "$skill_dir")"

    # Line count
    lines=$(wc -l < "$skill_file" | tr -d ' ')

    # Word count and estimated tokens
    words=$(wc -w < "$skill_file" | tr -d ' ')
    tokens=$(awk "BEGIN {printf \"%d\", $words * 1.3}")

    # Has references/
    if [ -d "$skill_dir/references" ]; then
        has_refs="yes"
    else
        has_refs="no"
    fi

    # Has scripts/
    if [ -d "$skill_dir/scripts" ]; then
        has_scripts="yes"
    else
        has_scripts="no"
    fi

    # Description length from frontmatter
    desc_len=0
    if command -v awk >/dev/null 2>&1; then
        desc=$(awk '/^---$/{n++; next} n==1 && /^description:/{found=1; sub(/^description:[[:space:]]*>?[[:space:]]*/, ""); if(length($0)>0) buf=$0; next} n==1 && found && /^[[:space:]]/{sub(/^[[:space:]]+/, ""); buf=buf " " $0; next} found{found=0} n==2{exit} END{print buf}' "$skill_file")
        desc_len=${#desc}
    fi

    printf "%-25s %6d %8d %5s %7s %5d\n" "$skill_name" "$lines" "$tokens" "$has_refs" "$has_scripts" "$desc_len"
done
