#!/usr/bin/env bats
# Tests for measure-context.sh
# AK1: Script runs and logs results to structured output
# AK2: Tracks per-session overhead by category
# AK3: Outputs ranked list of heaviest contributors

SCRIPT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)/scripts/measure-context.sh"
FIXTURES="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)/fixtures"

# ── AK1: Structured output ─────────────────────────────────────────────────

@test "script exists and is executable" {
  [ -x "$SCRIPT" ]
}

@test "script exits 0 with --help" {
  run "$SCRIPT" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"Usage"* ]]
}

@test "script produces a Summary section" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --window 200000
  [ "$status" -eq 0 ]
  [[ "$output" == *"Summary"* ]]
}

@test "output contains context window percentage" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --window 200000
  [ "$status" -eq 0 ]
  [[ "$output" == *"200,000"* ]] || [[ "$output" == *"200000"* ]] || [[ "$output" == *"200.000"* ]]
  [[ "$output" == *"%"* ]]
}

# ── AK2: Per-category overhead ─────────────────────────────────────────────

@test "output contains By Category table header" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --window 200000
  [ "$status" -eq 0 ]
  [[ "$output" == *"By Category"* ]]
}

@test "output lists Skills category" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --window 200000
  [ "$status" -eq 0 ]
  [[ "$output" == *"Skills"* ]]
}

@test "output lists Agents category" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --window 200000
  [ "$status" -eq 0 ]
  [[ "$output" == *"Agents"* ]]
}

@test "output lists CLAUDE.md category" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --window 200000
  [ "$status" -eq 0 ]
  [[ "$output" == *"CLAUDE.md"* ]]
}

@test "output lists MCP category" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --window 200000
  [ "$status" -eq 0 ]
  [[ "$output" == *"MCP"* ]]
}

@test "category tokens are numeric" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --window 200000
  [ "$status" -eq 0 ]
  # Check that Skills row has a number in it
  skills_line=$(echo "$output" | grep "Skills" | head -1)
  [[ "$skills_line" =~ [0-9]+ ]]
}

# ── AK3: Ranked contributors ───────────────────────────────────────────────

@test "output contains Ranked Contributors section" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --window 200000
  [ "$status" -eq 0 ]
  [[ "$output" == *"Ranked Contributors"* ]]
}

@test "ranked list includes fixture skill name" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --window 200000
  [ "$status" -eq 0 ]
  [[ "$output" == *"my-skill"* ]]
}

@test "ranked list includes fixture agent name" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --window 200000
  [ "$status" -eq 0 ]
  [[ "$output" == *"test-agent"* ]]
}

@test "ranked list is sorted descending by tokens" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --window 200000
  [ "$status" -eq 0 ]
  # Extract numbers from ranked lines; first should be >= last
  ranked_section=$(echo "$output" | awk '/Ranked Contributors/,0')
  first_tokens=$(echo "$ranked_section" | grep -E '^\|[[:space:]]+[0-9]' | head -1 | grep -oE '[0-9]+' | sed -n '3p')
  last_tokens=$(echo "$ranked_section" | grep -E '^\|[[:space:]]+[0-9]' | tail -1 | grep -oE '[0-9]+' | sed -n '3p')
  [ -n "$first_tokens" ]
  [ -n "$last_tokens" ]
  [ "$first_tokens" -ge "$last_tokens" ]
}

# ── Format flags ───────────────────────────────────────────────────────────

@test "--format=json produces valid JSON" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --format json \
    --window 200000
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c "import sys,json; json.load(sys.stdin)"
}

@test "--format=json output has categories key" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --format json \
    --window 200000
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'categories' in d, 'missing categories key'"
}

@test "--format=json output has contributors key" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --format json \
    --window 200000
  [ "$status" -eq 0 ]
  echo "$output" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'contributors' in d, 'missing contributors key'"
}

# ── Category filter ────────────────────────────────────────────────────────

@test "--category=skills only shows skills output" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --category skills \
    --window 200000
  [ "$status" -eq 0 ]
  [[ "$output" == *"my-skill"* ]]
}

# ── Budget warnings ────────────────────────────────────────────────────────

@test "output contains Budget Warnings section" {
  run "$SCRIPT" \
    --skills-dir "$FIXTURES/skills" \
    --agents-dir "$FIXTURES/agents" \
    --claude-md "$FIXTURES/claude-md/CLAUDE.md" \
    --mcp-config /dev/null \
    --window 200000
  [ "$status" -eq 0 ]
  [[ "$output" == *"Budget"* ]]
}
