---
name: project-context
model: inherit
description: >-
  Generate docs/project-context.md (Constitution Pattern) from an existing codebase.
  Analyzes CLAUDE.md, architecture docs, and directory structure to produce a readable,
  editable, git-versioned context document covering Tech Stack, Architecture Principles,
  Module Map, Established Patterns, and Critical Invariants. Used by bead-orchestrator
  Phase 2 as project context. Triggers on: project context, generate project context,
  project-context, create project-context, constitution document, codebase context.
argument-hint: "[--force] [--dry-run] [--section=<name>]"
tags: project, documentation, architecture
---

# /project-context

Generate `docs/project-context.md` — a human-readable, editable Constitution document that
captures your codebase's tech stack, architecture principles, module map, patterns, and
critical invariants.

The output is **intentionally static** — it does not auto-regenerate to avoid drift. Regenerate
manually when your architecture changes significantly.

Consumed by `bead-orchestrator` Phase 2 as project context for new implementations.

## When to Use

- After setting up a new project (`/project-setup` → `/project-context`)
- When onboarding someone new to the codebase
- When starting a major refactor and want to document current state first
- When bead-orchestrator Phase 2 needs `docs/project-context.md` for context injection

## Do NOT

- Do NOT run automatically or as a CI step — regeneration is manual by design
- Do NOT overwrite `docs/project-context.md` without confirmation (use `--force` to skip)
- Do NOT include file-by-file listings — Module Map stays high-level (top-level dirs only)

## Arguments

`$ARGUMENTS`

| Flag | Effect |
|------|--------|
| (none) | Interactive: analyze + generate with overwrite confirmation if file exists |
| `--force` | Overwrite existing `docs/project-context.md` without asking |
| `--dry-run` | Analyze and print the generated content to chat, do NOT write the file |
| `--section=<name>` | Regenerate only one section (tech-stack, module-map, patterns, invariants, principles) |

## Workflow

### Phase 0: Pre-flight

1. Parse `$ARGUMENTS` to detect flags (`--force`, `--dry-run`, `--section=<name>`)

2. Check if `docs/project-context.md` already exists:
   ```bash
   test -f docs/project-context.md && echo "EXISTS" || echo "NEW"
   ```

   **If EXISTS and NOT `--force` and NOT `--section`:**
   - Report: "⚠️  `docs/project-context.md` already exists."
   - Show first 5 lines of the existing file so user knows what version it is
   - Ask: "Overwrite with a fresh analysis? (Use `--force` to skip this prompt)"
   - If user says no / cancel: abort with "Aborted. Run `/project-context --force` to overwrite."
   - If user says yes: continue

3. Create `docs/` directory if it doesn't exist:
   ```bash
   mkdir -p docs
   ```

### Phase 1: Gather Sources

Collect all available context. Use Read and Glob tools (NOT grep/find/cat).

**1a. CLAUDE.md** (primary source for principles and invariants):
Read `./CLAUDE.md`. If not found: note "CLAUDE.md not present — deriving principles from codebase analysis only."
Follow symlinks: CLAUDE.md may be a symlink. Read the resolved file content.

**1b. Architecture documents** (secondary source):
Glob `docs/architecture/**/*.md`, `docs/arch/*.md`, `docs/design/*.md`, `ADR-*.md`, `architecture.md`.
Read up to 5 most recent architecture files.

**1c. README**: Read `README.md`. Extract project name, one-line description, architecture notes.

**1d. Package manifests** (for tech-stack detection):
Glob and read whichever exist: `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, `Gemfile`, `uv.lock`, `bun.lockb`, `bunfig.toml`.
Extract: language version, runtime, framework, package manager, test framework, linter.

**1e. CI configuration**:
Glob `.github/workflows/*.yml`, `.gitlab-ci.yml`. Extract CI platform and build commands.

**1f. Top-level directory structure** (for Module Map):
List top-level directories, excluding `.git/`, `node_modules/`, `__pycache__/`, `dist/`, `build/`, `target/`, `.venv/`.
For each top-level directory: read its README.md or main entrypoint if small.

**Secrets/PII filter**: Do NOT include content from `.env`, `*.key`, `*.pem`, `secrets.*`, `credentials.*`.

### Phase 2: Analysis

Derive each section from gathered sources:

**Tech Stack** — from package manifests + CI.

**Architecture Principles** — from CLAUDE.md + arch docs + README. Extract explicit architectural
decisions and rationale. If none found: derive from structural patterns.
Format as numbered list: **Name**: Explanation.

**Module Map** — from directory structure + README. List each top-level directory with one-line
purpose and 1-2 key files. Skip: `.git/`, `node_modules/`, `__pycache__/`, `dist/`, `build/`.
For monorepos: list sub-packages, not individual files.

**Established Patterns** — from CLAUDE.md + codebase reading. Minimum 3 patterns, maximum 8.
Each pattern: name, where it appears, what it is, why it exists.

**Critical Invariants** — from CLAUDE.md + arch docs. Extract explicit must/never/always rules.
Minimum 3 invariants.

### Phase 3: Generate Output

**If `--dry-run`**: print full generated content to chat, do NOT write any file. End with:
`[DRY RUN — file not written. Run `/project-context` without --dry-run to write docs/project-context.md]`

**If `--section=<name>`**: regenerate only that section in the existing file.

**Otherwise**: write the full document to `docs/project-context.md` using the template from
`references/output-template.md` as structural guide.

Section ordering (always):
1. Tech Stack
2. Architecture Principles
3. Module Map
4. Established Patterns
5. Critical Invariants

Output size: target 150-300 lines. If Module Map exceeds 20 rows, truncate to top 15 + note.

**Handle overwrite scenario**: if file exists and `--force` not set and not `--section`, confirm before overwriting.

### Phase 4: Report

After writing (or dry-running):

```
## ✅ docs/project-context.md generated

**Sources used:**
- CLAUDE.md: {found/not found}
- Architecture docs: {N files}
- Package manifests: {list}
- Directory scan: {N top-level dirs}

**Sections written:**
- Tech Stack: {N rows}
- Architecture Principles: {N items}
- Module Map: {N modules}
- Established Patterns: {N patterns}
- Critical Invariants: {N invariants}

**Warnings** (if any):
- {e.g. "CLAUDE.md not found"}

Next: Review the generated file, edit as needed, then commit:
  git add docs/project-context.md && git commit -m "docs: add project-context"
```

## Edge Cases

| Situation | Behavior |
|-----------|----------|
| No `CLAUDE.md` | Note in output header; derive from codebase |
| No architecture docs | Module Map from directory structure only |
| `docs/project-context.md` exists, no `--force` | Ask for confirmation before overwriting |
| Large monorepo (N > 20 top-level dirs) | Limit Module Map to 15 entries + count note |
| Mixed languages | Tech Stack lists all runtimes found |
| Symlinked CLAUDE.md | Follow symlink; read resolved content |
| Secrets files | Skip and report skipped files |
| `--section=<name>` | Regenerate only named section; preserve rest |

## Output Template

See `references/output-template.md` for the full template.

The template covers these required sections:
- Tech-Stack table
- Architecture Principles numbered list
- Module Map table
- Established Patterns subsections
- Invarianten (Critical Invariants) numbered list

## Integration

**Consumed by:**
- `bead-orchestrator` Phase 2: reads `docs/project-context.md` for project context injection
- `session-close`: may append new architecture decisions after significant sessions

**Related skills:**
- `/project-setup` — sets up new project (run before `/project-context`)
- `/project-health` — quality assessment (run independently)
- `/spec-developer` — deep feature specs (uses project-context as input context)
