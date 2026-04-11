# Upgrade Changelog

When the project-setup skill version advances, document what changed here.
The upgrade mode reads this to determine which steps to apply for a version jump.

## 2026.03.0 (Initial Release)

First version. No upgrades to apply — this is the baseline.

### What this version establishes

- `.project-setup-version` file in project root
- `.beads/.gitignore` canonical version (63 lines, includes `interactions.jsonl`, `.migration-hint-*`)
- Beads Dolt setup: central server on port 3307, `dolt-data-dir` in config.yaml
- `metadata.json` clean: only `dolt_database` (+ `project_id`)
- No legacy files in `.beads/`
- CLAUDE.md generated via auto-scan + interview
- `.claude/` symlinked via claude-config-handler
- Type-specific scaffolding applied

### Upgrading from "no version" to 2026.03.0

Projects without `.project-setup-version` are treated as pre-skill. The upgrade checks all components
and applies what's missing. Equivalent to a selective init that preserves existing content.

Steps:
1. Detect project type
2. Check and fix `.beads/.gitignore` (copy canonical, `git rm --cached` for newly-ignored files)
3. Check and fix Dolt setup (port, data-dir, metadata.json, legacy files)
4. Check CLAUDE.md exists (offer to generate if missing)
5. Check `.claude/` symlink (fix if broken)
6. Write `.project-setup-version`
