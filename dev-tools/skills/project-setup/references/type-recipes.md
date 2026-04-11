# Type-Specific Scaffolding Recipes

## python-cli

Based on standard: `~/.claude/standards/python/cli-patterns.md`

### Directory structure
```
<project>/
  src/<package_name>/
    __init__.py          # __version__ = "0.0.0" (CI stamps this)
    __main__.py          # click.group() entry point
    cli.py               # CLI commands
  tests/
    __init__.py
    conftest.py
    test_cli.py
  pyproject.toml
  README.md
  CHANGELOG.md
  .gitignore
  .python-version        # e.g. "3.12"
```

### pyproject.toml template
```toml
[project]
name = "<project-name>"
version = "0.0.0"
description = "<from interview>"
requires-python = ">=3.12"
dependencies = [
    "click>=8.1",
]

[project.scripts]
<cli-name> = "<package_name>.cli:cli"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.backends"

[tool.hatch.build.targets.wheel]
packages = ["src/<package_name>"]

[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Post-scaffold commands
```bash
uv sync                  # Create venv + install deps
uv run pytest            # Verify test setup works
```

### .gitignore additions
```
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/
.ruff_cache/
```

---

## web-ts

Based on mira project patterns.

### Directory structure
```
<project>/
  src/
    index.ts             # Entry point
    lib/
      config.ts          # Centralized config (env vars)
    routes/              # API routes (Hono)
  tests/
    setup.ts
  package.json
  tsconfig.json
  bunfig.toml
  README.md
  CHANGELOG.md
  .gitignore
  .env.example
```

### package.json template
```json
{
  "name": "<project-name>",
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "bun run --watch src/index.ts",
    "build": "bun build src/index.ts --outdir dist",
    "test": "bun test",
    "lint": "bunx biome check ."
  },
  "dependencies": {
    "hono": "^4"
  },
  "devDependencies": {
    "@biomejs/biome": "^1",
    "@types/bun": "latest"
  }
}
```

### tsconfig.json template
```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "skipLibCheck": true,
    "types": ["bun-types"],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["src/**/*.ts", "tests/**/*.ts"]
}
```

### Post-scaffold commands
```bash
bun install              # Install deps
bun test                 # Verify test setup
```

### .gitignore additions
```
node_modules/
dist/
.env
bun.lockb
```

---

## infra

Minimal scaffolding — infrastructure projects are mostly shell scripts and config.

### Directory structure
```
<project>/
  scripts/               # Operational scripts
  docs/                  # Runbooks, architecture notes
  Makefile               # Common operations
  README.md
  CHANGELOG.md
  .gitignore
```

### Makefile template
```makefile
.PHONY: help
help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
```

No package manager, no build system. The value comes from beads tracking + CLAUDE.md + standards.

---

## docs

Even more minimal — documentation and content projects.

### Directory structure
```
<project>/
  README.md
  CHANGELOG.md
  .gitignore
```

If the project uses a static site generator (detected via package.json with astro/vitepress/etc.),
treat it as `web-ts` instead.

---

## Upgrade Notes per Type

When upgrading, only add what's missing. Never overwrite existing files unless the user confirms.

### python-cli upgrades
- Check `pyproject.toml` has `[tool.ruff]` section
- Check `pyproject.toml` has `[tool.pytest.ini_options]`
- Check `.python-version` exists
- Check `src/` layout (not flat layout)
- Check `__version__` sentinel in `__init__.py`

### web-ts upgrades
- Check `tsconfig.json` uses strict mode
- Check `.env.example` exists
- Check `src/lib/config.ts` exists (centralized config)
- Check biome or eslint is configured

### infra upgrades
- Check Makefile has help target
- Check scripts/ has shebang lines and `set -euo pipefail`

### All types
- `.beads/.gitignore` matches canonical
- `.project-setup-version` exists and is current
- `CLAUDE.md` exists
- `.claude/` is properly symlinked
- Beads Dolt setup is correct (see dolt-remote skill)
