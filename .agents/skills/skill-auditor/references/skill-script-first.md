# Skill Script-First Rule

Executable workflow logic belongs in bundled scripts, not in `SKILL.md` body.
This document explains the rule, what counts as a violation, allowed exceptions,
and how to use `validate-skill.py` to check compliance.

## The Rule

A `SKILL.md` body is a **system prompt**, not an executable notebook. It must
contain only:

- Agent instructions expressed in imperative prose
- References to bundled scripts via `$SCRIPT` or explicit paths
- Short illustrative one-liners that demonstrate a concept

Whenever a skill body contains executable logic that can be mechanically run —
whether as a fenced code block or as a prose description of a step-by-step
tool-call sequence — that logic must move to a script in `scripts/`.

**Why?** Skills are loaded into every agent invocation as context tokens.
Inline code bloats the skill beyond its informational purpose, degrades token
efficiency, and makes it harder for agents to distinguish "what I must decide"
from "what a script already does deterministically."

## What Counts as EXTRACTABLE_CODE

### BLOCKING Violations

These must be fixed before a skill ships:

**Large shell block** — a fenced `` ```bash `` / `` ```sh `` / `` ```zsh `` block with
more than 5 real lines of executable code (comments and blank lines excluded).

**Large python block** — a fenced `` ```python `` block with more than 3 real lines
of executable code.

### ADVISORY Violations

These should be fixed but do not hard-block:

**Shell pipeline** — any shell block that contains 3 or more pipeline markers
(pipe characters `|`, command substitution `$(`, `grep`, `jq`, `sed`, `awk`,
`sqlite3`, `cmux`, `python -c`, `2>&1`). Even a single line like
`find . | grep skill | head -10` is an advisory violation — it belongs in a
script so it can be tested, versioned, and replaced without re-reading the skill.

**Verbal multi-step pipeline** — an ordered list with 4 or more consecutive
items where each item contains at least one tool/action keyword (`bash`, `python`,
`run`, `grep`, `query`, `search`, `parse`, `store`, `call`, `execute`, `scan`,
`read`, `write`, `check`, `send`). This is the prose equivalent of embedded code.
Example:
```
1. Run scan-skills.sh to search for all skills.     ← tool keyword: run, search
2. Parse the output and grep for BLOCKING findings. ← tool keyword: parse, grep
3. Query the database for previously reviewed items.← tool keyword: query
4. Call the auditor agent with the result.          ← tool keyword: call
```
This 4-step list should become a single `$SCRIPT` call that encapsulates steps 1–3,
with the agent making the judgment call in step 4.

**Inline `python -c`** — any inline `python3 -c "..."` or `uv run python -c "..."`
invocation. Extract to a named script.

## Allowed Exceptions

The validator does **not** flag:

1. **Files under `references/`** — these are documentation, not active skill body.
   Illustrative snippets in reference files are allowed regardless of length.

2. **Single-command examples** (≤ 1 real line, no pipeline markers) — for example:
   ```bash
   bd show CCP-123
   ```
   This is a usage illustration, not executable workflow logic.

3. **Pure comment blocks** — lines starting with `#` are not counted toward the
   real-line threshold.

## How to Use validate-skill.py

Run against a skill directory or directly against a `SKILL.md` file:

```bash
# Check a skill by directory
python3 meta/skills/skill-auditor/scripts/validate-skill.py meta/skills/my-skill/

# Check a specific SKILL.md file
python3 meta/skills/skill-auditor/scripts/validate-skill.py meta/skills/my-skill/SKILL.md

# Strict mode: advisory findings also fail (exit 1)
python3 meta/skills/skill-auditor/scripts/validate-skill.py meta/skills/my-skill/ --strict
```

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | No findings (or advisory-only in non-strict mode) |
| `1` | BLOCKING finding present (or any finding in `--strict` mode) |
| `2` | File not found / parse error |

**Example output:**

```
EXTRACTABLE_CODE [BLOCKING]: Extractable executable code: 8-line shell block in skill body
    → Move to scripts/<name>.sh and use core/contracts/execution-result.schema.json for multi-field outputs
EXTRACTABLE_CODE [ADVISORY]: Verbal multi-step pipeline detected: ordered list with 4+ items containing tool/action keywords
    → Consider extracting to scripts/<name>.sh
```

## When to Use JSON Output Contract vs Bare Value

When extracting logic to a script, choose the output format based on complexity:

**Bare value** — the script prints a single string to stdout (a path, a count,
a UUID). The calling agent captures it directly. No envelope needed.

**JSON envelope** — use `core/contracts/execution-result.schema.json` when:
- The script produces multiple fields the agent needs to inspect separately
- The script has meaningful failure modes the agent must distinguish
  (`ok` vs `warning` vs `error`)

Minimal valid shape:
```json
{"status": "ok", "summary": "one sentence", "data": {}, "errors": [], "next_steps": [], "open_items": [], "meta": {}}
```

The agent checks `status` without parsing free-form text, eliminating
"run this, check if output is empty, run that" verbal pipelines in the skill.

See `core/contracts/execution-result.schema.json` for the full schema and field
definitions.

## Skill Creation Checklist

When creating a new skill:
1. Draft `SKILL.md` with frontmatter and body — keep executable logic OUT of the body.
2. Run `validate-skill.py` before first commit: `python3 meta/skills/skill-auditor/scripts/validate-skill.py <skill-dir>`
3. Fix any BLOCKING findings by extracting logic to `scripts/`.
4. Commit only when validator exits 0 (or exit 0 with advisory-only findings if acceptable).

## Wiring into Skill Authoring

When creating a new skill or rewriting an existing one:

1. Draft the `SKILL.md` body with prose instructions.
2. Run `validate-skill.py` on the draft.
3. For each BLOCKING finding, extract the code to `scripts/<name>.sh` (or `.py`).
4. Replace the code block with a `$SCRIPT` reference and describe the expected output.
5. For ADVISORY findings, evaluate whether the pipeline belongs in a script
   or is genuinely a single-step illustration.
6. Re-run `validate-skill.py` until exit 0.

The `meta:skill-auditor` skill dispatches validate-skill.py as part of its
Improve Mode workflow — it runs the validator after every rewrite to confirm
no EXTRACTABLE_CODE remains.
