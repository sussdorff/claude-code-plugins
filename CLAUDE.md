# Claude Code Plugins Development Standards

## Python Script Standards

### Dependency Management Strategy

Choose the appropriate approach based on your script's dependencies:

#### Scripts with External Dependencies → Use `uv` + PEP 723

**REQUIRED** for scripts that need packages beyond Python's standard library.

**Template:**
```python
#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0",
#   "jsonschema>=4.0",
#   "pytest>=8.0"
# ]
# ///
"""
Script description
"""

import yaml
import jsonschema
import pytest

# Your code here...
```

**Why `uv` with PEP 723?**
- 10-100x faster than pip
- Automatic virtual environment management
- Scripts are completely self-contained and portable
- No separate `requirements.txt` needed
- No manual `pip install` step required
- Perfect for Claude Code skill distribution

#### Scripts with Stdlib Only → Use Plain Python

**ALLOWED** for scripts that only use Python's standard library.

**Template:**
```python
#!/usr/bin/env python3
"""
Script description
"""

import sys
import json
from pathlib import Path

# Your code here...
```

**Why plain Python for stdlib-only scripts?**
- Simpler, less boilerplate
- No UV installation required
- Works with any Python installation
- Cleaner for simple utilities

### When to Use Different Dependency Approaches

| Approach | When to Use | Example |
|----------|-------------|---------|
| **PEP 723 with `uv`** | Scripts with external dependencies | `test_hooks.py` (uses pytest) |
| **Plain `python3`** | Scripts with stdlib only | `validate-plugin.py` |
| **Skill-level `requirements.txt`** | Skills with importable Python modules + shared dependencies | `slack-gif-creator` with `core/` modules |
| **Plugin-level `pyproject.toml`** | Development/testing infrastructure only (NOT for distribution) | `plugin-developer/pyproject.toml` |

### Script Distribution in Claude Code

When users install plugins/skills:
- Scripts get copied to `~/.claude/plugins/` or `~/.claude/skills/`
- Scripts with external dependencies must use PEP 723 (self-contained)
- Scripts with stdlib only can use plain `python3`
- Separate dependency files (`requirements.txt`, `pyproject.toml`) won't be available to distributed scripts

## Development Workflow

```bash
# Development (optional: add plugin-level pyproject.toml for testing/linting)
cd plugin-developer
uv sync                    # If you have pyproject.toml
uv run pytest              # Run tests

# Scripts work independently via inline metadata
cd skills/plugin-tester/scripts
uv run validate-plugin.py  # Uses inline dependencies
```

## MCP Configuration in Projects

### Critical: `.mcp.json` Permission Acceptance

**IMPORTANT**: If you have a local `.mcp.json` file in your project, you **MUST** run Claude Code without `--dangerously-skip-permissions` at least **once** in that project directory for it to accept and load the `.mcp.json` configuration.

**Why this matters:**
- `.mcp.json` files require explicit user trust/approval
- Running with `--dangerously-skip-permissions` bypasses the permission dialog
- Without the initial approval, MCP servers in `.mcp.json` won't be loaded
- This only needs to be done once per project

**Workflow:**
1. Add/modify `.mcp.json` in your project
2. Run `claude` (without `--dangerously-skip-permissions`) in that directory
3. Accept the MCP server trust dialog when prompted
4. After approval, you can use `--dangerously-skip-permissions` if desired
5. Restart Claude Code to load the MCP servers

**Troubleshooting:**
- If MCP tools aren't available: Check if you've approved `.mcp.json`
- If `claude mcp list` shows nothing: MCP servers might still work in the session
- Check `.mcp.json` location: Must be at project root, not in `.claude/`

## Migration Checklist

When creating or updating Python scripts:

**For scripts with external dependencies:**
- [ ] Change shebang to `#!/usr/bin/env -S uv run --quiet --script`
- [ ] Add PEP 723 metadata block with dependencies list
- [ ] Test script runs with `uv run script.py`
- [ ] Verify script is self-contained

**For scripts with stdlib only:**
- [ ] Use `#!/usr/bin/env python3` shebang
- [ ] Verify no external dependencies in imports
- [ ] Test script runs with `python3 script.py`

## Project Structure and .claude Directories

### Symlinked .claude Pattern

This repository and related projects use a symlinked `.claude` directory pattern for centralized configuration management:

**Pattern:**
```
~/code/solutio/charly-server/.claude -> ~/code/claude/charly-server/
~/code/claude-code-plugins/.claude -> ~/code/claude/claude-code-plugins/
```

**Key Points:**
- Project repositories (e.g., `~/code/solutio/charly-server/`) contain `.claude` symlinks
- Actual `.claude` directories live in `~/code/claude/` (centralized location)
- Multiple projects can share or have separate `.claude` configurations
- Skills, commands, and settings are stored in the symlink target

**When installing skills manually:**
```bash
# For charly-server project
cp -r plugin/skills/skill-name ~/code/claude/charly-server/skills/

# For this project
cp -r plugin/skills/skill-name ~/code/claude/claude-code-plugins/skills/
```

## Plugin Skills Discovery Issue

### Known Bug

**Status:** There are active bugs in Claude Code with plugin skill discovery (Issues #9716, #9954).

**Symptoms:**
- Plugins install successfully with valid structure
- Skills from plugins are not automatically discovered
- Skills in `.claude/skills/` may not be recognized

**Our Plugin Structure (CORRECT per documentation):**
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # No 'category' field allowed
└── skills/
    └── skill-name/          # Skill subdirectory
        ├── SKILL.md         # With YAML frontmatter
        ├── references/
        └── scripts/
```

**Workaround:**
Until Claude Code fixes skill discovery, manually install skills to project `.claude/skills/` directories:

```bash
# Copy skill from plugin to project
cp -r bash-best-practices/skills/bash-best-practices .claude/skills/

# Or for symlinked .claude directories
cp -r bash-best-practices/skills/bash-best-practices ~/code/claude/project-name/skills/
```

**Verification:**
- Skills copied to `.claude/skills/` work reliably
- Plugin skills discovery is inconsistent
- Restart Claude Code after installing skills manually

### Plugin Manifest Requirements

**Valid plugin.json fields:**
- `name` (required)
- `version`
- `description`
- `author` (object with `name` and optional `email`)
- `keywords` (array)
- `license`

**Invalid fields** (cause validation errors):
- ❌ `category` - Only valid in marketplace.json, NOT plugin.json

### Marketplace.json Pattern Options

**Option 1: Anthropic Pattern (strict: false)**
```json
{
  "name": "plugin-name",
  "source": "./",
  "strict": false,
  "skills": ["./path/to/skill"]
}
```

**Option 2: Proper Plugin Structure (strict: true, default)**
```json
{
  "name": "plugin-name",
  "source": "./plugin-name",
  "category": "shell-scripting"  // Valid here, not in plugin.json
}
```

**Current Status:**
- This marketplace uses Option 2 (proper plugin structure)
- Plugin structure is correct per documentation
- Skill discovery bug prevents automatic loading
- Manual installation workaround required until bug is fixed
- ~/code/claude/ contains ".claude" directories which are dynamically linked. We we want to install into them, assume this is already the .claude directory

## Architecture Trinity Vocabulary

This project uses the **Architecture Trinity** model to classify architectural tooling into four precise terms: ADR, Helper, Enforcer-Proactive, and Enforcer-Reactive. Use this vocabulary consistently across all skills, READMEs, and design discussions.

| Term | Category | Role | Enforces? |
|------|----------|------|-----------|
| **ADR** | Decision Record | Documents "the law" — context, decision, consequences | No — governs humans and tooling |
| **Helper** | Utility | Encapsulates a common operation for reuse | No — passive, optional to use |
| **Enforcer-Proactive** | Codegen / Builder | Generates code so the wrong pattern is structurally impossible | Yes — at creation time |
| **Enforcer-Reactive** | Lint / Test | Checks existing code for violations after the fact | Yes — at review/CI time |

### Definitions

**ADR (Architecture Decision Record)**: A documented architectural decision capturing context, the decision made, and its consequences. Establishes "what is the law" for a given concern — other tooling implements or enforces that law.

**Helper**: A utility function or module that encapsulates a common operation. Passive — it helps when used, but does not prevent misuse and carries no enforcement mechanism.

**Enforcer-Proactive (Codegen / Builder)**: Tooling that generates code or scaffolding such that the wrong pattern is structurally impossible. The API itself rejects invalid input — you cannot misuse it even if you try.

**Enforcer-Reactive (Lint / Test)**: Tooling that checks existing code for violations after the fact. Catches wrong patterns during code review or CI — does not prevent writing them in the first place.

### Reference Examples (from mira-adapters)

| Example | Trinity Category | Why |
|---------|-----------------|-----|
| **ADR-001** | ADR | Declares that all entity IDs must use typed helpers, not raw strings. The governing decision. |
| **makeIdHelper** | Enforcer-Proactive | Generates typed ID accessor functions — the generated API only accepts the correct type; passing a raw string is a compile-time error. |
| **no-raw-id-concat** | Enforcer-Reactive | An ESLint rule that flags raw string concatenation of IDs. Catches violations in existing code during lint/CI. |

## Codex / codex-exec.sh

All Codex adversarial reviews run through `beads-workflow/scripts/codex-exec.sh`.

### Timeout Threshold

`CODEX_EXEC_TIMEOUT` controls the hard timeout (in seconds) passed to `timeout`/`gtimeout`:

| Variable | Default | Notes |
|----------|---------|-------|
| `CODEX_EXEC_TIMEOUT` | `300` (5 min) | Override when large prompts cause exit 124 |
| `CODEX_EXEC_MAX_PROMPT_CHARS` | `32000` | Prompt is truncated (with notice) if it exceeds this limit |

**Override syntax:**
```bash
CODEX_EXEC_TIMEOUT=600 BEAD_ID=... PHASE_LABEL=... beads-workflow/scripts/codex-exec.sh ...
```

**When to raise the timeout:**
- Codex exits 124 (timeout) without any findings in the output
- The prompt contains large agent file content (e.g. `session-close.md` at 511+ lines)
- Wave sessions processing many beads in sequence

**When to lower `CODEX_EXEC_MAX_PROMPT_CHARS`:**
- Repeated exit 124s even after raising the timeout — the prompt is simply too large
- Default (32000 chars) covers most diffs; lower only if Codex still times out

**Bash tool timeout:** When overriding `CODEX_EXEC_TIMEOUT`, also raise the Bash `timeout:` parameter
to `(CODEX_EXEC_TIMEOUT + 60) * 1000` ms to prevent the Bash wrapper from racing the internal timeout.

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
