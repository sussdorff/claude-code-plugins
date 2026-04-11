#!/usr/bin/env bash
# entropy-scan.sh — Validate Claude harness invariants
#
# Exit codes:
#   0 = no violations found (harness is healthy)
#   1 = violations found (harness needs attention)
#   2 = error running checks (e.g. permission errors)
#
# Usage:
#   entropy-scan.sh [--dir <path>]
#
# Default directory is current working directory.

set -euo pipefail

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
SCAN_DIR="."
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dir)
            SCAN_DIR="${2:?--dir requires a path argument}"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

cd "$SCAN_DIR"

violations=()

# ---------------------------------------------------------------------------
# 1. Skills (SKILL-01 through SKILL-05)
# ---------------------------------------------------------------------------

# SKILL-01: Every skill directory must have SKILL.md
if [[ -d malte/skills ]]; then
    while read -r dir; do
        if [[ ! -f "$dir/SKILL.md" ]]; then
            violations+=("VIOLATION [SKILL-01]: $dir — SKILL.md missing — FIX: Create $dir/SKILL.md with required frontmatter (name: and description:)")
        fi
    done < <(find malte/skills -maxdepth 1 -mindepth 1 -type d 2>/dev/null)
fi

# SKILL-02: Every SKILL.md must have name (kebab-case) and description (150-300 chars)
shopt -s nullglob
for file in malte/skills/*/SKILL.md; do
    [[ -f "$file" ]] || continue

    # Check for 'name:' field
    if ! grep -q "^name:" "$file"; then
        violations+=("VIOLATION [SKILL-02]: $file — Missing 'name:' field in frontmatter — FIX: Add 'name: <kebab-case-name>' to frontmatter")
    fi

    # Check for 'description:' field and character count
    if ! grep -q "^description:" "$file"; then
        violations+=("VIOLATION [SKILL-02]: $file — Missing 'description:' field in frontmatter — FIX: Add 'description: >- <150-300 char text>' to frontmatter")
    else
        # Extract description value(s): multi-line folded scalar or inline
        # Grab lines from 'description:' up to (not including) the next top-level key
        # Count actual characters (fold newlines to single space, don't strip spaces)
        desc_text=$(awk '
          /^---$/ { if (in_fm) exit; in_fm=1; next }
          in_fm && /^description:/ { found=1; sub(/^description:[[:space:]]*(>-[[:space:]]*)?/,""); print; next }
          in_fm && found && /^[a-zA-Z][a-zA-Z0-9_-]*:/ { found=0 }
          in_fm && found { print }
        ' "$file" | tr '\n' ' ' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
        desc_len=${#desc_text}
        if [[ $desc_len -lt 150 || $desc_len -gt 300 ]]; then
            violations+=("VIOLATION [SKILL-02]: $file — Description is $desc_len chars (must be 150-300) — FIX: Adjust description text to 150-300 characters (excluding YAML formatting)")
        fi
    fi
done

# SKILL-03: Required sections must exist and be in prescribed order
for file in malte/skills/*/SKILL.md; do
    [[ -f "$file" ]] || continue

    overview_line=$(grep -n "^## Overview" "$file" | cut -d: -f1 | head -1 || true)
    when_line=$(grep -n "^## When to Use" "$file" | cut -d: -f1 | head -1 || true)

    # Flag missing required sections
    if [[ -z "$overview_line" ]]; then
        violations+=("VIOLATION [SKILL-03]: $file — Missing '## Overview' section — FIX: Add '## Overview' section before '## When to Use'")
    fi
    if [[ -z "$when_line" ]]; then
        violations+=("VIOLATION [SKILL-03]: $file — Missing '## When to Use' section — FIX: Add '## When to Use' section after '## Overview'")
    fi

    # If both exist, verify order
    if [[ -n "$overview_line" && -n "$when_line" ]] && [[ $overview_line -gt $when_line ]]; then
        violations+=("VIOLATION [SKILL-03]: $file — Section order wrong (Overview after 'When to Use') — FIX: Reorder: Overview must come before 'When to Use'")
    fi

    resources_line=$(grep -n "^## Resources" "$file" | cut -d: -f1 | head -1 || true)
    scope_line=$(grep -n "^## Out of Scope" "$file" | cut -d: -f1 | head -1 || true)
    if [[ -n "$resources_line" && -n "$scope_line" ]] && [[ $resources_line -gt $scope_line ]]; then
        violations+=("VIOLATION [SKILL-03]: $file — Section order wrong (Resources after 'Out of Scope') — FIX: Reorder: Resources must come before 'Out of Scope'")
    fi
done

# SKILL-04: Skill files should not exceed 500 lines
for file in malte/skills/*/SKILL.md; do
    [[ -f "$file" ]] || continue
    line_count=$(wc -l < "$file")
    if [[ $line_count -gt 500 ]]; then
        violations+=("VIOLATION [SKILL-04]: $file — $line_count lines (max 500) — FIX: Move detailed workflows to references/ or split into separate skills")
    fi
done

# SKILL-05: Each skill directory may only contain known file types
for dir in malte/skills/*/; do
    [[ -d "$dir" ]] || continue
    for file in "$dir"*; do
        [[ -f "$file" ]] || continue
        base=$(basename "$file")
        case "$base" in
            SKILL.md|*.md|*.yml|*.yaml|*.sh|*.py|*.json) ;;
            *)
                violations+=("VIOLATION [SKILL-05]: $file — Unexpected file type in skill directory — FIX: Remove or move '$base' outside the skill directory")
                ;;
        esac
    done
done

shopt -u nullglob

# ---------------------------------------------------------------------------
# 2. Hooks (HOOK-01 through HOOK-04)
# ---------------------------------------------------------------------------

# Collect all hook files
hook_files=()
shopt -s nullglob
for f in .claude/hooks/*.sh .claude/hooks/*.py default/hooks/*.sh default/hooks/*.py; do
    [[ -f "$f" ]] && hook_files+=("$f")
done
shopt -u nullglob

# HOOK-01: Every hook must document exit codes in comments
for file in "${hook_files[@]}"; do
    # Check for an exit-code comment block (look for both exit 0 and exit 2 documentation)
    has_exit0_comment=false
    has_exit2_comment=false
    # Match comment lines that reference exit codes (only on lines starting with #)
    # Require literal comment lines: "# exit 0" or "# 0 = allow" style
    if grep -qE '^\s*#\s*(exit\s+0|0\s*=\s*allow|0 - allow|exit code.*0)' "$file"; then
        has_exit0_comment=true
    fi
    if grep -qE '^\s*#\s*(exit\s+2|2\s*=\s*deny|2 - deny|exit code.*2)' "$file"; then
        has_exit2_comment=true
    fi
    if [[ "$has_exit0_comment" == false || "$has_exit2_comment" == false ]]; then
        violations+=("VIOLATION [HOOK-01]: $file — Missing exit-code comment block — FIX: Add comment block documenting exit codes (# exit 0 = allow, # exit 2 = deny)")
    fi
done

# HOOK-02: Bash hooks must have 'set -euo pipefail'; Python hooks must have try/except
shopt -s nullglob
for file in .claude/hooks/*.sh default/hooks/*.sh; do
    [[ -f "$file" ]] || continue
    if ! grep -q "set -euo pipefail" "$file"; then
        violations+=("VIOLATION [HOOK-02]: $file — Missing error handling — FIX: Add 'set -euo pipefail' after the shebang line")
    fi
done
for file in .claude/hooks/*.py default/hooks/*.py; do
    [[ -f "$file" ]] || continue
    if ! grep -q "try:" "$file" || ! grep -q "except" "$file"; then
        violations+=("VIOLATION [HOOK-02]: $file — Missing try/except error handling — FIX: Wrap main logic in try/except to handle errors gracefully")
    fi
done
shopt -u nullglob

# HOOK-03: Bash hooks must read stdin using INPUT=$(cat) pattern; Python hooks should read sys.stdin
shopt -s nullglob
for file in .claude/hooks/*.sh default/hooks/*.sh; do
    [[ -f "$file" ]] || continue
    if grep -qE 'INPUT=\$\(cat\)|while.*IFS.*read' "$file"; then
        if ! grep -qF 'INPUT=$(cat)' "$file"; then
            violations+=("VIOLATION [HOOK-03]: $file — Non-standard stdin pattern — FIX: Use 'INPUT=\$(cat)' to read stdin safely")
        fi
    fi
done
for file in .claude/hooks/*.py default/hooks/*.py; do
    [[ -f "$file" ]] || continue
    # Python hooks that appear to read input but don't use sys.stdin.read()
    if grep -q "stdin\|input()" "$file"; then
        if ! grep -qE "sys\.stdin\.read\(\)|json\.load\(sys\.stdin\)" "$file"; then
            violations+=("VIOLATION [HOOK-03]: $file — Non-standard stdin pattern in Python hook — FIX: Use 'sys.stdin.read()' or 'json.load(sys.stdin)' to read stdin")
        fi
    fi
done
shopt -u nullglob

# HOOK-04: Hooks must return appropriate exit codes (0, 2, or 1)
shopt -s nullglob
for file in .claude/hooks/*.sh default/hooks/*.sh; do
    [[ -f "$file" ]] || continue
    if ! grep -qE "exit [012]" "$file"; then
        violations+=("VIOLATION [HOOK-04]: $file — No explicit exit codes found — FIX: Ensure hook exits with 0 (allow), 2 (deny), or 1 (error)")
    fi
done
for file in .claude/hooks/*.py default/hooks/*.py; do
    [[ -f "$file" ]] || continue
    if ! grep -qE "sys\.exit\(0\)|sys\.exit\(1\)|sys\.exit\(2\)" "$file"; then
        violations+=("VIOLATION [HOOK-04]: $file — No explicit sys.exit() calls found — FIX: Use sys.exit(0) (allow), sys.exit(2) (deny), or sys.exit(1) (error)")
    fi
done
shopt -u nullglob

# ---------------------------------------------------------------------------
# 3. Agents (AGENT-01 through AGENT-04)
# ---------------------------------------------------------------------------

# AGENT-01: Every agent directory must have agent.yml
shopt -s nullglob
for base_dir in .claude/agents default/agents; do
    [[ -d "$base_dir" ]] || continue
    while read -r dir; do
        if [[ ! -f "$dir/agent.yml" ]]; then
            violations+=("VIOLATION [AGENT-01]: $dir — agent.yml missing — FIX: Create $dir/agent.yml with required fields (name, description, tools)")
        fi
    done < <(find "$base_dir" -maxdepth 1 -mindepth 1 -type d 2>/dev/null)
done
shopt -u nullglob

# AGENT-02: agent.yml must have name, description (<=300 chars), and tools fields
shopt -s nullglob
for file in .claude/agents/*/agent.yml default/agents/*/agent.yml; do
    [[ -f "$file" ]] || continue

    if ! grep -q "^name:" "$file"; then
        violations+=("VIOLATION [AGENT-02]: $file — Missing 'name:' field — FIX: Add 'name: <agent-name>' field")
    fi

    if ! grep -q "^description:" "$file"; then
        violations+=("VIOLATION [AGENT-02]: $file — Missing 'description:' field — FIX: Add 'description: <text>' field (1-2 sentences, <=300 chars)")
    else
        # Check description length
        desc_text=$(awk '
          /^---$/ { if (in_fm) exit; in_fm=1; next }
          in_fm && /^description:/ { found=1; sub(/^description:[[:space:]]*(>-[[:space:]]*)?/,""); print; next }
          in_fm && found && /^[a-zA-Z][a-zA-Z0-9_-]*:/ { found=0 }
          in_fm && found { print }
        ' "$file" | tr '\n' ' ' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
        desc_len=${#desc_text}
        if [[ $desc_len -gt 300 ]]; then
            violations+=("VIOLATION [AGENT-02]: $file — Description is $desc_len chars (max 300) — FIX: Shorten description to at most 300 characters")
        fi
    fi

    if ! grep -q "^tools:" "$file"; then
        violations+=("VIOLATION [AGENT-02]: $file — Missing 'tools:' field — FIX: Add 'tools: <tool1>, <tool2>, ...' field")
    fi
done
shopt -u nullglob

# AGENT-03: agent.yml tools must be valid Claude Code tool names
valid_tools_pattern="^(Read|Write|Edit|Bash|Grep|Glob|Skill|Monitor|WebSearch|WebFetch|NotebookEdit|ToolSearch|Agent|mcp__.*)$"
shopt -s nullglob
for file in .claude/agents/*/agent.yml default/agents/*/agent.yml; do
    [[ -f "$file" ]] || continue

    # Gate on tools: field existence to avoid crash when field is absent (AGENT-02 catches missing field)
    if grep -q "^tools:" "$file"; then
        tools_line=$(grep "^tools:" "$file" | cut -d: -f2- || true)
        # Handle inline comma-separated form: tools: Read, Write, Edit
        if [[ -n "$(echo "$tools_line" | tr -d '[:space:]')" ]]; then
            IFS=',' read -ra tools_arr <<< "$tools_line"
            for tool in "${tools_arr[@]}"; do
                tool=$(echo "$tool" | tr -d '[:space:]')
                if [[ -n "$tool" ]] && ! echo "$tool" | grep -qE "$valid_tools_pattern"; then
                    violations+=("VIOLATION [AGENT-03]: $file — Invalid tool name '$tool' — FIX: Use valid Claude Code tool names (Read, Write, Edit, Bash, Grep, Glob, Skill, etc.)")
                fi
            done
        else
            # Handle YAML block list form: "  - ToolName" lines following "tools:"
            in_tools=false
            while IFS= read -r line; do
                if [[ "$line" =~ ^tools: ]]; then
                    in_tools=true
                    continue
                fi
                if $in_tools; then
                    if [[ "$line" =~ ^[[:space:]]+-[[:space:]]+(.*) ]]; then
                        tool="${BASH_REMATCH[1]}"
                        tool=$(echo "$tool" | tr -d '[:space:]')
                        if [[ -n "$tool" ]] && ! echo "$tool" | grep -qE "$valid_tools_pattern"; then
                            violations+=("VIOLATION [AGENT-03]: $file — Invalid tool name '$tool' — FIX: Use valid Claude Code tool names (Read, Write, Edit, Bash, Grep, Glob, Skill, etc.)")
                        fi
                    elif [[ "$line" =~ ^[a-zA-Z] || ( "$line" =~ ^[[:space:]] && ! "$line" =~ ^[[:space:]]+-[[:space:]] ) ]]; then
                        in_tools=false
                    fi
                fi
            done < "$file"
        fi
    fi
done
shopt -u nullglob

# AGENT-04: agent.yml optional fields must be non-empty if present
shopt -s nullglob
for file in .claude/agents/*/agent.yml default/agents/*/agent.yml; do
    [[ -f "$file" ]] || continue

    if grep -q "^standards:" "$file"; then
        standards_line=$(grep "^standards:" "$file" | cut -d: -f2- | xargs)
        if [[ -z "$standards_line" ]]; then
            violations+=("VIOLATION [AGENT-04]: $file — Empty 'standards:' field — FIX: Remove empty 'standards:' or populate with standard references")
        fi
    fi
done
shopt -u nullglob

# ---------------------------------------------------------------------------
# 4. Standards (STD-01 through STD-04)
# ---------------------------------------------------------------------------

# STD-01: Every path: entry in index.yml must reference an existing .md file
if [[ -f malte/standards/index.yml ]]; then
    # Use yq if available, otherwise fall back to grep+awk
    if command -v yq &>/dev/null; then
        while IFS= read -r path_val; do
            [[ -z "$path_val" ]] && continue
            if [[ ! -f "malte/standards/$path_val" ]]; then
                violations+=("VIOLATION [STD-01]: malte/standards/$path_val — File not found (referenced in index.yml) — FIX: Create the file or remove the entry from malte/standards/index.yml")
            fi
        done < <(yq e '.. | select(has("path")) | .path' malte/standards/index.yml 2>/dev/null | grep -v '^---$' | grep -v '^null$')
    else
        while IFS= read -r path_val; do
            [[ -z "$path_val" ]] && continue
            if [[ ! -f "malte/standards/$path_val" ]]; then
                violations+=("VIOLATION [STD-01]: malte/standards/$path_val — File not found (referenced in index.yml) — FIX: Create the file or remove the entry from malte/standards/index.yml")
            fi
        done < <(grep -E '^\s+path:' malte/standards/index.yml | awk '{print $2}' | tr -d '"'"'")
    fi
fi

# STD-02: Paths in index.yml must be relative and reference .md files only
if [[ -f malte/standards/index.yml ]]; then
    while IFS= read -r line; do
        path=$(echo "$line" | awk '{print $2}' | tr -d '"'"'")
        [[ -z "$path" ]] && continue

        if [[ "$path" == /* || "$path" == ~* ]]; then
            violations+=("VIOLATION [STD-02]: malte/standards/index.yml — Absolute path '$path' — FIX: Use relative paths (e.g., python/style.md)")
        fi

        if [[ "$path" != *.md ]]; then
            violations+=("VIOLATION [STD-02]: malte/standards/index.yml — Non-markdown path '$path' — FIX: Change to .md file reference")
        fi
    done < <(grep -E '^\s+path:' malte/standards/index.yml)
fi

# STD-03: index.yml entries must have non-empty triggers lists
index_file="malte/standards/index.yml"
if [[ -f "$index_file" ]]; then
    if command -v yq &>/dev/null; then
        empty_triggers=$(yq '.standards | to_entries[] | select(.value.triggers | length == 0) | .key' "$index_file" 2>/dev/null)
        [[ -n "$empty_triggers" ]] && violations+=("VIOLATION [STD-03]: $index_file — standards with empty triggers: $empty_triggers — FIX: Add at least one trigger string to each standard")
    else
        # Manual: after "triggers:", next line should be "- something"
        while IFS= read -r line; do
            if [[ "$line" =~ ^[[:space:]]+triggers:$ ]]; then
                read -r next_line
                if [[ ! "$next_line" =~ ^[[:space:]]+-[[:space:]] ]]; then
                    violations+=("VIOLATION [STD-03]: $index_file — found empty triggers block — FIX: Add at least one trigger string")
                fi
            fi
        done < "$index_file"
    fi
fi

# STD-04: Standard .md files should have title and section structure
while IFS= read -r -d '' file; do
    [[ -f "$file" ]] || continue

    if ! grep -q "^# " "$file"; then
        violations+=("VIOLATION [STD-04]: $file — Missing title (level-1 heading) — FIX: Add '# Title' at the top of the file")
    fi

    if ! grep -q "^## " "$file"; then
        violations+=("VIOLATION [STD-04]: $file — Missing section headings (level-2) — FIX: Add '## Section Name' headers to organize content")
    fi
done < <(find malte/standards -name '*.md' -print0 2>/dev/null)

# ---------------------------------------------------------------------------
# 5. Output
# ---------------------------------------------------------------------------
if [[ ${#violations[@]} -eq 0 ]]; then
    echo "Harness entropy scan complete. No violations found."
    exit 0
fi

for v in "${violations[@]}"; do
    echo "$v"
done

echo ""
echo "Total violations: ${#violations[@]}"
exit 1
