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
