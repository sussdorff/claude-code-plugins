#!/usr/bin/env zsh
#
# Script: style-engine.zsh
# Description: Commit message style detection and application
# Usage: Sourced by git-ops.zsh
# Requires: git, grep, sed

# Reset to known ZSH defaults
emulate -LR zsh

# Detect commit style from CLAUDE.md files
# Priority: CLAUDE.local.md > CLAUDE.md > default
detect_commit_style() {
    typeset style="conventional"  # default

    # Check CLAUDE.md in home directory (user-wide)
    if [[ -f ~/.claude/CLAUDE.md ]]; then
        typeset user_style=$(grep -i "^Commit style:" ~/.claude/CLAUDE.md 2>/dev/null | cut -d: -f2- | xargs)
        [[ -n "$user_style" ]] && style="$user_style"
    elif [[ -f ~/CLAUDE.md ]]; then
        typeset user_style=$(grep -i "^Commit style:" ~/CLAUDE.md 2>/dev/null | cut -d: -f2- | xargs)
        [[ -n "$user_style" ]] && style="$user_style"
    fi

    # Check CLAUDE.local.md in current directory (project-specific - overrides)
    if [[ -f ./CLAUDE.local.md ]]; then
        typeset project_style=$(grep -i "^Commit style:" ./CLAUDE.local.md 2>/dev/null | cut -d: -f2- | xargs)
        [[ -n "$project_style" ]] && style="$project_style"
    fi

    echo "$style"
}

# Detect attribution setting from CLAUDE.md files
# Priority: CLAUDE.local.md > CLAUDE.md > default (none)
detect_attribution_setting() {
    typeset attribution="none"  # default

    # Check CLAUDE.md in home directory (user-wide)
    if [[ -f ~/.claude/CLAUDE.md ]]; then
        typeset user_attr=$(grep -i "^Commit attribution:" ~/.claude/CLAUDE.md 2>/dev/null | cut -d: -f2- | xargs)
        [[ -n "$user_attr" ]] && attribution="$user_attr"
    elif [[ -f ~/CLAUDE.md ]]; then
        typeset user_attr=$(grep -i "^Commit attribution:" ~/CLAUDE.md 2>/dev/null | cut -d: -f2- | xargs)
        [[ -n "$user_attr" ]] && attribution="$user_attr"
    fi

    # Check CLAUDE.local.md in current directory (project-specific - overrides)
    if [[ -f ./CLAUDE.local.md ]]; then
        typeset project_attr=$(grep -i "^Commit attribution:" ./CLAUDE.local.md 2>/dev/null | cut -d: -f2- | xargs)
        [[ -n "$project_attr" ]] && attribution="$project_attr"
    fi

    echo "$attribution"
}

# Apply style transformation to commit message
# Args: message, style
apply_commit_style() {
    typeset message=$1
    typeset style=$2

    case "$style" in
        conventional)
            # Already in conventional format, pass through
            echo "$message"
            ;;
        pirate)
            transform_to_pirate "$message"
            ;;
        snarky)
            transform_to_snarky "$message"
            ;;
        emoji)
            transform_to_emoji "$message"
            ;;
        minimal)
            strip_prefixes "$message"
            ;;
        corporate)
            transform_to_corporate "$message"
            ;;
        *)
            # Unknown style, pass through as-is
            echo "$message"
            ;;
    esac
}

# Transform conventional commit to pirate style
# Args: conventional message
transform_to_pirate() {
    typeset message=$1

    # Check if message matches conventional format
    if echo "$message" | grep -qE '^(feat|fix|docs|refactor|test|chore|perf|style)(\([^)]+\))?: .+'; then
        # Extract type (first word before colon)
        typeset type=$(echo "$message" | sed -E 's/^([a-z]+).*/\1/')

        # Extract scope (if present)
        typeset scope=""
        if echo "$message" | grep -q '('; then
            scope=$(echo "$message" | sed -E 's/^[a-z]+\(([^)]+)\).*/\1/')
        fi

        # Extract description (after colon)
        typeset desc=$(echo "$message" | sed -E 's/^[a-z]+(\([^)]+\))?: //')

        typeset action=""
        case "$type" in
            feat)
                action="Hoisted the new feature"
                ;;
            fix)
                action="Plundered the bug in"
                ;;
            docs)
                action="Scribed the scrolls for"
                ;;
            refactor)
                action="Rejiggered the code for"
                ;;
            test)
                action="Tested the waters of"
                ;;
            chore)
                action="Swabbed the decks"
                ;;
            perf)
                action="Made faster the"
                ;;
            style)
                action="Polished the brass on"
                ;;
        esac

        if [[ -n "$scope" ]]; then
            echo "Arr! ${action} ${scope}: ${desc}"
        else
            echo "Arr! ${action}: ${desc}"
        fi
    else
        # Not in conventional format, add pirate prefix
        echo "Arr! ${message}"
    fi
}

# Transform to snarky style
# Args: conventional message
transform_to_snarky() {
    typeset message=$1

    # Check if message matches conventional format
    if echo "$message" | grep -qE '^(feat|fix|docs|refactor|test|chore|perf|style)(\([^)]+\))?: .+'; then
        # Extract type
        typeset type=$(echo "$message" | sed -E 's/^([a-z]+).*/\1/')

        # Extract scope (if present)
        typeset scope=""
        if echo "$message" | grep -q '('; then
            scope=$(echo "$message" | sed -E 's/^[a-z]+\(([^)]+)\).*/\1/')
        fi

        # Extract description
        typeset desc=$(echo "$message" | sed -E 's/^[a-z]+(\([^)]+\))?: //')

        typeset sarcasm=""
        case "$type" in
            feat)
                sarcasm="Because apparently we needed"
                ;;
            fix)
                sarcasm="Obviously this needed attention"
                ;;
            docs)
                sarcasm="Yet another documentation update for"
                ;;
            refactor)
                sarcasm="Because the previous implementation was clearly brilliant"
                ;;
            test)
                sarcasm="Testing, because who doesn't love tests for"
                ;;
            chore)
                sarcasm="The thrilling chore of"
                ;;
            *)
                sarcasm="Surprise"
                ;;
        esac

        if [[ -n "$scope" ]]; then
            echo "${sarcasm} (${scope}): ${desc}"
        else
            echo "${sarcasm}: ${desc}"
        fi
    else
        # Not in conventional format, add sarcasm
        echo "Obviously: ${message}"
    fi
}

# Transform to emoji style
# Args: conventional message
transform_to_emoji() {
    typeset message=$1

    # Check if message starts with a conventional type
    if echo "$message" | grep -qE '^(feat|fix|docs|refactor|test|chore|perf|style)'; then
        typeset type=$(echo "$message" | sed -E 's/^([a-z]+).*/\1/')

        typeset emoji=""
        case "$type" in
            feat)
                emoji="✨"
                ;;
            fix)
                emoji="🐛"
                ;;
            docs)
                emoji="📝"
                ;;
            refactor)
                emoji="♻️"
                ;;
            test)
                emoji="✅"
                ;;
            chore)
                emoji="🔧"
                ;;
            perf)
                emoji="⚡"
                ;;
            style)
                emoji="💄"
                ;;
        esac

        echo "${emoji} ${message}"
    else
        # No conventional prefix, just add generic emoji
        echo "📌 ${message}"
    fi
}

# Strip type prefixes for minimal style
# Args: conventional message
strip_prefixes() {
    typeset message=$1

    # Remove conventional prefix if present
    if echo "$message" | grep -qE '^(feat|fix|docs|refactor|test|chore|perf|style)(\([^)]+\))?: .+'; then
        echo "$message" | sed -E 's/^[a-z]+(\([^)]+\))?: //'
    else
        echo "$message"
    fi
}

# Transform to corporate style
# Args: conventional message
transform_to_corporate() {
    typeset message=$1

    # Check if message matches conventional format
    if echo "$message" | grep -qE '^(feat|fix|docs|refactor|test|chore|perf|style)(\([^)]+\))?: .+'; then
        # Extract type
        typeset type=$(echo "$message" | sed -E 's/^([a-z]+).*/\1/')

        # Extract scope (if present)
        typeset scope=""
        if echo "$message" | grep -q '('; then
            scope=$(echo "$message" | sed -E 's/^[a-z]+\(([^)]+)\).*/\1/')
        fi

        # Extract description
        typeset desc=$(echo "$message" | sed -E 's/^[a-z]+(\([^)]+\))?: //')

        typeset category=""
        case "$type" in
            feat)
                category="Feature"
                ;;
            fix)
                category="Defect Fix"
                ;;
            docs)
                category="Documentation"
                ;;
            refactor)
                category="Code Improvement"
                ;;
            test)
                category="Test Enhancement"
                ;;
            chore)
                category="Maintenance"
                ;;
            perf)
                category="Performance Enhancement"
                ;;
            style)
                category="Code Style"
                ;;
        esac

        # Capitalize first letter of description
        desc="$(tr '[:lower:]' '[:upper:]' <<< ${desc:0:1})${desc:1}"

        if [[ -n "$scope" ]]; then
            # Uppercase the scope
            scope=$(echo "$scope" | tr '[:lower:]' '[:upper:]')
            echo "[${scope}] ${category}: ${desc}"
        else
            echo "${category}: ${desc}"
        fi
    else
        # Not in conventional format, use generic corporate format
        typeset desc="$(tr '[:lower:]' '[:upper:]' <<< ${message:0:1})${message:1}"
        echo "Update: ${desc}"
    fi
}

# Remove attribution footers from commit message
# Args: commit message (potentially multi-line)
remove_attribution() {
    typeset message=$1

    # Remove "Generated with Claude Code" footer
    message=$(echo "$message" | sed '/^🤖 Generated with \[Claude Code\]/d')
    message=$(echo "$message" | sed '/^Generated with \[Claude Code\]/d')

    # Remove "Co-Authored-By: Claude" footer
    message=$(echo "$message" | sed '/^Co-Authored-By: Claude/d')

    # Trim only trailing blank lines (not all blank lines)
    # This removes empty lines at the end but keeps the message content
    message=$(echo "$message" | sed -e :a -e '/^\n*$/{$d;N;ba' -e '}')

    echo "$message"
}
