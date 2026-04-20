---
name: project-context
description: >-
  Generate docs/project-context.md (Constitution Pattern) from an existing codebase.
  Analyzes CLAUDE.md, architecture docs, and directory structure to produce a readable,
  editable, git-versioned context document covering Tech Stack, Architecture Principles,
  Module Map, Established Patterns, and Critical Invariants. Triggers on: project context, generate project context,
  project-context, create project-context, constitution document, codebase context.
tags: project, documentation, architecture
---

# Project Context

Generate `docs/project-context.md` — a human-readable, editable Constitution document that
captures your codebase's tech stack, architecture principles, module map, patterns, and
critical invariants.

The output is **intentionally static** — it does not auto-regenerate to avoid drift. Regenerate
manually when your architecture changes significantly.

Consumed by orchestration agents as project context for new implementations.

## When to Use

- After setting up a new project (project setup → project context generation; see your harness adapter (e.g. `SKILL.claude-adapter.md`) for invocation details)
- When onboarding someone new to the codebase
- When starting a major refactor and want to document current state first
- When your orchestration workflow injects project context into implementation sessions

## Do NOT

- Do NOT run automatically or as a CI step — regeneration is manual by design
- Do NOT overwrite `docs/project-context.md` without confirmation (use `--force` to skip)
- Do NOT include file-by-file listings — Module Map stays high-level (top-level dirs only)

## Arguments

Pass arguments directly when invoking this skill. Supported flags: `--force`, `--dry-run`, `--section=<name>`.

| Flag | Effect |
|------|--------|
| (none) | Interactive: analyze + generate with overwrite confirmation if file exists |
| `--force` | Overwrite existing `docs/project-context.md` without asking |
| `--dry-run` | Analyze and print the generated content to chat, do NOT write the file |
| `--section=<name>` | Regenerate only one section (tech-stack, module-map, patterns, invariants, principles, enforcement-matrix) |

## Workflow

### Phase 0: Pre-flight

1. Parse the arguments passed to this skill invocation to detect flags (`--force`, `--dry-run`, `--section=<name>`)

2. Check if `docs/project-context.md` already exists:
   ```bash
   test -f docs/project-context.md && echo "EXISTS" || echo "NEW"
   ```

   **If EXISTS and NOT `--force` and NOT `--section`:**
   - Report: "⚠️  `docs/project-context.md` already exists."
   - Show first 5 lines of the existing file so user knows what version it is
   - Ask: "Overwrite with a fresh analysis? (Use `--force` to skip this prompt)"
   - If user says no / cancel: abort with "Aborted. Run this skill again with `--force` to overwrite."
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
`[DRY RUN — file not written. Run this skill without --dry-run to write docs/project-context.md]`

**If `--section=<name>`**: regenerate only that section in the existing file.

**Otherwise**: write the full document to `docs/project-context.md` using the template from
`references/output-template.md` as structural guide.

Section ordering (always):
1. Tech Stack
2. Architecture Principles
3. Module Map
4. Established Patterns
5. Critical Invariants
6. Enforcement Matrix

Output size: target 150-300 lines. If Module Map exceeds 20 rows, truncate to top 15 + note.

**Handle overwrite scenario**: if file exists and `--force` not set and not `--section`, confirm before overwriting.

### Phase 3.5: Enforcement Matrix

Run the standalone scanner to generate the Enforcement Matrix section:

```bash
python3 <skill_dir>/scripts/enforcement_matrix_scanner.py <repo_root>
```

Where `<skill_dir>` is the directory containing this SKILL.md (find it via the skill installation path), and `<repo_root>` is the project root being analyzed.

The scanner (`enforcement_matrix_scanner.py`) is a stdlib-only Python script that:
- Parses `docs/adr/**/*.md` YAML frontmatter for contract declarations
- Scans `packages/*/src/` for Helper artifacts
- Scans `packages/*/scripts/*gen*` and `package.json` for Proactive (codegen) enforcers
- Checks `eslint.config.js` and `check:*` scripts for Reactive (lint) enforcers
- Outputs a `## Enforcement Matrix` Markdown section with a gap-count signal line

**Insert the script output** into the generated document after `## Critical Invariants`.

If the output contains `Enforcement gaps: N`, note this in the Phase 4 report.

**If `--section=enforcement-matrix`**: run only the scanner, update only that section.

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
- Enforcement Matrix: {N contracts × M packages} ({gap_count} gaps or "none")

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
| No `docs/adr/` directory | Enforcement Matrix shows "No contracts declared yet" |
| ADRs exist but no `packages/*/` | Use repo root as single package column |

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
- Orchestration agents: reads `docs/project-context.md` for project context injection
- Session summary tools: may append new architecture decisions after significant sessions (see your harness adapter for specifics)

**Related skills:**
- Project setup — sets up a new project (see your harness adapter for invocation details)
- Project health — quality assessment (run independently)
- Spec developer — deep feature specs (uses project-context as input context; see your harness adapter for invocation details)
