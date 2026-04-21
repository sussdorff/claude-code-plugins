# Project Health — Check Definitions and Thresholds

## Default Thresholds

```yaml
coverage:
  green: 80   # >= 80% → green
  yellow: 60  # >= 60% → yellow; below → red

issues:
  yellow: 1   # >= 1 issue → yellow
  red: 10     # >= 10 issues → red
```

Override per-project by creating `.project-health.yml` in the project root with any subset of these keys.

## Python Checks

| Check | Command | Metric | Notes |
|-------|---------|--------|-------|
| pytest | `uv run pytest --tb=no -q` | pass/fail count | Count failures for `score_issues_count` |
| ruff | `ruff check . --output-format=concise` | error count | Count lines starting with a path |
| mypy | `mypy . --ignore-missing-imports --no-error-summary` | error count | Count lines ending with `error:` |
| pip-audit | `pip-audit -f json` | CVE count | Parse `results[].vulnerabilities` count |
| coverage | `coverage report --format=total` or pytest-cov `--cov --cov-report=term-missing` | % integer | Parse last line or `TOTAL` row |

### Python Tool Availability

Check with `which <tool>` or `uv run <tool> --version`. If unavailable, mark status `🟡 not available`.

For projects using `uv`, prefer `uv run pytest`, `uv run ruff`, `uv run mypy`, `uv run pip-audit`.

## TypeScript Checks

| Check | Command | Metric | Notes |
|-------|---------|--------|-------|
| jest | `npx jest --passWithNoTests 2>&1` | fail count | Count `FAIL` lines |
| vitest | `npx vitest run --reporter=verbose 2>&1` | fail count | Count `FAIL` lines |
| eslint | `npx eslint . --format=compact 2>&1` | error count | Count lines with `Error -` |
| tsc | `npx tsc --noEmit 2>&1` | error count | Count lines with `error TS` |
| npm audit | `npm audit --json` | critical+high count | Parse `.metadata.vulnerabilities.critical + .high` |

### TypeScript Test Runner Detection

Check `package.json` `scripts` and `devDependencies`:
- `vitest` in deps → use vitest
- `jest` in deps → use jest
- Neither → mark as `🟡 not configured`

## Universal Checks (All Project Types)

### Git Hygiene

```bash
# Uncommitted changes
git status --porcelain | wc -l

# Stale branches (>30 days since last commit)
git for-each-ref --format='%(refname:short) %(committerdate:unix)' refs/heads/ | \
  awk -v cutoff="$(date -d '30 days ago' +%s)" '$2 < cutoff {print $1}'

# Diverged remote
git fetch --dry-run 2>&1 | grep -c "would fetch"
# OR: git status -sb | grep "ahead\|behind"
```

Scoring:
- `git status` clean + no stale branches + not diverged → 🟢
- 1–5 uncommitted files OR stale branches present → 🟡
- 6+ uncommitted files OR diverged remote → 🔴

### Beads Backlog Health

Only run if `.beads/` directory exists.

```bash
bd list --status=open 2>/dev/null | wc -l
bd list --status=blocked 2>/dev/null | wc -l
```

Scoring (open beads count):
- 0–5 open, 0 blocked → 🟢
- 6–15 open OR any blocked → 🟡
- 16+ open OR 3+ blocked → 🔴

If `.beads/` absent: skip (mark as `🟡 no beads`).

### CLAUDE.md Completeness

```bash
test -f CLAUDE.md && echo exists
grep -c "## " CLAUDE.md  # section count
grep -l "Commands\|commands" CLAUDE.md
grep -l "Overview\|overview" CLAUDE.md
```

Scoring:
- File exists + has Overview section + has Commands section → 🟢
- File exists but missing one required section → 🟡
- File absent → 🔴

Required sections: `Overview` (or `# ProjectName` + description), `Commands` (with at least one runnable command).

### Harness Invariants Check

Only run if `malte/skills/` or `.claude/agents/` exists (harness repository).

```bash
# Check if this is a harness repo
if [[ -d malte/skills ]] || [[ -d .claude/agents ]]; then
  # Run entropy-scan script if present; falls back to 0 violations if not installed
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

Scoring (violation count):
- 0 violations → 🟢
- 1–5 violations → 🟡
- 6+ violations → 🔴

If not a harness repo: skip (mark as `🟡 not a harness repository`).

**Validation:** The entropy-scan skill validates the complete harness state:
- **Skills invariants:** SKILL-01 through SKILL-04 (directory structure, frontmatter, section order, line count)
- **Hooks invariants:** HOOK-01 through HOOK-04 (exit code documentation, error handling, stdin pattern, exit codes)
- **Agents invariants:** AGENT-01 through AGENT-04 (directory structure, required fields, tool validity, optional fields)
- **Standards invariants:** STD-01 through STD-04 (file references, path format, trigger lists, structure)

Reference: `docs/HARNESS_SPEC.md` for complete invariant definitions.

## Threshold Override File

Create `.project-health.yml` in the project root:

```yaml
# .project-health.yml — custom thresholds for this project
coverage:
  green: 90   # require 90% for green (default: 80)
  yellow: 75  # require 75% for yellow (default: 60)

issues:
  yellow: 1   # 1+ issues → yellow (default: 1)
  red: 5      # 5+ issues → red (default: 10) — stricter than default
```

All keys are optional — missing keys fall back to defaults. The file is loaded by `malte/skills/project_health/scoring.py:load_thresholds()`.

> **Threshold semantics for `issues`:** Scoring uses `>=` comparisons — `count >= red` → red, `count >= yellow` → yellow, else green. Setting `yellow: 0` makes green unreachable (0 issues still scores yellow). This is intentional for strict zero-tolerance projects but should be used knowingly.

## Configurable Per Project Type

"Configurable per project type" means two distinct things:

**1. Project type detection selects a different fixed checklist.**

The detected project type (`python`, `typescript`, or `generic`) determines which tool checks are run. Python projects run pytest/ruff/mypy/pip-audit/coverage; TypeScript projects run jest/vitest/eslint/tsc/npm-audit; generic projects run only the Universal checks. This selection is automatic and not user-tunable.

**2. Thresholds in `.project-health.yml` are the user-tunable knobs.**

Any numeric threshold used for scoring can be overridden per project by creating a `.project-health.yml` file in the project root. Missing keys fall back to defaults.

Example with per-project threshold overrides:

```yaml
# .project-health.yml — stricter thresholds for a production API
coverage:
  green: 90   # require 90% coverage for green (default: 80)
  yellow: 75  # require 75% for yellow (default: 60)

issues:
  yellow: 1   # 1+ issues → yellow (unchanged from default)
  red: 3      # 3+ issues → red (stricter than default: 10)
```

> **Note:** Setting `yellow: 0` for issues makes green unreachable since `0 >= 0` is always true. Use `yellow: 1` (default) for the standard "zero issues is green" behaviour. Only set `yellow: 0` deliberately when you want every run to show at least yellow regardless of issue count.

The checklist itself (which tools to run) is fixed by project type and cannot be changed via `.project-health.yml`. Only thresholds are configurable.

## Output Table Format

```markdown
## Project Health — {project_name}
Checked: {timestamp} | Type: {python|typescript|generic}

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

## Graceful Degradation

When a tool is not installed or the command fails with a non-results error:
- Mark the row: `🟡 not available — install <tool>`
- Continue with remaining checks
- Count `not available` rows as yellow for overall score

Never abort the entire health check because one tool is missing.
