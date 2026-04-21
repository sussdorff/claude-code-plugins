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

# Find SKILL.md files (deduplicate by resolved path)
seen_paths=""
for base in "${default_paths[@]}"; do
    if [ -d "$base" ]; then
        while IFS= read -r f; do
            resolved="$(cd "$(dirname "$f")" && pwd -P)/$(basename "$f")"
            if ! echo "$seen_paths" | grep -qF "$resolved"; then
                seen_paths="$seen_paths
$resolved"
                skill_files+=("$f")
            fi
        done < <(find "$base" -maxdepth 2 -name "SKILL.md" -type f 2>/dev/null)
    fi
done

if [ ${#skill_files[@]} -eq 0 ]; then
    echo "No skills found in searched paths."
    echo "Searched: ${default_paths[*]}"
    exit 0
fi

# Fleet totals
total_skills=0
total_desc_chars=0
bloated=()

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

    # Accumulate fleet totals
    total_skills=$((total_skills + 1))
    total_desc_chars=$((total_desc_chars + desc_len))
    if [ "$desc_len" -gt 300 ]; then
        bloated+=("${skill_name}:${desc_len}")
    fi
done

# Fleet summary
echo ""
echo "=== Fleet System Prompt Cost ==="
echo "Total skills:            $total_skills"
echo "Total description chars: $total_desc_chars"
est_tokens=$(awk "BEGIN {printf \"%d\", $total_desc_chars / 4}")
echo "Est. description tokens: $est_tokens"
if [ "$total_skills" -gt 0 ]; then
    avg=$(awk "BEGIN {printf \"%d\", $total_desc_chars / $total_skills}")
    echo "Avg description length:  $avg chars"
fi

if [ ${#bloated[@]} -gt 0 ]; then
    echo ""
    echo "Bloated descriptions (>300 chars):"
    # Sort by char count descending
    IFS=$'\n' sorted=($(for b in "${bloated[@]}"; do
        name="${b%%:*}"
        chars="${b##*:}"
        printf "%d %s\n" "$chars" "$name"
    done | sort -rn))
    unset IFS
    for entry in "${sorted[@]}"; do
        chars="${entry%% *}"
        name="${entry#* }"
        printf "  %-25s %d chars\n" "$name" "$chars"
    done
fi
