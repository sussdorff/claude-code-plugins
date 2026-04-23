# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd prime` for full workflow context.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work atomically
bd close <id>         # Complete work
bd dolt push          # Push beads data to remote
```

## Non-Interactive Shell Commands

**ALWAYS use non-interactive flags** with file operations to avoid hanging on confirmation prompts.

Shell commands like `cp`, `mv`, and `rm` may be aliased to include `-i` (interactive) mode on some systems, causing the agent to hang indefinitely waiting for y/n input.

**Use these forms instead:**
```bash
# Force overwrite without prompting
cp -f source dest           # NOT: cp source dest
mv -f source dest           # NOT: mv source dest
rm -f file                  # NOT: rm file

# For recursive operations
rm -rf directory            # NOT: rm -r directory
cp -rf source dest          # NOT: cp -r source dest
```

**Other commands that may prompt:**
- `scp` - use `-o BatchMode=yes` for non-interactive
- `ssh` - use `-o BatchMode=yes` to fail instead of prompting
- `apt-get` - use `-y` flag
- `brew` - use `HOMEBREW_NO_AUTO_UPDATE=1` env var

## Harness Authoring Rules

Before writing or editing any skill body, agent `.md`, or helper script, follow these two rules:

1. **Script-First** — executable workflow logic (fenced shell blocks >5 real lines, Python blocks >3 real lines, `python -c` glue, "run X, parse it, feed to Y" prose) does **not** belong in skill/agent bodies. Extract it to `scripts/` (or `beads-workflow/lib/orchestrator/` for orchestrator logic). Reference: `meta/skills/skill-auditor/references/skill-script-first.md`. Enforcer: `python3 meta/skills/skill-auditor/scripts/validate-skill.py <skill-dir>`.

2. **Execution-Result Envelope** — helpers returning multiple fields or distinguishing ok/warning/error emit `core/contracts/execution-result.schema.json`. Single atomic values may print bare. Reference: `meta/skills/agent-forge/references/execution-result-contract.md`. Reference implementation: `beads-workflow/scripts/wave-poll.py`.

Canonical Python homes: `beads-workflow/lib/orchestrator/` (orchestrator modules), `core/contracts/` (shared JSON schemas). Each has a `README.md`.

## Architecture Trinity Vocabulary

When discussing or implementing architectural tooling, use these terms precisely:

| Term | Role |
|------|------|
| **ADR** | Architecture Decision Record — documents the governing decision (context, decision, consequences) |
| **Helper** | Passive utility — encapsulates a common operation, no enforcement |
| **Enforcer-Proactive** | Codegen/Builder — makes the wrong pattern structurally impossible at creation time |
| **Enforcer-Reactive** | Lint/Test — catches violations in existing code at review/CI time |

Reference examples (mira-adapters): **ADR-001** (ADR), **makeIdHelper** (Enforcer-Proactive), **no-raw-id-concat** (Enforcer-Reactive).

See `meta/plugins/architecture-trinity/README.md` for full definitions and the canonical vocabulary table.

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
