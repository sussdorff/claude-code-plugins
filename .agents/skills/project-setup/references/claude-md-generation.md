# CLAUDE.md Generation

Ported from the old project-init skill. This is Phase 3 of `/project-setup` init mode.

## Auto-Scan

Use Glob and Read (NOT grep/find). Check each category in parallel.

### Tech Stack Detection

| File | Detects |
|------|---------|
| `pyproject.toml` | Python version, deps, build system, linter |
| `package.json` | Node.js, framework, scripts |
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `Dockerfile` | Container setup |
| `docker-compose.yml` | Multi-service |
| `uv.lock` | uv package manager |
| `bun.lockb` / `bunfig.toml` | Bun runtime |
| `Makefile` | Make-based build |

### CI/CD Detection

Check: `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`

### Git Info

```bash
git remote get-url origin 2>/dev/null
git log --oneline -10 2>/dev/null          # Commit style
git tag --sort=-creatordate 2>/dev/null | head -5  # Release strategy
```

## CLAUDE.md Template

Generate in English. Omit sections with no data.

```markdown
# Project: [name]

[One-liner from interview or README]

## Tech Stack
- **Language:** [e.g. Python 3.12]
- **Framework:** [e.g. FastAPI]
- **Package Manager:** [e.g. uv]

## Architecture
[Decisions with WHY from interview]

## Development Setup
```bash
# Setup
[detected commands, e.g.:]
uv sync

# Tests
[e.g.:]
uv run pytest

# Linting
[e.g.:]
uv run ruff check .
```

## Project Structure
```
project-root/
+-- src/           -- [description]
+-- tests/         -- [test framework]
```

## Conventions
- **Branch Naming:** [detected or from interview]
- **Commit Style:** [detected from git log]
- **Testing:** [framework + coverage]

## Known Constraints
- [From interview]

## External Dependencies
- [APIs, services, databases]
```

## Rules

1. Omit sections with no data — no empty placeholders
2. Use detected ecosystem commands (uv run for Python+uv, bun for Bun, etc.)
3. Keep it concise — reference doc, not essay
4. English for CLAUDE.md content
5. If existing CLAUDE.md has custom sections not in template: PRESERVE them
6. Never write without showing diff and getting confirmation
