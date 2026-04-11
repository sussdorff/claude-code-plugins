---
name: project-health
model: sonnet
description: >-
  Run a quick quality assessment on a project and produce a traffic-light
  scorecard. Triggers on: project health, projekt check, health check, project
  quality, wie gesund ist das projekt, code health check.
---

# Project Health

Assess a project's quality across tests, linting, type safety, dependency security, git hygiene, and documentation. Produces a Markdown table with 🟢/🟡/🔴 traffic lights and an overall score (up to 8 categories for Python/TypeScript, 3 for generic projects).

## Overview

Project Health runs a read-only quality assessment for any project and reports a traffic-light scorecard. It auto-detects project type (Python, TypeScript, generic), runs the appropriate tool checks, evaluates universal checks (git hygiene, beads backlog, CLAUDE.md), and — for harness repositories — runs the entropy-scan invariant checker. Results are shown as a single Markdown table; no files are modified.

## When to Use

- "project health" / "health check" / "projekt check"
- "how healthy is this project?" / "code health check"
- "wie gesund ist das projekt?" / "project quality"

## Workflow

### 1. Detect Project Type

Identify type from file presence in the project root:
- `pyproject.toml` or `setup.py` → **python**
- `package.json` or `tsconfig.json` → **typescript**
- neither → **generic**

### 2. Load Thresholds

Check for `.project-health.yml` in the project root. Use those values where present; fall back to defaults for any missing keys.

Default thresholds:
- Coverage: green ≥ 80%, yellow ≥ 60%, red < 60%
- Issues count: green = 0, yellow ≥ 1, red ≥ 10

### 3. Run Type-Specific Checks

<investigation>
Run all checks silently. Capture output. Do not report partial results yet.
</investigation>

**Python checks** (skip any tool not installed — mark 🟡 not available):

```bash
uv run pytest --tb=no -q 2>&1          # test pass/fail count
uv run ruff check . --output-format=concise 2>&1  # lint error count
uv run mypy . --ignore-missing-imports --no-error-summary 2>&1  # type error count
uv run pip-audit -f json 2>&1           # CVE count
uv run pytest --cov --cov-report=term-missing -q 2>&1  # coverage %
```

**TypeScript checks** (skip any tool not installed — mark 🟡 not available):

```bash
npx jest --passWithNoTests 2>&1         # test fail count
npx vitest run 2>&1                     # alternative test runner
npx eslint . --format=compact 2>&1      # lint error count
npx tsc --noEmit 2>&1                   # type error count
npm audit --json 2>&1                   # critical+high vulnerability count
```

See `references/checks.md` for exact parsing instructions per tool.

### 4. Run Universal Checks

Run these for all project types:

```bash
git status --porcelain | wc -l          # uncommitted file count
git for-each-ref --format='%(refname:short) %(committerdate:relative)' refs/heads/  # stale branches
git fetch --dry-run 2>&1               # diverged remote
```

**Beads backlog** (only if `.beads/` exists):

```bash
if [ -d .beads ]; then
  bd dolt start 2>/dev/null
  bd list --status=open 2>/dev/null | wc -l
  bd list --status=blocked 2>/dev/null | wc -l
fi
```

**CLAUDE.md completeness**: check file exists, contains an Overview/project description, and contains a Commands section with at least one command.

**Harness check** (only if `malte/skills/` or `.claude/agents/` exists — harness repository):

```bash
if [[ -d malte/skills ]] || [[ -d .claude/agents ]]; then
  # Run entropy-scan script if present
  if [ -f malte/skills/entropy-scan/scripts/entropy-scan.sh ]; then
    entropy_output=$(bash malte/skills/entropy-scan/scripts/entropy-scan.sh 2>&1)
    entropy_exit=$?
    if [[ $entropy_exit -eq 2 ]]; then
      # Script error — score as red with error note
      violation_count="error"
    else
      violation_count=$(echo "$entropy_output" | grep -c "VIOLATION \[" 2>/dev/null || echo 0)
    fi
  else
    violation_count=0
  fi

  if [[ "$violation_count" == "error" ]]; then
    harness_status="🔴"
    harness_detail="entropy-scan script error"
  elif [[ $violation_count -eq 0 ]]; then
    harness_status="🟢"
    harness_detail="0 violations"
  elif [[ $violation_count -le 5 ]]; then
    harness_status="🟡"
    harness_detail="$violation_count violation(s)"
  else
    harness_status="🔴"
    harness_detail="$violation_count violations"
  fi
fi
```

### 5. Score Each Check

Apply scoring using these rules:

| Check | Green | Yellow | Red |
|-------|-------|--------|-----|
| Test pass rate | 100% | ≥ 90% | < 90% |
| Lint errors | 0 | 1–9 | ≥ 10 |
| Type errors | 0 | 1–9 | ≥ 10 |
| CVEs / vulns | 0 | 1–4 | ≥ 5 |
| Coverage | ≥ 80% | ≥ 60% | < 60% |
| Git hygiene | clean | minor dirt | diverged/stale |
| Beads backlog | ≤ 5 open, 0 blocked | 6–15 or 1–2 blocked | 16+ or 3+ blocked |
| CLAUDE.md | all sections | partial | absent |
| Harness | 0 violations | 1–5 violations | 6+ violations |

Custom thresholds in `.project-health.yml` override the defaults for coverage and issues count rows.

### 6. Output Scorecard

```markdown
## Project Health — {project_name}
Checked: {ISO timestamp} | Type: {python|typescript|generic}

| Category | Check | Status | Detail |
|----------|-------|--------|--------|
| Python | pytest | 🟢 | 142/142 passed |
| Python | ruff | 🟢 | 0 errors |
| Python | mypy | 🟡 | 3 type errors |
| Python | pip-audit | 🟢 | 0 CVEs |
| Python | coverage | 🔴 | 42% (threshold: 80%) |
| Universal | git hygiene | 🟢 | clean, no stale branches |
| Universal | beads backlog | 🟡 | 8 open, 1 blocked |
| Universal | CLAUDE.md | 🟢 | all required sections present |

**Overall: 6/8 🟡**
```

Overall emoji:
- Strict majority green → 🟢
- More yellow/red or majority yellow → 🟡
- More red than yellow → 🔴

After the table, add a **Top Issues** list (max 3 items) — only the red and yellow findings worth acting on first.

## Do NOT

- Run checks that modify the project (e.g., `ruff --fix`, `npm audit fix`)
- Push or commit anything
- Block on a missing tool — mark it yellow and continue
- Report partial results mid-check — complete all checks first, then output once
- Invoke `bd dolt start` unless `.beads/` is present

## Resources

- `references/checks.md` — Tool commands, parsing rules, threshold details, graceful degradation

## Out of Scope

- Fixing the issues found (report only)
- Security remediation (flag for human review)
- Performance profiling
- Dependency upgrade decisions
