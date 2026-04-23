---
name: project-setup
description: >
  Set up new projects and upgrade existing ones to current standards. Handles scaffolding,
  beads init, Dolt remote, CLAUDE.md generation, .gitignore, and standards injection for all
  project types (Python CLI, TypeScript/Bun web, infrastructure, docs). Use when: creating a
  new project, onboarding an existing repo, upgrading project setup to current conventions,
  auditing setup drift across the fleet, or when user says "neues Projekt", "Projekt aufsetzen",
  "project setup", "setup upgraden", "fleet audit". Replaces the old project-init skill.
  Also triggers on: project init, setup CLAUDE.md, project setup, create CLAUDE.md.
---

# project-setup

> **Setup-Version**: 2026.03.0
> This skill tracks its own CalVer. Projects store their setup version in `.project-setup-version`.
> When this skill's version advances, `/project-setup --upgrade` brings projects up to date.

## Modes

```
/project-setup                    # New project: interview + full scaffolding
/project-setup --upgrade          # Upgrade existing project to current setup version
/project-setup --audit            # Fleet audit: scan all projects, report drift
/project-setup --scan-only        # Just detect and report, no changes
```

## Quick Routing

| Situation | Mode |
|-----------|------|
| Brand new project, nothing exists yet | `/project-setup` (init) |
| Existing repo, never had beads/CLAUDE.md | `/project-setup` (init) |
| Project exists but setup is outdated | `/project-setup --upgrade` |
| Want to see what's different across all projects | `/project-setup --audit` |
| Just curious what would be detected | `/project-setup --scan-only` |

## Project Types

| Type | Stack | Detection | Examples |
|------|-------|-----------|----------|
| `python-cli` | Python + uv + Click/Typer + PyPI | `pyproject.toml` with `[project.scripts]` | abs-cli, fmcli, zahnrad |
| `web-ts` | Bun + Hono + TypeScript | `package.json` + `bunfig.toml` or `bun.lockb` | mira, gobot, open-brain |
| `infra` | Shell/Makefile + SSH configs | `Makefile` or shell scripts, no package manager | elysium-proxmox, hetzner |
| `docs` | Markdown, possibly SSG | No code package manager, mostly `.md` files | agenticcoding.school |

Auto-detection picks the type. If ambiguous, ask the user.

---

## Init Mode (new project)

### Phase 0: Pre-flight

1. Confirm working directory is correct: show path, ask user
2. Check if `.beads/` exists — if yes, suggest `--upgrade` instead
3. Check if `.project-setup-version` exists — if yes, suggest `--upgrade` instead
4. Run `bd --version` — record for compatibility notes

### Phase 1: Interview

Ask one question at a time. In German. Accept "passt so", "skip", "weiter" as confirmation.

**Q1: Was wird das?**
> Was fuer ein Projekt ist das? Was soll es tun und fuer wen?

**Q2: Projekttyp bestaetigen**
> Based on Q1 answer and any existing files, propose a type (`python-cli`, `web-ts`, `infra`, `docs`).
> Show reasoning. Ask user to confirm or correct.

**Q3: Name und Prefix**
> Wie soll das Projekt heissen? (Verzeichnisname, PyPI-Paketname, Beads-Prefix)
> Schlage vor basierend auf Verzeichnisname. Beads-Prefix: kurz, keine Bindestriche.

**Q4: Git Remote**
> Git Remote URL? (Falls noch kein git repo: Soll ich eins anlegen?)

**Q5: Architektur** (skip for `infra`/`docs`)
> Gibt es wichtige Architektur-Entscheidungen? Besonders das WARUM.

**Q6: Externe Abhaengigkeiten** (skip for `docs`)
> Mit welchen externen APIs, Services oder Datenbanken wird gearbeitet?

### Phase 2: Scaffolding

After interview, show a complete plan of what will be created. Get explicit confirmation before writing anything.

#### Common steps (all types)

1. `git init` (if not already a repo)
2. `bd init --server --prefix <prefix>` — initializes beads with Dolt server mode
3. Fix beads setup (use dolt-remote skill knowledge):
   - `bd dolt stop` (stop local server bd just started)
   - `bd dolt set port 3307`
   - `bd config set dolt-data-dir /Users/malte/.dolt-data`
   - Clean `metadata.json` to only `dolt_database`
4. Copy canonical `.beads/.gitignore` from `/Users/malte/code/claude/.beads/.gitignore`
5. Create remote DB on elysium (via dolt-remote workflow)
6. `bd dolt remote add origin http://192.168.60.30:8080/beads_<prefix>`
7. Force-push to establish remote history
8. Set up `.claude/` symlink via `/claude-config-handler`
9. Write `.project-setup-version` with current skill version

#### Type-specific scaffolding

See `references/type-recipes.md` for the complete scaffolding per project type.

### Phase 3: CLAUDE.md Generation

Use the auto-scan + interview approach from the old project-init skill to generate `./CLAUDE.md`.

See `references/claude-md-generation.md` for the full template and rules.

### Phase 4: Standards Injection

Run `/inject-standards` to load relevant standards based on detected project type.

### Phase 5: Verification

```bash
bd dolt test          # Dolt connection works
bd dolt push          # Remote push works
bd doctor             # No warnings
cat .project-setup-version  # Shows current version
```

Report results. If anything fails, diagnose using dolt-remote skill knowledge.

### Phase 6: Summary

```
Projekt "<name>" ist aufgesetzt:

  Typ:           python-cli
  Beads-Prefix:  <prefix>
  Dolt Remote:   http://192.168.60.30:8080/beads_<prefix>
  Setup-Version: 2026.03.0

  Naechste Schritte:
  - [typ-spezifische Hinweise]
  - bd create --title="..." --type=feature  (erstes Bead anlegen)
```

---

## Upgrade Mode

Brings an existing project up to the current setup version.

### Step 1: Read current state

```bash
cat .project-setup-version 2>/dev/null || echo "NONE"
bd --version
```

### Step 2: Detect project type

Use the same detection as init mode (pyproject.toml, package.json, etc.).

### Step 3: Diff against current version

Compare what the project has against what the current setup version expects. Check each component:

| Component | Check | Fix |
|-----------|-------|-----|
| `.beads/.gitignore` | Diff against canonical | Copy canonical version, `git rm --cached` for newly-ignored tracked files |
| `.beads/metadata.json` | Only `dolt_database` (+`project_id`) | Remove deprecated fields |
| `.beads/dolt-server.port` | Contains `3307` | Write `3307` |
| `.beads/config.yaml` | Has `dolt-data-dir` | `bd config set dolt-data-dir /Users/malte/.dolt-data` |
| Legacy files | None should exist | Remove (see dolt-remote skill) |
| `.project-setup-version` | Exists and current | Create/update |
| `CLAUDE.md` | Exists and structured | Run CLAUDE.md generation if missing |
| `.claude/` | Symlinked correctly | Fix via claude-config-handler |
| Type-specific | See `references/type-recipes.md` | Apply missing pieces |

### Step 4: Present changes

Show everything that would change. Get confirmation before applying.

### Step 5: Apply and verify

Apply changes, run verification (same as init Phase 5), update `.project-setup-version`.

---

## Audit Mode

Scans all projects under `~/code/` that have `.beads/` and reports drift.

```bash
find ~/code -maxdepth 3 -name ".beads" -type d ! -path "*worktrees*" 2>/dev/null
```

For each project, check:
- `.project-setup-version` (missing = never set up, outdated = needs upgrade)
- Project type detection
- Beads health (`metadata.json`, `dolt-server.port`, legacy files)
- `.gitignore` diff against canonical

Output a table:

```
Project             Type        Setup Version   Status
abs-cli             python-cli  2026.03.0       OK
fmcli               python-cli  NONE            NEEDS SETUP
mira                web-ts      2025.12.0       NEEDS UPGRADE
cognovis-website    docs        NONE            NEEDS SETUP
```

Do NOT auto-fix in audit mode. Just report. Suggest `/project-setup --upgrade` for individual projects.

---

## Version Tracking

### `.project-setup-version` file

Lives in project root. Single line with the CalVer version of this skill at setup/upgrade time.

```
2026.03.0
```

This file SHOULD be committed to git — it's team-shared project metadata.

### Upgrade changelog

When the skill version advances, document what changed between versions in `references/upgrade-changelog.md`.
The upgrade mode reads this to determine which steps to apply for a given version jump.

---

## Do NOT

- Do NOT scaffold without showing the plan and getting user confirmation. A wrong scaffold is hard to undo.
- Do NOT run `bd init` with default settings. Always use `--server --prefix` and then fix the Dolt setup to use the central server. The default local server creates problems (see dolt-remote skill).
- Do NOT guess the project type when auto-detection is ambiguous. Ask the user.
- Do NOT apply upgrades without showing what will change. Users need to review first.
- Do NOT overwrite manually added CLAUDE.md sections. Preserve custom content.
- Do NOT push to git remote without user confirmation.

## Important Notes

- **Interview in German, CLAUDE.md in English.** Convention: CLAUDE.md is always English for portability.
- **Idempotent upgrades.** Running `--upgrade` on an already-current project is a no-op.
- **Canonical `.gitignore` source:** `/Users/malte/code/claude/.beads/.gitignore`
- **This skill delegates** to dolt-remote knowledge for Dolt setup and to claude-config-handler for `.claude/` management. It orchestrates, those handle the details.
