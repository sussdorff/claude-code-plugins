#!/bin/bash
# nbj-audit.sh — Inventory collector for NBJ 12-primitive audit
# Requires: python3 (for JSON history parsing, optional — falls back to grep)
# Usage: nbj-audit.sh [project-root]
#
# Detects harness vs project mode, then emits structured inventory
# that the AI evaluates against the 12 primitives.
#
# Output format:
#   mode=harness|project
#   project=<name>
#   skills_count=N
#   PRIMITIVE: N | name | status=present|partial|missing | finding
#   HISTORY: <path> exists|missing
#   TIMESTAMP: <iso8601>

set -euo pipefail

PROJECT_ROOT="${1:-$(pwd)}"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

# ── Mode detection ────────────────────────────────────────────────────────────
HARNESS="false"
if [ -d "$PROJECT_ROOT/malte/skills" ] && [ -d "$PROJECT_ROOT/malte/agents" ]; then
    HARNESS="true"
fi

if [ "$HARNESS" = "true" ]; then
    MODE="harness"
else
    MODE="project"
fi

PROJECT_NAME="$(basename "$PROJECT_ROOT")"
echo "mode=$MODE"
echo "project=$PROJECT_NAME"
echo "root=$PROJECT_ROOT"

# ── Primitive evaluation (harness mode) ──────────────────────────────────────
if [ "$HARNESS" = "true" ]; then
    SKILLS_DIR="$PROJECT_ROOT/malte/skills"
    AGENTS_DIR="$PROJECT_ROOT/malte/agents"
    HOOKS_DIR="$PROJECT_ROOT/malte/hooks"
    CLAUDE_MD="$PROJECT_ROOT/malte/CLAUDE.md"
    GLOBAL_CLAUDE_MD="$PROJECT_ROOT/CLAUDE.md"

    # Count skills
    skills_count=$(find "$SKILLS_DIR" -maxdepth 2 -name "SKILL.md" -type f 2>/dev/null | wc -l | tr -d ' ')
    echo "skills_count=$skills_count"

    # Count agents
    agents_count=$(find "$AGENTS_DIR" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
    echo "agents_count=$agents_count"

    # P1: Tool Registry
    if [ "$skills_count" -ge 20 ]; then
        p1_status="present"
        p1_finding="$skills_count skills in malte/skills/"
    elif [ "$skills_count" -ge 5 ]; then
        p1_status="partial"
        p1_finding="$skills_count skills in malte/skills/ (thin coverage)"
    else
        p1_status="missing"
        p1_finding="malte/skills/ empty or absent"
    fi
    echo "PRIMITIVE: 1 | Tool Registry | status=$p1_status | $p1_finding"

    # P2: Permission System
    if [ -f "$HOOKS_DIR/pre_tool_use.py" ]; then pre_tool_hook="true"; else pre_tool_hook="false"; fi
    safety_rules=$( { grep -cE "BLOCKED|Safety Check|flag for human review" "$CLAUDE_MD" "$GLOBAL_CLAUDE_MD" 2>/dev/null || true; } | awk -F: '{sum+=$2} END{print sum+0}')
    if [ "$pre_tool_hook" = "true" ] && [ "$safety_rules" -ge 3 ]; then
        p2_status="present"
        p2_finding="pre_tool_use.py hook + $safety_rules safety rules in CLAUDE.md"
    elif [ "$pre_tool_hook" = "true" ] || [ "$safety_rules" -ge 1 ]; then
        p2_status="partial"
        hook_desc=$([ "$pre_tool_hook" = "true" ] && echo "hook present" || echo "hook missing")
        p2_finding="$hook_desc, $safety_rules safety rules"
    else
        p2_status="missing"
        p2_finding="no pre_tool_use.py and no safety rules found"
    fi
    echo "PRIMITIVE: 2 | Permission System | status=$p2_status | $p2_finding"

    # P3: Session Persistence
    if [ -d "$PROJECT_ROOT/.beads" ]; then has_beads="true"; else has_beads="false"; fi
    if grep -rqlE "open-brain|memory" "$SKILLS_DIR" 2>/dev/null; then has_memory="true"; else has_memory="false"; fi
    if [ "$has_beads" = "true" ] && [ "$has_memory" = "true" ]; then
        p3_status="present"
        p3_finding=".beads/ dir + open-brain memory skill"
    elif [ "$has_beads" = "true" ] || [ "$has_memory" = "true" ]; then
        p3_status="partial"
        beads_desc=$([ "$has_beads" = "true" ] && echo ".beads/ present" || echo ".beads/ absent")
        mem_desc=$([ "$has_memory" = "true" ] && echo "yes" || echo "no")
        p3_finding="$beads_desc, memory=$mem_desc"
    else
        p3_status="missing"
        p3_finding="no .beads/ dir and no memory skill found"
    fi
    echo "PRIMITIVE: 3 | Session Persistence | status=$p3_status | $p3_finding"

    # P4: Workflow State
    if command -v bd >/dev/null 2>&1; then bd_cmd="true"; else bd_cmd="false"; fi
    if [ -d "$SKILLS_DIR/beads" ]; then beads_skill="true"; else beads_skill="false"; fi
    if [ "$has_beads" = "true" ] && ([ "$bd_cmd" = "true" ] || [ "$beads_skill" = "true" ]); then
        p4_status="present"
        p4_finding=".beads/ + bd CLI for status tracking"
    elif [ "$has_beads" = "true" ]; then
        p4_status="partial"
        p4_finding=".beads/ present but no bd CLI or beads skill"
    else
        p4_status="missing"
        p4_finding="no workflow state tracking"
    fi
    echo "PRIMITIVE: 4 | Workflow State | status=$p4_status | $p4_finding"

    # P5: Token Budget
    if [ -d "$SKILLS_DIR/token-cost" ]; then has_token_skill="true"; else has_token_skill="false"; fi
    tier_refs=$( { grep -cE "tier|token budget|<3k|<5k|Medium tier|Light tier|Heavy tier" "$CLAUDE_MD" "$GLOBAL_CLAUDE_MD" 2>/dev/null || true; } | awk -F: '{sum+=$2} END{print sum+0}')
    if [ "$has_token_skill" = "true" ] && [ "$tier_refs" -ge 2 ]; then
        p5_status="present"
        p5_finding="token-cost skill + $tier_refs tier references in CLAUDE.md"
    elif [ "$has_token_skill" = "true" ] || [ "$tier_refs" -ge 1 ]; then
        p5_status="partial"
        skill_desc=$([ "$has_token_skill" = "true" ] && echo "yes" || echo "no")
        p5_finding="token-cost skill=$skill_desc, tier refs=$tier_refs"
    else
        p5_status="missing"
        p5_finding="no token-cost skill and no tier references"
    fi
    echo "PRIMITIVE: 5 | Token Budget | status=$p5_status | $p5_finding"

    # P6: Streaming Events
    if [ -d "$SKILLS_DIR/cmux" ]; then has_cmux="true"; else has_cmux="false"; fi
    has_orchestrator=$(find "$AGENTS_DIR" -maxdepth 2 -name "*.md" -exec grep -lE "phase|stream|event" {} + 2>/dev/null | wc -l | tr -d ' ')
    if [ "$has_cmux" = "true" ] && [ "$has_orchestrator" -ge 1 ]; then
        p6_status="present"
        p6_finding="cmux skill + orchestrator with streaming phases"
    elif [ "$has_cmux" = "true" ]; then
        p6_status="partial"
        p6_finding="cmux skill present, no orchestrator streaming found"
    else
        p6_status="missing"
        p6_finding="no cmux skill and no streaming events"
    fi
    echo "PRIMITIVE: 6 | Streaming Events | status=$p6_status | $p6_finding"

    # P7: Event Logging
    if [ -f "$HOOKS_DIR/event-log.py" ]; then has_event_hook="true"; else has_event_hook="false"; fi
    if [ -d "$SKILLS_DIR/event-log" ]; then has_event_skill="true"; else has_event_skill="false"; fi
    if [ "$has_event_hook" = "true" ] && [ "$has_event_skill" = "true" ]; then
        p7_status="present"
        p7_finding="event-log.py hook + event-log skill"
    elif [ "$has_event_hook" = "true" ] || [ "$has_event_skill" = "true" ]; then
        p7_status="partial"
        hook_desc=$([ "$has_event_hook" = "true" ] && echo "yes" || echo "no")
        skill_desc=$([ "$has_event_skill" = "true" ] && echo "yes" || echo "no")
        p7_finding="hook=$hook_desc, skill=$skill_desc"
    else
        p7_status="missing"
        p7_finding="no event-log hook or skill"
    fi
    echo "PRIMITIVE: 7 | Event Logging | status=$p7_status | $p7_finding"

    # P8: Verification Harness
    if [ -d "$AGENTS_DIR/review-agent" ] || [ -d "$AGENTS_DIR/holdout-validator" ]; then has_review="true"; else has_review="false"; fi
    if [ -d "$AGENTS_DIR/verification-agent" ] || [ -d "$AGENTS_DIR/constraint-checker" ]; then has_verif="true"; else has_verif="false"; fi
    agent_count=$(find "$AGENTS_DIR" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
    if ([ "$has_review" = "true" ] || [ "$has_verif" = "true" ]) && [ "$agent_count" -ge 3 ]; then
        p8_status="present"
        p8_finding="review/verification agents + $agent_count total agents"
    elif [ "$has_review" = "true" ] || [ "$has_verif" = "true" ]; then
        p8_status="partial"
        p8_finding="some verification agents, only $agent_count total"
    else
        p8_status="missing"
        p8_finding="no review or verification agents ($agent_count agents total)"
    fi
    echo "PRIMITIVE: 8 | Verification Harness | status=$p8_status | $p8_finding"

    # P9: Tool Pool Assembly
    if [ -f "$PROJECT_ROOT/.claude/index.yml" ] || [ -f "$PROJECT_ROOT/malte/index.yml" ]; then has_index="true"; else has_index="false"; fi
    on_demand_refs=$( { grep -cE "on.demand|load.*demand|references/" "$CLAUDE_MD" "$GLOBAL_CLAUDE_MD" 2>/dev/null || true; } | awk -F: '{sum+=$2} END{print sum+0}')
    if [ "$has_index" = "true" ] && [ "$on_demand_refs" -ge 2 ]; then
        p9_status="present"
        p9_finding="index.yml + $on_demand_refs on-demand loading references in CLAUDE.md"
    elif [ "$has_index" = "true" ] || [ "$on_demand_refs" -ge 1 ]; then
        p9_status="partial"
        idx_desc=$([ "$has_index" = "true" ] && echo "yes" || echo "no")
        p9_finding="index=$idx_desc, on-demand refs=$on_demand_refs"
    else
        p9_status="missing"
        p9_finding="no index.yml and no on-demand loading"
    fi
    echo "PRIMITIVE: 9 | Tool Pool Assembly | status=$p9_status | $p9_finding"

    # P10: Transcript Compaction
    has_precompact=$( { grep -cE "PreCompact|compaction|Transcript Compaction|compact" "$CLAUDE_MD" "$GLOBAL_CLAUDE_MD" 2>/dev/null || true; } | awk -F: '{sum+=$2} END{print sum+0}')
    if [ "$has_precompact" -ge 3 ]; then
        p10_status="present"
        p10_finding="$has_precompact compaction references in CLAUDE.md"
    elif [ "$has_precompact" -ge 1 ]; then
        p10_status="partial"
        p10_finding="$has_precompact compaction references (needs more coverage)"
    else
        p10_status="missing"
        p10_finding="no PreCompact rules or compaction behavior defined"
    fi
    echo "PRIMITIVE: 10 | Transcript Compaction | status=$p10_status | $p10_finding"

    # P11: Permission Audit Trail
    if [ -d "$SKILLS_DIR/event-log" ]; then has_audit_skill="true"; else has_audit_skill="false"; fi
    bd_audit=$(command -v bd >/dev/null 2>&1 && bd audit --help 2>/dev/null | head -1 || echo "")
    if [ -n "$bd_audit" ]; then has_bd_audit="true"; else has_bd_audit="false"; fi
    if [ "$has_audit_skill" = "true" ] && [ "$has_bd_audit" = "true" ]; then
        p11_status="present"
        p11_finding="event-log skill + bd audit command available"
    elif [ "$has_event_hook" = "true" ] && [ "$has_audit_skill" = "true" ]; then
        p11_status="present"
        p11_finding="event-log hook captures permission decisions + audit skill"
    elif [ "$has_audit_skill" = "true" ] || [ "$has_event_hook" = "true" ]; then
        p11_status="partial"
        el_desc=$([ "$has_event_hook" = "true" ] && echo "hook" || echo "missing")
        as_desc=$([ "$has_audit_skill" = "true" ] && echo "yes" || echo "no")
        p11_finding="partial trail: event-log=$el_desc, audit-skill=$as_desc"
    else
        p11_status="missing"
        p11_finding="no permission audit trail"
    fi
    echo "PRIMITIVE: 11 | Permission Audit Trail | status=$p11_status | $p11_finding"

    # P12: Doctor + Provenance
    if command -v bd >/dev/null 2>&1 && bd doctor --help >/dev/null 2>&1; then has_bd_doctor="true"; else has_bd_doctor="false"; fi
    if [ "$has_bd_doctor" = "true" ] && [ "$has_beads" = "true" ]; then
        p12_status="present"
        p12_finding="bd doctor available + .beads/ provenance tracking"
    elif [ "$has_bd_doctor" = "true" ] || [ "$has_beads" = "true" ]; then
        p12_status="partial"
        bd_desc=$([ "$has_bd_doctor" = "true" ] && echo "available" || echo "missing")
        beads_desc=$([ "$has_beads" = "true" ] && echo "present" || echo "absent")
        p12_finding="bd=$bd_desc, .beads=$beads_desc"
    else
        p12_status="missing"
        p12_finding="no bd doctor and no .beads/ provenance"
    fi
    echo "PRIMITIVE: 12 | Doctor + Provenance | status=$p12_status | $p12_finding"

# ── Primitive evaluation (project mode) ──────────────────────────────────────
else
    echo "skills_count=0"

    # Helper: count files matching a grep pattern under PROJECT_ROOT
    count_project_files() {
        local pattern="$1"
        { find "$PROJECT_ROOT" -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/dist/*' -not -path '*/build/*' -print0 2>/dev/null | xargs -0 grep -lE "$pattern" 2>/dev/null; true; } | wc -l | tr -d ' '
    }

    # P1: Tool Registry
    api_routes=$(find "$PROJECT_ROOT" -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/dist/*' -not -path '*/build/*' \( -name "routes.ts" -o -name "routes.js" -o -name "router.ts" -o -name "*routes*.ts" -o -name "*.routes.ts" \) 2>/dev/null | wc -l | tr -d ' ')
    if [ "$api_routes" -ge 3 ]; then
        p1_status="present"; p1_finding="$api_routes route files found"
    elif [ "$api_routes" -ge 1 ]; then
        p1_status="partial"; p1_finding="$api_routes route file(s), check for registry pattern"
    else
        p1_status="missing"; p1_finding="no API route files found"
    fi
    echo "PRIMITIVE: 1 | Tool Registry | status=$p1_status | $p1_finding"

    # P2: Permission System
    auth_files=$(find "$PROJECT_ROOT" -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/dist/*' -not -path '*/build/*' \( -name "auth*.ts" -o -name "auth*.js" -o -name "*middleware*" -o -name "*permission*" -o -name "*rbac*" \) 2>/dev/null | wc -l | tr -d ' ')
    validation=$(find "$PROJECT_ROOT" -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/dist/*' -not -path '*/build/*' \( -name "*validation*" -o -name "*validator*" -o -name "*schema*" \) 2>/dev/null | wc -l | tr -d ' ')
    if [ "$auth_files" -ge 2 ] && [ "$validation" -ge 1 ]; then
        p2_status="present"; p2_finding="$auth_files auth/middleware files + $validation validation files"
    elif [ "$auth_files" -ge 1 ] || [ "$validation" -ge 1 ]; then
        p2_status="partial"; p2_finding="auth=$auth_files files, validation=$validation files"
    else
        p2_status="missing"; p2_finding="no auth middleware or validation files"
    fi
    echo "PRIMITIVE: 2 | Permission System | status=$p2_status | $p2_finding"

    # P3: Session Persistence
    db_files=$(find "$PROJECT_ROOT" -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/dist/*' -not -path '*/build/*' \( -name "*.sql" -o -name "*migration*" -o -name "*schema.prisma" -o -name "drizzle*" \) 2>/dev/null | wc -l | tr -d ' ')
    session_files=$(find "$PROJECT_ROOT" -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/dist/*' -not -path '*/build/*' \( -name "*session*" -o -name "*store*" \) 2>/dev/null | wc -l | tr -d ' ')
    if [ "$db_files" -ge 2 ]; then
        p3_status="present"; p3_finding="$db_files DB/migration files (persistence layer present)"
    elif [ "$db_files" -ge 1 ] || [ "$session_files" -ge 1 ]; then
        p3_status="partial"; p3_finding="db=$db_files files, session=$session_files files"
    else
        p3_status="missing"; p3_finding="no DB, migration, or session storage found"
    fi
    echo "PRIMITIVE: 3 | Session Persistence | status=$p3_status | $p3_finding"

    # P4: Workflow State
    state_files=$(find "$PROJECT_ROOT" -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/dist/*' -not -path '*/build/*' \( -name "*workflow*" -o -name "*state*" -o -name "*machine*" -o -name "*status*" \) 2>/dev/null | wc -l | tr -d ' ')
    if [ "$state_files" -ge 3 ]; then
        p4_status="present"; p4_finding="$state_files workflow/state files"
    elif [ "$state_files" -ge 1 ]; then
        p4_status="partial"; p4_finding="$state_files state file(s) — verify state machine coverage"
    else
        p4_status="missing"; p4_finding="no workflow or state machine files"
    fi
    echo "PRIMITIVE: 4 | Workflow State | status=$p4_status | $p4_finding"

    # P5: Token Budget
    rate_limit=$(count_project_files "rateLimit|rate_limit|RateLimit|throttle")
    if [ "$rate_limit" -ge 2 ]; then
        p5_status="present"; p5_finding="$rate_limit files with rate limiting"
    elif [ "$rate_limit" -ge 1 ]; then
        p5_status="partial"; p5_finding="$rate_limit rate limit file(s) — check cost tracking"
    else
        p5_status="missing"; p5_finding="no rate limiting or cost tracking"
    fi
    echo "PRIMITIVE: 5 | Token Budget | status=$p5_status | $p5_finding"

    # P6: Streaming Events
    stream_files=$(count_project_files "EventSource|SSE|WebSocket|socket\.io|EventEmitter|\.emit\(")
    if [ "$stream_files" -ge 2 ]; then
        p6_status="present"; p6_finding="$stream_files files with streaming/events"
    elif [ "$stream_files" -ge 1 ]; then
        p6_status="partial"; p6_finding="$stream_files streaming file(s) — check coverage"
    else
        p6_status="missing"; p6_finding="no WebSocket, SSE, or EventEmitter found"
    fi
    echo "PRIMITIVE: 6 | Streaming Events | status=$p6_status | $p6_finding"

    # P7: Event Logging
    log_files=$(count_project_files "winston|pino|bunyan|log4j|audit.*log|logEvent|logger\.")
    if [ "$log_files" -ge 3 ]; then
        p7_status="present"; p7_finding="$log_files files with structured logging"
    elif [ "$log_files" -ge 1 ]; then
        p7_status="partial"; p7_finding="$log_files logging file(s) — check audit trail completeness"
    else
        p7_status="missing"; p7_finding="no structured logging found"
    fi
    echo "PRIMITIVE: 7 | Event Logging | status=$p7_status | $p7_finding"

    # P8: Verification Harness
    test_files=$(find "$PROJECT_ROOT" -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/dist/*' -not -path '*/build/*' \( -name "*.test.ts" -o -name "*.test.js" -o -name "*.spec.ts" -o -name "*.spec.js" -o -name "*_test.py" -o -name "test_*.py" \) 2>/dev/null | wc -l | tr -d ' ')
    ci_files=$(find "$PROJECT_ROOT" -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/dist/*' -not -path '*/build/*' -name "*.yml" -path "*github*" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$test_files" -ge 5 ] && [ "$ci_files" -ge 1 ]; then
        p8_status="present"; p8_finding="$test_files test files + CI config"
    elif [ "$test_files" -ge 2 ]; then
        p8_status="partial"; p8_finding="$test_files test files, ci=$ci_files"
    else
        p8_status="missing"; p8_finding="$test_files test files, $ci_files CI files — insufficient coverage"
    fi
    echo "PRIMITIVE: 8 | Verification Harness | status=$p8_status | $p8_finding"

    # P9: Tool Pool Assembly
    feature_flags=$(count_project_files "featureFlag|feature_flag|isEnabled|LaunchDarkly|flipper")
    lazy_load=$(count_project_files "dynamic import|lazy|import\('")
    if [ "$feature_flags" -ge 2 ] || ([ "$feature_flags" -ge 1 ] && [ "$lazy_load" -ge 2 ]); then
        p9_status="present"; p9_finding="$feature_flags feature flag files + $lazy_load lazy imports"
    elif [ "$feature_flags" -ge 1 ] || [ "$lazy_load" -ge 1 ]; then
        p9_status="partial"; p9_finding="feature_flags=$feature_flags, lazy_load=$lazy_load files"
    else
        p9_status="missing"; p9_finding="no feature flags or lazy loading found"
    fi
    echo "PRIMITIVE: 9 | Tool Pool Assembly | status=$p9_status | $p9_finding"

    # P10: Transcript Compaction (N/A for project mode)
    echo "PRIMITIVE: 10 | Transcript Compaction | status=partial | N/A in project mode (harness-level only)"

    # P11: Permission Audit Trail
    access_log=$(count_project_files "accessLog|access_log|auditLog|audit_log|authLog")
    if [ "$access_log" -ge 2 ]; then
        p11_status="present"; p11_finding="$access_log access/audit log files"
    elif [ "$access_log" -ge 1 ]; then
        p11_status="partial"; p11_finding="$access_log audit log file(s) — verify completeness"
    else
        p11_status="missing"; p11_finding="no access logs or audit logs"
    fi
    echo "PRIMITIVE: 11 | Permission Audit Trail | status=$p11_status | $p11_finding"

    # P12: Doctor + Provenance
    health_files=$(find "$PROJECT_ROOT" -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/dist/*' -not -path '*/build/*' \( -name "health*" -o -name "*health*" \) 2>/dev/null | wc -l | tr -d ' ')
    provenance=$(count_project_files "version|buildInfo|provenance|gitCommit|BUILD_SHA")
    if [ "$health_files" -ge 1 ] && [ "$provenance" -ge 2 ]; then
        p12_status="present"; p12_finding="$health_files health check + $provenance provenance files"
    elif [ "$health_files" -ge 1 ] || [ "$provenance" -ge 1 ]; then
        p12_status="partial"; p12_finding="health=$health_files files, provenance=$provenance files"
    else
        p12_status="missing"; p12_finding="no health checks or provenance tracking"
    fi
    echo "PRIMITIVE: 12 | Doctor + Provenance | status=$p12_status | $p12_finding"
fi

# ── Delta tracking ────────────────────────────────────────────────────────────
HISTORY_FILE="$PROJECT_ROOT/.beads/nbj-audit-history.json"
if [ -f "$HISTORY_FILE" ]; then
    echo "HISTORY: $HISTORY_FILE exists"
    if command -v python3 >/dev/null 2>&1; then
        last_run=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); runs=d.get('runs',[]); print(runs[-1]['timestamp'] if runs else 'none')" "$HISTORY_FILE" 2>/dev/null || echo "parse-error")
    else
        last_run=$(grep -o '"timestamp": "[^"]*"' "$HISTORY_FILE" 2>/dev/null | tail -1 | cut -d'"' -f4 || echo "unavailable")
    fi
    echo "HISTORY_LAST_RUN: $last_run"
else
    echo "HISTORY: $HISTORY_FILE missing"
fi

echo "TIMESTAMP: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
