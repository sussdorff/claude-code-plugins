#!/usr/bin/env bash
# measure-context.sh — Measure Claude Code context token overhead
#
# Usage: measure-context.sh [OPTIONS]
#
# Options:
#   --mode MODE            Measurement mode: session|full (default: session)
#                            session: only what the harness sends to Claude at
#                                     session start — YAML `description:` fields
#                                     from skills/agents. This is the REAL
#                                     cache-write cost per new session.
#                            full:    worst-case if every skill/agent were fully
#                                     loaded at once — SKILL.md body + references/
#                                     + agent body. Useful for auditing skill
#                                     bloat, NOT for measuring session-start cost.
#   --skills-dir DIR       Override skills search directory
#   --agents-dir DIR       Override agents search directory
#   --claude-md FILE       Override CLAUDE.md path(s), comma-separated
#   --mcp-config FILE      Override MCP config file path
#   --category CAT         Filter: skills|agents|claude-md|mcp|all (default: all)
#   --format FMT           Output format: table|json (default: table)
#   --window N             Context window size in tokens (default: 200000)
#   --save                 Save open-brain observation with audit results
#   --help                 Show this help message

set -euo pipefail

# ── Defaults ────────────────────────────────────────────────────────────────

SKILLS_DIR="${HOME}/.claude/skills"
AGENTS_DIR="${HOME}/.claude/agents"
# Memory chain: global + project + auto-memory (matches harness /memory output).
# Project CLAUDE.md is detected from $PWD (the session project, not this script).
_proj_md="$(pwd)/CLAUDE.md"
_proj_slug="$(pwd | sed 's|/|-|g')"
_auto_md="${HOME}/.claude/projects/${_proj_slug}/memory/MEMORY.md"
CLAUDE_MD_FILES="${HOME}/.claude/CLAUDE.md,${_proj_md},${_auto_md}"
unset _proj_md _proj_slug _auto_md
MCP_CONFIG="${HOME}/.claude/settings.json"
CATEGORY="all"
FORMAT="table"
WINDOW=200000
SAVE_MEMORY=0
MODE="session"
TODAY=$(date +%Y-%m-%d)

# ── Arg parsing ──────────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help)
      grep '^#' "$0" | grep -v '^#!/' | sed 's/^# *//'
      echo ""
      echo "Usage: $(basename "$0") [OPTIONS]"
      exit 0
      ;;
    --mode)         MODE="$2";            shift 2 ;;
    --skills-dir)   SKILLS_DIR="$2";      shift 2 ;;
    --agents-dir)   AGENTS_DIR="$2";      shift 2 ;;
    --claude-md)    CLAUDE_MD_FILES="$2"; shift 2 ;;
    --mcp-config)   MCP_CONFIG="$2";      shift 2 ;;
    --category)     CATEGORY="$2";        shift 2 ;;
    --format)       FORMAT="$2";          shift 2 ;;
    --window)       WINDOW="$2";          shift 2 ;;
    --save)         SAVE_MEMORY=1;        shift   ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if ! [[ "$WINDOW" =~ ^[0-9]+$ ]]; then
  echo "Error: --window must be a positive integer" >&2
  exit 1
fi

if [[ "$MODE" != "session" && "$MODE" != "full" ]]; then
  echo "Error: --mode must be 'session' or 'full' (got: $MODE)" >&2
  exit 1
fi

# ── Token estimation ─────────────────────────────────────────────────────────

tokens_for_file() {
  local file="$1"
  if [ -f "$file" ]; then
    local words
    words=$(wc -w < "$file" | tr -d ' ')
    LC_ALL=C awk "BEGIN {printf \"%d\", $words * 1.33}"
  else
    echo 0
  fi
}

# Extract only the YAML `description:` field (supports block and folded scalars)
# from a frontmatter-prefixed markdown file and return token estimate.
# This is what the harness actually sends to Claude at session start for
# skills (via the Skill system-reminder) and agents (via the Agent tool schema).
tokens_for_description() {
  local file="$1"
  [ -f "$file" ] || { echo 0; return; }
  local words
  words=$(awk '
    /^---[[:space:]]*$/ { n++; if (n==2) exit; next }
    n==1 && /^description:/ {
      flag = 1
      sub(/^description:[[:space:]]*[>|]?[-+]?[[:space:]]*/, "")
      if (length($0) > 0) print
      next
    }
    n==1 && flag && /^[A-Za-z_][A-Za-z0-9_-]*:/ { flag = 0; next }
    n==1 && flag { print }
  ' "$file" | wc -w | tr -d ' ')
  LC_ALL=C awk "BEGIN {printf \"%d\", $words * 1.33}"
}

pct() {
  local tokens="$1"
  LC_ALL=C awk "BEGIN {printf \"%.2f\", ($tokens / $WINDOW) * 100}"
}

# ── Contributor tracking (global arrays, populated directly — not in subshells) ──

CONTRIBUTOR_NAMES=()
CONTRIBUTOR_CATEGORIES=()
CONTRIBUTOR_TOKENS=()

# ── Counters ──────────────────────────────────────────────────────────────────

TOKENS_SKILLS=0
TOKENS_AGENTS=0
TOKENS_CLAUDE_MD=0
TOKENS_MCP=0

# ── Scan skills ──────────────────────────────────────────────────────────────

scan_skills() {
  [ -d "$SKILLS_DIR" ] || return 0

  local seen=""
  while IFS= read -r skill_file; do
    local resolved
    resolved="$(cd "$(dirname "$skill_file")" && pwd -P)/$(basename "$skill_file")"
    if ! echo "$seen" | grep -qF "$resolved"; then
      seen="$seen|$resolved"
      local skill_name
      skill_name="$(basename "$(dirname "$skill_file")")"
      local skill_tokens

      if [ "$MODE" = "session" ]; then
        # Session-start mode: only the YAML `description:` field is sent
        # to Claude via the Skill system-reminder. Body and references/ are
        # loaded on-demand when the skill is actually invoked.
        skill_tokens=$(tokens_for_description "$skill_file")
      else
        # Full-load mode: worst case if every skill were fully loaded —
        # SKILL.md body + references/ directory.
        local skill_md_tokens
        skill_md_tokens=$(tokens_for_file "$skill_file")
        skill_tokens="$skill_md_tokens"
        local ref_dir
        ref_dir="$(dirname "$skill_file")/references"
        if [ -d "$ref_dir" ]; then
          while IFS= read -r ref_file; do
            local ref_tokens
            ref_tokens=$(tokens_for_file "$ref_file")
            skill_tokens=$((skill_tokens + ref_tokens))
          done < <(find "$ref_dir" -type f 2>/dev/null)
        fi
      fi

      TOKENS_SKILLS=$((TOKENS_SKILLS + skill_tokens))

      CONTRIBUTOR_NAMES+=("$skill_name")
      CONTRIBUTOR_CATEGORIES+=("skill")
      CONTRIBUTOR_TOKENS+=("$skill_tokens")
    fi
  done < <(
    # User skills
    find "$SKILLS_DIR" -maxdepth 2 -name "SKILL.md" -type f 2>/dev/null
    # Plugin skills (installed via plugin-management / marketplace)
    find "${HOME}/.claude/plugins" -path "*/skills/*/SKILL.md" -type f 2>/dev/null
  )
}

# ── Scan agents ──────────────────────────────────────────────────────────────

scan_agents() {
  [ -d "$AGENTS_DIR" ] || return 0

  while IFS= read -r agent_file; do
    local agent_name
    agent_name="$(basename "$(dirname "$agent_file")")"
    local agent_tokens

    if [ "$MODE" = "session" ]; then
      # Session-start mode: only the YAML `description:` field appears
      # inline in the Agent tool schema as a `subagent_type` option.
      # The agent body is only loaded when the agent is actually spawned.
      agent_tokens=$(tokens_for_description "$agent_file")
    else
      agent_tokens=$(tokens_for_file "$agent_file")
    fi

    TOKENS_AGENTS=$((TOKENS_AGENTS + agent_tokens))

    CONTRIBUTOR_NAMES+=("$agent_name")
    CONTRIBUTOR_CATEGORIES+=("agent")
    CONTRIBUTOR_TOKENS+=("$agent_tokens")
  done < <(find "$AGENTS_DIR" -maxdepth 2 \( -name "agent.md" -o -name "AGENT.md" -o -name "prompt.md" \) -type f 2>/dev/null)
}

# ── Scan CLAUDE.md chain ──────────────────────────────────────────────────────

scan_claude_md() {
  local IFS_OLD="$IFS"
  IFS=','
  local files_arr
  read -ra files_arr <<< "$CLAUDE_MD_FILES"
  IFS="$IFS_OLD"

  for file in "${files_arr[@]}"; do
    file="${file# }"  # trim leading space
    [ -f "$file" ] || continue
    local tokens
    tokens=$(tokens_for_file "$file")
    TOKENS_CLAUDE_MD=$((TOKENS_CLAUDE_MD + tokens))

    # Shorten home path for display
    local label="${file/#$HOME/~}"

    CONTRIBUTOR_NAMES+=("$label")
    CONTRIBUTOR_CATEGORIES+=("claude-md")
    CONTRIBUTOR_TOKENS+=("$tokens")
  done
}

# ── Scan MCP config ───────────────────────────────────────────────────────────

scan_mcp() {
  [ -f "$MCP_CONFIG" ] || return 0
  [ "$MCP_CONFIG" = "/dev/null" ] && return 0

  if command -v python3 >/dev/null 2>&1; then
    local count
    count=$(MCP_CONFIG="$MCP_CONFIG" python3 - <<'PYEOF' 2>/dev/null || echo 0
import os, json
try:
  d = json.load(open(os.environ['MCP_CONFIG']))
  servers = d.get('mcpServers', {})
  print(len(servers))
except Exception:
  print(0)
PYEOF
)

    if [ "$count" -gt 0 ]; then
      # Estimate: server name + transport config ~20 tokens each
      local mcp_tokens=$((count * 20))
      TOKENS_MCP=$((TOKENS_MCP + mcp_tokens))

      CONTRIBUTOR_NAMES+=("mcp-servers(${count})")
      CONTRIBUTOR_CATEGORIES+=("mcp")
      CONTRIBUTOR_TOKENS+=("$mcp_tokens")
    fi
  fi
}

# ── Run scans ─────────────────────────────────────────────────────────────────

if [[ "$CATEGORY" == "all" || "$CATEGORY" == "skills" ]];     then scan_skills;    fi
if [[ "$CATEGORY" == "all" || "$CATEGORY" == "agents" ]];     then scan_agents;    fi
if [[ "$CATEGORY" == "all" || "$CATEGORY" == "claude-md" ]];  then scan_claude_md; fi
if [[ "$CATEGORY" == "all" || "$CATEGORY" == "mcp" ]];        then scan_mcp;       fi

TOTAL=$((TOKENS_SKILLS + TOKENS_AGENTS + TOKENS_CLAUDE_MD + TOKENS_MCP))

# ── Sort contributors descending by token count ───────────────────────────────

n_contributors=${#CONTRIBUTOR_NAMES[@]}
SORTED_INDICES=()
if [ "$n_contributors" -gt 0 ]; then
  # Build index-token pairs, sort, extract indices
  while IFS= read -r idx; do
    SORTED_INDICES+=("$idx")
  done < <(
    for ((i=0; i<n_contributors; i++)); do
      echo "${CONTRIBUTOR_TOKENS[$i]} $i"
    done | sort -rn | awk '{print $2}'
  )
fi

# ── Budget warnings ────────────────────────────────────────────────────────────
# Only meaningful in full-load mode (tier budgets apply to full SKILL.md+refs).
# In session mode, descriptions are too small to exceed tier budgets.

WARNINGS=()
if [ "$MODE" = "full" ]; then
for ((i=0; i<n_contributors; i++)); do
  c_name="${CONTRIBUTOR_NAMES[$i]}"
  c_cat="${CONTRIBUTOR_CATEGORIES[$i]}"
  c_tok="${CONTRIBUTOR_TOKENS[$i]}"

  if [ "$c_cat" = "skill" ]; then
    local_skill_file="$SKILLS_DIR/$c_name/SKILL.md"
    if [ -f "$local_skill_file" ]; then
      md_tok=$(tokens_for_file "$local_skill_file")
      if [ "$md_tok" -lt 1000 ] && [ "$c_tok" -gt 1000 ]; then
        WARNINGS+=("$c_name: light-tier exceeds 1000 token budget (total: ${c_tok})")
      elif [ "$md_tok" -lt 3000 ] && [ "$c_tok" -gt 5000 ]; then
        WARNINGS+=("$c_name: medium-tier exceeds 5000 token total budget (total: ${c_tok})")
      elif [ "$md_tok" -ge 3000 ] && [ "$c_tok" -gt 8000 ]; then
        WARNINGS+=("$c_name: heavy-tier exceeds 8000 token total budget (total: ${c_tok})")
      fi
    fi
  fi
done
fi  # MODE == full

# ── Determine budget status for a contributor ─────────────────────────────────

budget_status() {
  local c_name="$1"
  local c_cat="$2"
  local c_tok="$3"

  # Budget tiers apply only to full-load worst-case measurements.
  if [ "$MODE" != "full" ] || [ "$c_cat" != "skill" ]; then
    echo "-"
    return
  fi

  local skill_file="$SKILLS_DIR/$c_name/SKILL.md"
  if [ ! -f "$skill_file" ]; then
    echo "N/A"
    return
  fi

  local md_tok
  md_tok=$(tokens_for_file "$skill_file")

  if [ "$md_tok" -lt 1000 ]; then
    if [ "$c_tok" -le 1000 ]; then echo "ok(light)"; else echo "OVER(light:1k)"; fi
  elif [ "$md_tok" -lt 3000 ]; then
    if [ "$c_tok" -le 5000 ]; then echo "ok(medium)"; else echo "OVER(medium:5k)"; fi
  else
    if [ "$c_tok" -le 8000 ]; then echo "ok(heavy)"; else echo "OVER(heavy:8k)"; fi
  fi
}

# ── Output: JSON ──────────────────────────────────────────────────────────────

if [ "$FORMAT" = "json" ]; then
  total_pct=$(pct "$TOTAL")
  pct_skills=$(pct "$TOKENS_SKILLS")
  pct_agents=$(pct "$TOKENS_AGENTS")
  pct_claude=$(pct "$TOKENS_CLAUDE_MD")
  pct_mcp=$(pct "$TOKENS_MCP")

  # Write data to a temp file for python to read
  tmpfile=$(mktemp)
  trap 'rm -f "$tmpfile"' EXIT

  {
    echo "DATE=${TODAY}"
    echo "WINDOW=${WINDOW}"
    echo "TOTAL=${TOTAL}"
    echo "TOTAL_PCT=${total_pct}"
    echo "TOKENS_SKILLS=${TOKENS_SKILLS}"
    echo "TOKENS_AGENTS=${TOKENS_AGENTS}"
    echo "TOKENS_CLAUDE_MD=${TOKENS_CLAUDE_MD}"
    echo "TOKENS_MCP=${TOKENS_MCP}"
    echo "PCT_SKILLS=${pct_skills}"
    echo "PCT_AGENTS=${pct_agents}"
    echo "PCT_CLAUDE=${pct_claude}"
    echo "PCT_MCP=${pct_mcp}"
    echo "---CONTRIBUTORS---"
    for idx in "${SORTED_INDICES[@]}"; do
      c_name="${CONTRIBUTOR_NAMES[$idx]}"
      c_cat="${CONTRIBUTOR_CATEGORIES[$idx]}"
      c_tok="${CONTRIBUTOR_TOKENS[$idx]}"
      c_pct=$(pct "$c_tok")
      printf '%s\t%s\t%s\t%s\n' "$c_name" "$c_cat" "$c_tok" "$c_pct"
    done
    echo "---WARNINGS---"
    if [ ${#WARNINGS[@]} -gt 0 ]; then
      for warn in "${WARNINGS[@]}"; do
        [ -n "$warn" ] && echo "$warn"
      done
    fi
  } > "$tmpfile"

  TMPFILE="$tmpfile" python3 - <<'PYEOF'
import os, json

data = {}
contributors = []
warnings = []
mode = 'header'

with open(os.environ['TMPFILE']) as f:
    for line in f:
        line = line.rstrip('\n')
        if line == '---CONTRIBUTORS---':
            mode = 'contributors'
            continue
        elif line == '---WARNINGS---':
            mode = 'warnings'
            continue

        if mode == 'header':
            if '=' in line:
                k, v = line.split('=', 1)
                data[k] = v
        elif mode == 'contributors':
            if '\t' in line:
                parts = line.split('\t', 3)
                contributors.append({
                    'name': parts[0],
                    'category': parts[1],
                    'tokens': int(parts[2]),
                    'pct_of_context': float(parts[3])
                })
        elif mode == 'warnings':
            if line.strip():
                warnings.append(line)

output = {
    'date': data['DATE'],
    'context_window': int(data['WINDOW']),
    'summary': {
        'total_tokens': int(data['TOTAL']),
        'pct_of_context': float(data['TOTAL_PCT'])
    },
    'categories': {
        'skills':    {'tokens': int(data['TOKENS_SKILLS']),    'pct': float(data['PCT_SKILLS'])},
        'agents':    {'tokens': int(data['TOKENS_AGENTS']),    'pct': float(data['PCT_AGENTS'])},
        'claude_md': {'tokens': int(data['TOKENS_CLAUDE_MD']), 'pct': float(data['PCT_CLAUDE'])},
        'mcp':       {'tokens': int(data['TOKENS_MCP']),       'pct': float(data['PCT_MCP'])}
    },
    'contributors': contributors,
    'warnings': warnings
}
print(json.dumps(output, indent=2))
PYEOF
  exit 0
fi

# ── Output: Table ──────────────────────────────────────────────────────────────

total_pct=$(pct "$TOTAL")
window_fmt=$(printf "%'.0f" "$WINDOW" 2>/dev/null || echo "$WINDOW")

if [ "$MODE" = "session" ]; then
  mode_label="session-start (YAML descriptions only — what the harness actually sends at session start)"
else
  mode_label="full-load (worst case — every skill/agent body + references/ loaded at once)"
fi

echo "## Context Token Audit — $TODAY"
echo ""
echo "**Mode:** ${mode_label}"
echo ""
echo "### Summary"
echo "Total context components: ~${TOTAL} tokens"
echo "Context window: ${window_fmt} tokens (${total_pct}% used by static context)"
echo ""
echo "### By Category"
echo "| Category        | Tokens | % of Context |"
echo "|-----------------|--------|--------------|"
printf "| %-15s | %6d | %11s%% |\n" "Skills"    "$TOKENS_SKILLS"    "$(pct "$TOKENS_SKILLS")"
printf "| %-15s | %6d | %11s%% |\n" "Agents"    "$TOKENS_AGENTS"    "$(pct "$TOKENS_AGENTS")"
printf "| %-15s | %6d | %11s%% |\n" "CLAUDE.md" "$TOKENS_CLAUDE_MD" "$(pct "$TOKENS_CLAUDE_MD")"
printf "| %-15s | %6d | %11s%% |\n" "MCP"       "$TOKENS_MCP"       "$(pct "$TOKENS_MCP")"
printf "| %-15s | %6d | %11s%% |\n" "**TOTAL**" "$TOTAL"            "$total_pct"
echo ""
echo "### Ranked Contributors (heaviest first)"
echo "| # | Name | Category | Tokens | % of Context | Budget Status |"
echo "|---|------|----------|--------|--------------|---------------|"

rank=1
for idx in "${SORTED_INDICES[@]}"; do
  c_name="${CONTRIBUTOR_NAMES[$idx]}"
  c_cat="${CONTRIBUTOR_CATEGORIES[$idx]}"
  c_tok="${CONTRIBUTOR_TOKENS[$idx]}"
  c_pct=$(pct "$c_tok")
  bstat=$(budget_status "$c_name" "$c_cat" "$c_tok")
  printf "| %d | %-30s | %-8s | %6d | %11s%% | %s |\n" \
    "$rank" "$c_name" "$c_cat" "$c_tok" "$c_pct" "$bstat"
  rank=$((rank + 1))
done

if [ "$MODE" = "full" ]; then
  echo ""
  echo "### Budget Warnings"
  if [ ${#WARNINGS[@]} -eq 0 ]; then
    echo "No budget violations detected."
  else
    for warn in "${WARNINGS[@]}"; do
      echo "  $warn"
    done
  fi
fi

echo ""
echo "### Notes"
echo "- Token estimate: word count x 1.33 (approximation for English prose)"
echo "- MCP server instructions are runtime-provided and cannot be measured statically."
echo "  Only server count and config metadata are reflected above."
if [ "$MODE" = "session" ]; then
  echo "- Session mode: skills/agents counted by YAML \`description:\` field only."
  echo "  Skill bodies and references/ are loaded lazily when a skill is invoked."
  echo "  Run with \`--mode full\` to audit worst-case skill/agent fleet size."
else
  echo "- Full mode: skills counted as SKILL.md body + references/ directory."
  echo "  This is NOT the session-start cost. Run with \`--mode session\` (default)"
  echo "  for real cache-write overhead per new session."
fi

# ── AK4: Save trending observation ────────────────────────────────────────────

if [ "$SAVE_MEMORY" -eq 1 ]; then
  echo ""
  echo "### SAVE_OBSERVATION"
  echo "title: Token Cost Audit ${TODAY}"
  echo "type: observation"
  echo "text: |"
  echo "  Token cost audit ${TODAY}."
  echo "  Total: ${TOTAL} tokens (${total_pct}% of ${WINDOW} context window)."
  echo "  Skills: ${TOKENS_SKILLS} | Agents: ${TOKENS_AGENTS} | CLAUDE.md: ${TOKENS_CLAUDE_MD} | MCP: ${TOKENS_MCP}."
  if [ ${#WARNINGS[@]} -gt 0 ]; then
    echo "  Budget violations: ${#WARNINGS[@]}"
    for warn in "${WARNINGS[@]}"; do
      echo "    - $warn"
    done
  fi
  echo "  Top 3 contributors:"
  top3=0
  for idx in "${SORTED_INDICES[@]}"; do
    [ "$top3" -ge 3 ] && break
    c_name="${CONTRIBUTOR_NAMES[$idx]}"
    c_tok="${CONTRIBUTOR_TOKENS[$idx]}"
    c_pct=$(pct "$c_tok")
    echo "    - ${c_name}: ${c_tok} tokens (${c_pct}%)"
    top3=$((top3 + 1))
  done
  echo ""
  echo "# When Claude reads SAVE_OBSERVATION section: call mcp__open-brain__save_memory"
  echo "# with type=observation, title and text as shown above."
fi
