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
