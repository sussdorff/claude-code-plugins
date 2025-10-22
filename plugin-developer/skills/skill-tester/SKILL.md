---
name: skill-tester
description: This skill should be used when testing or installing standalone skills under local development. It handles copying skill files to .claude/skills/, validation, and provides guidance on when Claude Code restart is needed. Use when developing, testing, or validating any standalone skill (not part of a plugin). FOR LOCAL DEVELOPMENT ONLY - does not install skills from marketplaces.
---

# Skill Tester

Meta skill for testing standalone skills under local development.

## Overview

The skill-tester provides tools and workflows for iterative standalone skill development. It automates the installation of skills from development directories to `.claude/skills/` for testing, handles validation, and clearly communicates when Claude Code restart is required.

**Important:** This skill is for LOCAL DEVELOPMENT ONLY. It installs skills directly from your project directories, not from marketplaces or external sources.

## Key Distinction: Skill vs Plugin Installation

### Skill-Tester (this skill) - For Standalone Skills
- **What it installs:** Individual skills (directories with SKILL.md)
- **Where from:** Local project directories
- **Where to:** `.claude/skills/` directly
- **Use case:** Developing a single skill in isolation
- **Example:** `git-worktree-tools/`, `jira-context-fetcher/`
- **Structure:** Skill directory with SKILL.md at root

### Plugin-Tester (sibling skill) - For Complete Plugins
- **What it installs:** Full plugins (with `.claude-plugin/plugin.json`)
- **Where from:** Local plugin directories
- **Where to:** `.claude/commands/` AND `.claude/skills/`
- **Use case:** Developing a plugin that bundles commands, skills, hooks, agents
- **Example:** `reference-file-compactor` plugin
- **Structure:** Plugin directory with `.claude-plugin/plugin.json` metadata

**Choose the right tool:**
- Use **skill-tester** for standalone skill development
- Use **plugin-tester** for plugin development that may include multiple commands and skills

**Neither installs from marketplaces** - both are for local development only!

## When to Use This Skill

Use this skill to:
- Install a skill from the project for testing
- Update an already-installed skill with latest changes
- Validate a skill before distribution
- Understand the testing workflow for this project
- Determine if Claude Code restart is needed

## Project Structure Understanding

Standalone skills in your project typically follow this structure:

```
your-project/
├── my-skill/                   # Skill under development
│   ├── SKILL.md               # Required: skill definition
│   ├── scripts/               # Optional: executable scripts
│   ├── references/            # Optional: documentation
│   └── assets/                # Optional: images, data files
├── another-skill/             # Another skill
└── .claude/                   # Testing location
    └── skills/                # Where skills are installed
```

## Key Concept: When Skills Are Loaded

**Critical:** Skills are loaded when Claude Code starts a session, not dynamically during a session.

- **New skills**: Require exit and restart of Claude Code
- **Updated skills**: Changes available after copy (restart if issues)
- **No hot-reload**: Changes to skill files don't affect current session

## Installing Skills for Testing

### Using the Install Script (Recommended)

Execute the bundled install script to copy a skill to `.claude/skills/`:

```bash
python3 ./skill-tester/scripts/install-skill-for-testing.py <skill-name>
```

**Example:**
```bash
python3 ./plugin-developer/skills/skill-tester/scripts/install-skill-for-testing.py git-worktree-tools
```

The script will:
1. Validate the source skill exists
2. Check if skill is new or being updated
3. Copy all skill files to `.claude/skills/<skill-name>/`
4. Report whether Claude Code restart is needed

**Output interpretation:**
- **"NEW SKILL DETECTED"**: Must exit and restart Claude Code session
- **"SKILL UPDATED"**: Changes are available (restart if not appearing)

### Manual Installation

For manual control using Python:

```bash
# Copy skill files
python3 -c "import shutil; from pathlib import Path; src=Path('<skill-name>'); dst=Path('.claude/skills/<skill-name>'); dst.parent.mkdir(parents=True, exist_ok=True); shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst)"

# Check if new or updated:
# - If new: Exit and restart Claude Code
# - If updated: Continue testing (restart if issues)
```

## Validating Skills

### Quick Validation

Validate a skill without packaging:

```bash
./skill-tester/scripts/validate-skill.py <skill-name>
```

**Example:**
```bash
./plugin-developer/skills/skill-tester/scripts/validate-skill.py git-worktree-tools
```

This runs validation checks without creating a package.

## Development Workflow

### Iterative Testing Loop

```
1. Edit skill files
   ↓
2. Install for testing
   python3 ./plugin-developer/skills/skill-tester/scripts/install-skill-for-testing.py <skill-name>
   ↓
3. Restart Claude Code if new skill
   exit → claude
   ↓
4. Test skill naturally
   "Use <skill-name> to..."
   ↓
5. Observe results and repeat from step 1
```

### Testing Best Practices

1. **Validate first**: Run validation before testing to catch issues early
2. **Test incrementally**: Install and test after each significant change
3. **Use real scenarios**: Test with actual data, not synthetic examples
4. **Clean installs**: Delete and reinstall for clean testing environment
5. **Document issues**: Track what works and what doesn't

## Common Issues and Solutions

### Skill Doesn't Activate

**Symptoms:** Claude doesn't use the skill when prompted

**Solutions:**
1. Verify skill is installed: `ls -la .claude/skills/<skill-name>/`
2. If new skill, restart Claude Code session
3. Improve skill description in YAML frontmatter to match use case
4. Explicitly invoke: "Use <skill-name> to..."

### Changes Don't Appear

**Symptoms:** Old version of skill behavior persists

**Solutions:**
1. Re-run install script to ensure latest files copied
2. Start fresh Claude Code session
3. Verify files in `.claude/skills/` match source files

### Scripts Not Found

**Symptoms:** Script execution fails with "not found"

**Solutions:**
1. Verify script paths in SKILL.md are relative to skill root
2. Re-run install script
3. Check permissions: `chmod +x skill-name/scripts/*.zsh`
4. Verify scripts were copied: `ls -la .claude/skills/<skill-name>/scripts/`

## Testing with Real Data

For skills that interact with external systems or files:

1. **Set up environment**:
   ```bash
   # Verify necessary environment variables
   env | grep RELEVANT_VAR

   # Check configuration files
   cat ~/.config/your-tool.json
   ```

2. **Test with real inputs**:
   ```
   "Use <skill-name> to process real-file.md"
   "Apply <skill-name> to actual-project/"
   ```

3. **Verify outputs**:
   ```bash
   # Check created files or modifications
   ls -la /output/directory/

   # Verify content if applicable
   cat output-file.txt
   ```

## Distribution Workflow

Once testing is complete and you want to share your skill:

1. **Final validation:**
   ```bash
   ./plugin-developer/skills/skill-tester/scripts/validate-skill.py <skill-name>
   ```

2. **Package options:**
   - **Standalone skill:** Share the entire skill directory
   - **As part of plugin:** Include in a plugin's `skills/` directory
   - **Via marketplace:** Package using skill-creator tools (if available)

3. **Documentation:**
   - Ensure SKILL.md is clear and complete
   - Document any dependencies or setup requirements
   - Include usage examples in references/

## Scripts Reference

### install-skill-for-testing.py

Copies a skill from development directory to `.claude/skills/` for testing.

**Usage:**
```bash
python3 ./plugin-developer/skills/skill-tester/scripts/install-skill-for-testing.py <skill-name>
```

**Behavior:**
- Validates source skill exists
- Detects if skill is new or updated
- Copies all files using Python shutil (no external dependencies)
- Reports restart requirement
- Cross-platform compatible

### validate-skill.py

Validates a skill without packaging.

**Usage:**
```bash
./plugin-developer/skills/skill-tester/scripts/validate-skill.py <skill-name>
```

**Checks:**
- YAML frontmatter format
- Required fields present
- File organization
- Naming conventions

## See Also

- [testing-workflow.md](./references/testing-workflow.md) - Comprehensive testing guide
- plugin-tester skill - For testing complete plugins (with commands and skills bundled)
- [Claude Code Skills Documentation](https://docs.claude.com/en/docs/claude-code/skills)
