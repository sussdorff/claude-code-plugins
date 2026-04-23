---
name: stringer
description: stringer — Codebase archaeology and tech debt scanning
---
# stringer — Codebase archaeology and tech debt scanning

Scan a repository for tech debt signals, generate agent onboarding context, or view a health dashboard using the `stringer` CLI. Signals can be imported directly into beads for tracking.

Optional: Eingabeargumente (z.B. `scan`, `scan --full`, `context`, `docs`, `init`, oder beliebige stringer-Flags)

## Pre-flight

1. Check if `stringer` is installed:
   ```bash
   command -v stringer
   ```
   If not found, tell the user: `brew install davetashner/tap/stringer` and stop.

2. Unless mode is `init`, check if `.stringer/` exists in the target directory:
   ```bash
   ls -d .stringer/ 2>/dev/null
   ```
   If not found, suggest running `stringer init` first. Ask the user whether to proceed without config or init first.

## Mode Detection

Parse the provided input arguments to determine the mode. Any flags not consumed by mode detection are passed through to the stringer command.

| Args pattern | Mode |
|---|---|
| (empty / no args) | `report` |
| `scan --full [flags]` | `scan-full` |
| `scan [flags]` | `scan-delta` |
| `context [flags]` | `context` |
| `docs [flags]` | `docs` |
| `init` | `init` |

## Mode: report (default)

```bash
stringer report .
```

Display the output directly — it's a human-readable health dashboard. No further action needed.

## Mode: scan-delta

Run a delta scan (only new signals since last baseline):

```bash
stringer scan . --delta --format=beads $EXTRA_FLAGS
```

**Important:** Do NOT pipe directly to `bd import`. Instead:

1. Capture output to a temp file
2. Count signals and summarize top categories:
   ```bash
   stringer scan . --delta --dry-run $EXTRA_FLAGS
   ```
3. Show the user: "Found X signals (Y todos, Z complexity, ...). Import to beads?"
4. Only after confirmation:
   ```bash
   stringer scan . --delta --format=beads $EXTRA_FLAGS | bd import -i -
   ```

## Mode: scan-full

Same as scan-delta but without `--delta`:

```bash
stringer scan . --format=beads $EXTRA_FLAGS
```

Follow the same confirm-before-import pattern as scan-delta. Warn the user that a full scan may produce many signals — suggest `--delta` if a baseline exists.

## Mode: context

Generate a CONTEXT.md for agent onboarding:

```bash
stringer context . $EXTRA_FLAGS
```

If `CONTEXT.md` already exists in the target directory, ask before overwriting. The user can redirect with `-o <path>` if preferred.

Display a brief summary of what was generated.

## Mode: docs

Generate an AGENTS.md scaffold:

```bash
stringer docs . $EXTRA_FLAGS
```

If `AGENTS.md` already exists, use `--update` to preserve manual sections:

```bash
stringer docs . --update $EXTRA_FLAGS
```

## Mode: init

Bootstrap stringer in the repository:

```bash
stringer init .
```

After init, create a baseline from current signals so future `--delta` scans only show new issues:

```bash
stringer baseline create .
```

Tell the user: "stringer initialized. `.stringer/` created with baseline. Future `stringer scan` will only show new signals."

## Useful Flag Combinations

These can be appended to any scan mode:

- `--collectors=complexity,todos` — focus on specific signal types
- `--min-confidence=0.8` — filter low-confidence signals
- `--paths=src/` — restrict to specific directories
- `--infer-priority` — let LLM assign P1-P4 priorities
- `--max-issues=20` — cap output count
- `--format=markdown` — human-readable scan output instead of beads JSONL

## Available Collectors

For reference when the user asks what can be scanned:

apidrift, complexity, configdrift, coupling, deadcode, dephealth, docstale, duplication, github, githygiene, gitlog, lotteryrisk, patterns, todos, vuln
