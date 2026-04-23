# Python Default — Bash by Exception

> **Scope**: claude-code-plugins — applies to all scripts under `scripts/`, `skills/*/scripts/`, `agents/*/scripts/`, and any helper invoked by skills, agents, hooks, or CI.

**Python is the default language for scripts.** Bash is allowed only when one of the listed exceptions applies. This rule supersedes any historical preference for Bash as a "glue" or "orchestration" language.

## Why

The apparent advantages of Bash for orchestration are mostly habit, not engineering. When examined:

| Claimed Bash strength | Reality |
|---|---|
| "Shell-zentrisch" (cmux, tmux, bd) | CLIs are language-agnostic. `subprocess.run(["cmux", "send", ...])` is identical. |
| Timeout / signal handling | `subprocess.run(timeout=...)` + `signal` are more robust and cross-platform than `gtimeout`/`timeout` drift between macOS and Linux. |
| JSON handling with `jq` | Tolerable for flat reads; stdlib `json` wins as soon as fields are optional or nested. |
| `set -euo pipefail` | Brittle — subshells, `\|\|` chains, and pipe exit codes mis-behave. Python exceptions are clearer. |
| Testability | bats vs pytest — pytest wins. |
| Portability | macOS bash 3.2 vs Linux bash 5 is a real bug source. Python 3.11+ is stable. |

In addition, Python scripts slot into the existing canonical homes (`beads-workflow/lib/orchestrator/`, `core/contracts/`) and can be covered by `pytest`, type-checked, and re-used as importable modules inside one plugin.

## Allowed Bash exceptions

Bash is permitted **only** when one of these applies:

1. **The script manipulates the shell environment itself** — writing to `~/.zshrc`, `~/.bashrc`, PATH shims, shell completions. Bash is the target, not the tool. Examples: `install-bd-wrapper.sh`, activation/init scripts.
2. **The script is invoked by the shell loader as a hook/completion** — e.g. a bd `command-not-found` hook, a shell-function override, or a completion script that must source correctly.
3. **Trivial glue** — ≤10 real lines, no structured data (JSON/YAML), no control flow beyond a single `||`/`&&`, no external-process parsing.

If your script does not match (1), (2), or (3): **write it in Python.**

## Corollaries

- **No `python3 - <<PYEOF` heredocs inside Bash scripts.** If Python logic is needed, the whole script should be Python. Heredoc-embedded Python is a BLOCKING finding.
- **Bash wrappers around external binaries (e.g. Codex, timeout, cmux) are not automatically justified.** `subprocess.run([...], timeout=...)` in Python replaces them; use Bash only when one of the three exceptions above applies.
- **No cross-plugin Python imports.** Shared code lives inside one plugin (`beads-workflow/lib/orchestrator/` etc.). Contracts cross plugin boundaries via `core/contracts/` schemas; helpers do not. See the plugin-sharing boundary rule.

## Canonical Python homes

| Logic type | Home |
|---|---|
| Orchestrator / workflow / metrics / parsing | `beads-workflow/lib/orchestrator/` (module) + thin CLI wrapper in `beads-workflow/scripts/` |
| Cross-script contracts (schemas only) | `core/contracts/` |
| Plugin-internal helpers | `<plugin>/lib/` or `<plugin>/scripts/` |
| Skill-local helpers | `<skill>/scripts/` |

## Script template

Python default (PEP 723 when external deps, plain `python3` for stdlib):

```python
#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = ["pyyaml>=6.0"]
# ///
"""Short description."""
```

or

```python
#!/usr/bin/env python3
"""Short description — stdlib only."""
```

## Enforcement

- **Reactive**: `meta/skills/skill-auditor/scripts/validate-skill.py` flags heredoc-Python-in-Bash and shell blocks that exceed the Script-First thresholds.
- **Review**: New `.sh` files must be justified in the commit message or PR description by referencing exception (1), (2), or (3) above. Otherwise they should be Python.
- **Refactor**: Existing Bash scripts that do not match an exception are tech debt and should be migrated.

## Related standards

- `dev-tools/script-first-rule` — where executable logic lives (scripts, not markdown bodies)
- `dev-tools/execution-result-envelope` — multi-field structured output contract
