#!/usr/bin/env bash
# Fixture-based test for entropy-scan.sh
# Creates a minimal harness with known violations and verifies exact output.
# Exit 0 = all tests passed. Exit 1 = one or more tests failed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENTROPY_SCAN="$SCRIPT_DIR/../scripts/entropy-scan.sh"
PASS=0
FAIL=0

pass() { echo "PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $1"; FAIL=$((FAIL + 1)); }

# ---------------------------------------------------------------------------
# Setup: create a temporary fixture harness
# ---------------------------------------------------------------------------
FIXTURE=$(mktemp -d)
CLEAN=$(mktemp -d)
trap 'rm -rf "$FIXTURE" "$CLEAN"' EXIT

mkdir -p "$FIXTURE/malte/skills/good-skill"
mkdir -p "$FIXTURE/malte/skills/bad-skill-no-md"       # SKILL-01: missing SKILL.md
mkdir -p "$FIXTURE/malte/skills/bad-skill-desc"         # SKILL-02: short description
mkdir -p "$FIXTURE/malte/skills/bad-skill-sections"     # SKILL-03: missing Overview
mkdir -p "$FIXTURE/malte/skills/bad-skill-stray"        # SKILL-05: stray file
mkdir -p "$FIXTURE/.claude/hooks"
mkdir -p "$FIXTURE/.claude/agents/good-agent"
mkdir -p "$FIXTURE/.claude/agents/bad-agent-no-tools"
mkdir -p "$FIXTURE/.claude/agents/bad-agent-invalid-tools"
mkdir -p "$FIXTURE/malte/standards"

# --- Good skill — passes all invariants ---
cat > "$FIXTURE/malte/skills/good-skill/SKILL.md" << 'EOF'
---
name: good-skill
description: >-
  A well-formed skill that meets all invariants for harness scanner validation testing.
  Use when you need to confirm entropy-scan works correctly on valid fixtures.
  Triggers on: good skill, test skill, harness test, entropy scanner.
---

# Good Skill

## Overview

This skill demonstrates correct harness structure for testing purposes.

## When to Use

- "good skill" or "test skill"

## Out of Scope

- Nothing special.
EOF

# --- SKILL-02: too-short description (< 150 chars) ---
cat > "$FIXTURE/malte/skills/bad-skill-desc/SKILL.md" << 'EOF'
---
name: bad-skill-desc
description: >-
  Too short.
---

# Bad Desc Skill

## Overview

Short description test.

## When to Use

- test
EOF

# --- SKILL-03: missing ## Overview ---
cat > "$FIXTURE/malte/skills/bad-skill-sections/SKILL.md" << 'EOF'
---
name: bad-skill-sections
description: >-
  A skill with correct frontmatter but missing the required Overview section.
  This triggers SKILL-03. Triggers on: sections test, missing overview test.
  Used for entropy-scan fixture validation only.
---

# Bad Sections Skill

## When to Use

- "sections test"
EOF

# --- SKILL-05: stray log file at top level ---
cat > "$FIXTURE/malte/skills/bad-skill-stray/SKILL.md" << 'EOF'
---
name: bad-skill-stray
description: >-
  A skill with a stray log file at top level to trigger SKILL-05 violation.
  Triggers on: stray file test, SKILL-05 test, entropy fixture.
  Used for entropy-scan fixture validation only.
---

# Stray File Skill

## Overview

Has a stray file.

## When to Use

- "stray test"
EOF
echo "leftover log data" > "$FIXTURE/malte/skills/bad-skill-stray/stderr.log"

# --- Good hook — passes HOOK-01..04 ---
cat > "$FIXTURE/.claude/hooks/good-hook.sh" << 'EOF'
#!/usr/bin/env bash
# Exit codes:
#   0 = allow (normal operation)
#   2 = deny (blocked operation)
set -euo pipefail
INPUT=$(cat)
echo "OK"
exit 0
EOF

# --- Bad hook — missing set -euo pipefail (HOOK-02), missing exit comments (HOOK-01),
#     uses while IFS= read instead of INPUT=$(cat) (HOOK-03), no explicit exit code (HOOK-04) ---
cat > "$FIXTURE/.claude/hooks/bad-hook.sh" << 'EOF'
#!/usr/bin/env bash
while IFS= read -r line; do
    echo "bad: $line"
done
EOF

# --- Good agent ---
cat > "$FIXTURE/.claude/agents/good-agent/agent.yml" << 'EOF'
name: good-agent
description: "A properly configured agent for testing. Validates the harness scanner."
tools: Read, Write, Edit
EOF

# --- AGENT-02: missing tools field ---
cat > "$FIXTURE/.claude/agents/bad-agent-no-tools/agent.yml" << 'EOF'
name: bad-agent-no-tools
description: "An agent missing the required tools field."
EOF

# --- AGENT-03: invalid tool name ---
cat > "$FIXTURE/.claude/agents/bad-agent-invalid-tools/agent.yml" << 'EOF'
name: bad-agent-invalid-tools
description: "An agent with an invalid tool name."
tools: Read, InvalidTool, Write
EOF

# --- Standards index ---
# STD-01: test/missing.md does not exist
# STD-02: test/absolute has an absolute path entry
cat > "$FIXTURE/malte/standards/index.yml" << 'EOF'
standards:
  test/good:
    description: "Good standard"
    triggers:
      - test
    path: "test/good.md"
  test/missing:
    description: "Missing file"
    triggers:
      - missing
    path: "test/missing.md"
  test/absolute:
    description: "Absolute path entry"
    triggers:
      - absolute
    path: "/etc/absolute.md"
EOF

mkdir -p "$FIXTURE/malte/standards/test"
cat > "$FIXTURE/malte/standards/test/good.md" << 'EOF'
# Good Standard

## Overview

A test standard.
EOF

# ---------------------------------------------------------------------------
# Run scanner against fixture
# ---------------------------------------------------------------------------
set +e
output=$(bash "$ENTROPY_SCAN" --dir "$FIXTURE" 2>&1)
exit_code=$?
set -e

# ---------------------------------------------------------------------------
# Test 1: Script exits 1 (violations found)
# ---------------------------------------------------------------------------
if [[ $exit_code -eq 1 ]]; then
    pass "exit code 1 when violations exist"
else
    fail "expected exit 1 (violations), got exit $exit_code — output: $output"
fi

# ---------------------------------------------------------------------------
# Test 2: SKILL-01 — missing SKILL.md detected
# ---------------------------------------------------------------------------
if echo "$output" | grep -q "VIOLATION \[SKILL-01\].*bad-skill-no-md"; then
    pass "SKILL-01 detected: missing SKILL.md"
else
    fail "SKILL-01 not detected for bad-skill-no-md"
fi

# ---------------------------------------------------------------------------
# Test 3: SKILL-01 — no false positive for good-skill
# ---------------------------------------------------------------------------
if echo "$output" | grep -q "VIOLATION \[SKILL-01\].*good-skill"; then
    fail "SKILL-01 false positive for good-skill (has SKILL.md)"
else
    pass "SKILL-01 no false positive for good-skill"
fi

# ---------------------------------------------------------------------------
# Test 4: SKILL-02 — short description detected
# ---------------------------------------------------------------------------
if echo "$output" | grep -q "VIOLATION \[SKILL-02\].*bad-skill-desc"; then
    pass "SKILL-02 detected: description too short"
else
    fail "SKILL-02 not detected for bad-skill-desc"
fi

# ---------------------------------------------------------------------------
# Test 5: SKILL-03 — missing Overview section
# ---------------------------------------------------------------------------
if echo "$output" | grep -q "VIOLATION \[SKILL-03\].*bad-skill-sections.*Overview"; then
    pass "SKILL-03 detected: missing Overview section"
else
    fail "SKILL-03 not detected for bad-skill-sections (missing Overview)"
fi

# ---------------------------------------------------------------------------
# Test 6: SKILL-05 — stray file at top level
# ---------------------------------------------------------------------------
if echo "$output" | grep -q "VIOLATION \[SKILL-05\].*stderr.log"; then
    pass "SKILL-05 detected: stray log file"
else
    fail "SKILL-05 not detected for stderr.log in bad-skill-stray"
fi

# ---------------------------------------------------------------------------
# Test 7: HOOK-01 — missing exit-code comment block
# ---------------------------------------------------------------------------
if echo "$output" | grep -q "VIOLATION \[HOOK-01\].*bad-hook"; then
    pass "HOOK-01 detected: missing exit-code comment block"
else
    fail "HOOK-01 not detected for bad-hook.sh"
fi

# ---------------------------------------------------------------------------
# Test 8: HOOK-02 — missing set -euo pipefail
# ---------------------------------------------------------------------------
if echo "$output" | grep -q "VIOLATION \[HOOK-02\].*bad-hook"; then
    pass "HOOK-02 detected: missing set -euo pipefail"
else
    fail "HOOK-02 not detected for bad-hook.sh"
fi

# ---------------------------------------------------------------------------
# Test 9: HOOK-03 — non-standard stdin pattern (read vs INPUT=$(cat))
# ---------------------------------------------------------------------------
if echo "$output" | grep -q "VIOLATION \[HOOK-03\].*bad-hook"; then
    pass "HOOK-03 detected: non-standard stdin in bad-hook.sh"
else
    fail "HOOK-03 not detected for bad-hook.sh (uses read instead of INPUT=\$(cat))"
fi

# ---------------------------------------------------------------------------
# Test 10: AGENT-02 — missing tools field
# ---------------------------------------------------------------------------
if echo "$output" | grep -q "VIOLATION \[AGENT-02\].*bad-agent-no-tools.*tools"; then
    pass "AGENT-02 detected: missing tools field"
else
    fail "AGENT-02 not detected for bad-agent-no-tools"
fi

# ---------------------------------------------------------------------------
# Test 11: AGENT-03 — invalid tool name
# ---------------------------------------------------------------------------
if echo "$output" | grep -q "VIOLATION \[AGENT-03\].*bad-agent-invalid-tools.*InvalidTool"; then
    pass "AGENT-03 detected: invalid tool name 'InvalidTool'"
else
    fail "AGENT-03 not detected for bad-agent-invalid-tools"
fi

# ---------------------------------------------------------------------------
# Test 12: STD-01 — missing standard file
# ---------------------------------------------------------------------------
if echo "$output" | grep -q "VIOLATION \[STD-01\].*test/missing.md"; then
    pass "STD-01 detected: missing standard file"
else
    fail "STD-01 not detected for missing test/missing.md"
fi

# ---------------------------------------------------------------------------
# Test 13: STD-02 — absolute path in index.yml
# ---------------------------------------------------------------------------
if echo "$output" | grep -q "VIOLATION \[STD-02\].*absolute"; then
    pass "STD-02 detected: absolute path in standards index"
else
    fail "STD-02 not detected for absolute path /etc/absolute.md"
fi

# ---------------------------------------------------------------------------
# Test 14: All violation lines include FIX: instructions
# ---------------------------------------------------------------------------
violation_count=$(echo "$output" | grep -c "^VIOLATION \[" || true)
fix_count=$(echo "$output" | grep "^VIOLATION \[" | grep -c "FIX:" || true)
if [[ $violation_count -gt 0 && $violation_count -eq $fix_count ]]; then
    pass "All $violation_count violations include FIX: instructions"
else
    fail "Mismatch: $violation_count violations but $fix_count have FIX: instructions"
fi

# ---------------------------------------------------------------------------
# Test 15: Clean harness exits 0
# ---------------------------------------------------------------------------
cat > "$CLEAN/SKILL.md" << 'EOF'
# placeholder — not a skill dir
EOF
mkdir -p "$CLEAN/malte/skills/clean-skill"
cat > "$CLEAN/malte/skills/clean-skill/SKILL.md" << 'EOF'
---
name: clean-skill
description: >-
  A perfectly valid skill with correct frontmatter and all required sections present.
  Use when validating the entropy-scan harness checker. Triggers on: clean skill, valid skill,
  test harness, entropy scanner validation.
---

# Clean Skill

## Overview

A reference skill for clean-harness testing.

## When to Use

- "clean skill"

## Resources

None.

## Out of Scope

Nothing.
EOF

set +e
clean_output=$(bash "$ENTROPY_SCAN" --dir "$CLEAN" 2>&1)
clean_exit=$?
set -e
if [[ $clean_exit -eq 0 ]]; then
    pass "clean harness exits 0"
else
    fail "clean harness should exit 0, got $clean_exit. Output: $clean_output"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ $FAIL -eq 0 ]]
