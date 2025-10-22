---
name: skill-tester
description: This skill should be used when testing or installing skills under development in the solutio-claude-skills project. It handles copying skill files to .claude/skills/, validation, and provides guidance on when Claude Code restart is needed. Use when developing, testing, or validating any skill in this project.
---

# Skill Tester

Meta skill for testing skills under development in the solutio-claude-skills project.

## Overview

The skill-tester provides tools and workflows for iterative skill development. It automates the installation of skills from development directories to `.claude/skills/` for testing, handles validation, and clearly communicates when Claude Code restart is required.

This skill understands the project structure and the nuances of Claude Code's skill loading behavior.

## When to Use This Skill

Use this skill to:
- Install a skill from the project for testing
- Update an already-installed skill with latest changes
- Validate a skill before distribution
- Understand the testing workflow for this project
- Determine if Claude Code restart is needed

## Project Structure Understanding

Skills in this project follow this structure:

```
solutio-claude-skills/
├── jira-context-fetcher/      # Skill under development
│   ├── SKILL.md
│   ├── scripts/
│   ├── references/
│   └── assets/
├── screenshot-analyzer/        # Another skill
├── skill-tester/              # This meta skill
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
./skill-tester/scripts/install-skill-for-testing.zsh <skill-name>
```

**Example:**
```bash
./skill-tester/scripts/install-skill-for-testing.zsh jira-context-fetcher
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

For manual control:

```bash
# Copy skill files
rsync -av --delete <skill-name>/ .claude/skills/<skill-name>/

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
./skill-tester/scripts/validate-skill.py jira-context-fetcher
```

This runs the skill-creator validation checks without creating a package.

### Full Validation with Packaging

For complete validation including packaging:

```bash
cd ~/.claude/plugins/marketplaces/anthropic-agent-skills/skill-creator/
./scripts/package_skill.py /Users/malte/code/solutio/solutio-claude-skills/<skill-name>
```

## Development Workflow

### Iterative Testing Loop

```
1. Edit skill files
   ↓
2. Install for testing
   ./skill-tester/scripts/install-skill-for-testing.zsh <skill-name>
   ↓
3. Restart Claude Code if new skill
   exit → claude
   ↓
4. Test skill naturally
   "Test jira-context-fetcher with PROJ-123"
   ↓
5. Observe results and repeat from step 1
```

### Testing Best Practices

1. **Validate first**: Run validation before testing to catch issues early
2. **Test incrementally**: Install and test after each significant change
3. **Use real scenarios**: Test with actual data from JIRA, not synthetic examples
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

For skills like jira-context-fetcher that interact with external systems:

1. **Set up environment**:
   ```bash
   # Verify JIRA configuration
   cat ~/.jira-analyzer.json

   # Verify credentials
   echo $JIRA_EMAIL $JIRA_TOKEN
   ```

2. **Test with real tickets**:
   ```
   "Fetch CH2-14031"
   "Download PROJ-123 including linked tickets"
   "Get attachments from BUG-456"
   ```

3. **Verify outputs**:
   ```bash
   ls -la /tmp/jira-ticket-CH2-14031/
   jq . /tmp/jira-ticket-CH2-14031/manifest.json
   ```

## Distribution Workflow

Once testing is complete:

```bash
# 1. Final validation
./skill-tester/scripts/validate-skill.py <skill-name>

# 2. Package for distribution
cd ~/.claude/plugins/marketplaces/anthropic-agent-skills/skill-creator/
./scripts/package_skill.py /Users/malte/code/solutio/solutio-claude-skills/<skill-name>

# 3. Share the .zip file
# Created at: /Users/malte/code/solutio/solutio-claude-skills/<skill-name>.zip
```

## Scripts Reference

### install-skill-for-testing.zsh

Copies a skill from development directory to `.claude/skills/` for testing.

**Usage:**
```bash
./skill-tester/scripts/install-skill-for-testing.zsh <skill-name>
```

**Behavior:**
- Validates source skill exists
- Detects if skill is new or updated
- Copies all files using rsync
- Reports restart requirement

### validate-skill.py

Validates a skill without packaging.

**Usage:**
```bash
./skill-tester/scripts/validate-skill.py <skill-name>
```

**Checks:**
- YAML frontmatter format
- Required fields present
- File organization
- Naming conventions

## See Also

- [testing-workflow.md](./references/testing-workflow.md) - Comprehensive testing guide
- [skill-creator skill](~/.claude/plugins/marketplaces/anthropic-agent-skills/skill-creator/) - Original skill creation tool
- Project skills: jira-context-fetcher, screenshot-analyzer, jira-commentator
