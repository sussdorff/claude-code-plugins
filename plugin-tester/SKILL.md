---
name: plugin-tester
description: This skill should be used when testing or installing plugins under development in the claude-code-plugins project. It handles copying plugin commands and skills to .claude/ directories for local testing. Use when developing, testing, or validating any plugin in this project.
---

# Plugin Tester

Meta skill for testing plugins under development in the claude-code-plugins project.

## Overview

The plugin-tester provides tools and workflows for iterative plugin development. It automates the installation of plugins from development directories to `.claude/commands/` and `.claude/skills/` for local testing, handles validation, and clearly communicates when Claude Code restart is required.

This skill understands the local development workflow for Claude Code plugins.

## When to Use This Skill

Use this skill to:
- Install a plugin from the project for local testing
- Update an already-installed plugin with latest changes
- Validate a plugin structure before testing
- Understand the local testing workflow for this project
- Determine if Claude Code restart is needed

## Key Understanding: Local Testing vs Distribution

**For Local Development:**
- Commands → `.claude/commands/` (project-level)
- Skills → `.claude/skills/` (project-level)
- Both loaded at Claude Code startup
- No marketplace/plugin system needed

**For Distribution:**
- Package as plugin with `.claude-plugin/plugin.json`
- Commands and skills bundled together
- Distributed via marketplaces
- Installed with `/plugin install` command

This skill focuses on **local development** workflow.

## Project Structure Understanding

Plugins in this project follow the standard Claude Code plugin structure:

```
claude-code-plugins/
├── reference-file-compactor/      # Plugin under development
│   ├── .claude-plugin/
│   │   └── plugin.json           # Plugin metadata
│   ├── commands/                  # Slash commands
│   ├── skills/                    # Skills
│   └── README.md
├── plugin-tester/                 # This testing skill
└── .claude/                       # Local testing infrastructure
    ├── commands/                  # Installed commands
    └── skills/                    # Installed skills
```

## Key Concept: Plugins vs Skills vs Commands

**Plugins** (distribution unit):
- Contain `.claude-plugin/plugin.json` metadata
- Bundle commands, skills, agents, hooks together
- Packaged for distribution via marketplaces
- Structure preserved for future distribution

**Commands** (slash commands):
- Markdown files in `commands/` directory
- User-invoked with `/command-name`
- Loaded at Claude Code startup
- Copied to `.claude/commands/` for testing

**Skills** (AI capabilities):
- Directories with `SKILL.md` in `skills/` directory
- Model-invoked based on SKILL.md description
- Loaded at Claude Code startup
- Copied to `.claude/skills/` for testing

## Installing Plugins for Testing

### Using the Install Script (Recommended)

Execute the bundled install script to install a plugin for local testing:

```bash
./plugin-tester/scripts/install-plugin-for-testing.sh <plugin-name>
```

**Example:**
```bash
./plugin-tester/scripts/install-plugin-for-testing.sh reference-file-compactor
```

The script will:
1. Validate the plugin structure (checks for `.claude-plugin/plugin.json`)
2. Copy commands to `.claude/commands/`
3. Copy skills to `.claude/skills/`
4. Report what was installed
5. Provide restart instructions

**Example Output:**
```
📦 Installing plugin: reference-file-compactor (v1.0.0)
   Validation-driven reference file compaction

📋 Installing commands...
   ✓ compact-reference

🧠 Installing skills...
   ✨ New: reference-file-compactor

✅ Plugin installed successfully

📊 Summary:
   Commands: 1 installed to .claude/commands/
   Skills: 1 installed to .claude/skills/

⚠️  RESTART REQUIRED
   Commands and skills are loaded at Claude Code startup.

   Steps:
   1. Exit this Claude Code session: exit
   2. Start a new session: claude
   3. Test commands: /compact-reference
   3. Skills will be auto-invoked based on their descriptions

📍 Plugin source: /path/to/reference-file-compactor
📍 Commands: /path/to/.claude/commands/
📍 Skills: /path/to/.claude/skills/
```

### Manual Installation

For manual control:

1. **Copy commands:**
```bash
cp plugin-name/commands/*.md .claude/commands/
```

2. **Copy skills:**
```bash
rsync -a plugin-name/skills/ .claude/skills/
```

3. **Restart Claude Code:**
```bash
exit
claude
```

## Plugin Validation

### Quick Validation

Check plugin structure:

```bash
# Verify plugin.json exists and is valid
jq . <plugin-name>/.claude-plugin/plugin.json

# Check required fields
jq -r '.name, .version, .description' <plugin-name>/.claude-plugin/plugin.json
```

### Component Validation

**Commands validation:**
```bash
# Check commands directory exists
ls -la <plugin-name>/commands/

# Verify command files have YAML frontmatter
head -5 <plugin-name>/commands/*.md
```

**Skills validation:**
```bash
# Check skills directory
ls -la <plugin-name>/skills/

# Verify each skill has SKILL.md
find <plugin-name>/skills/ -name "SKILL.md"
```

## Development Workflow

### Iterative Testing Loop

```
1. Edit plugin files (commands, skills, scripts)
   ↓
2. Install for testing
   ./plugin-tester/scripts/install-plugin-for-testing.sh <plugin-name>
   ↓
3. Restart Claude Code
   exit → claude
   ↓
4. Test plugin functionality
   /your-command (for commands)
   "Use <skill-name>..." (for skills)
   ↓
5. Verify behavior and repeat from step 1
```

### Testing Best Practices

1. **Validate structure first**: Ensure plugin.json exists and is valid
2. **Test incrementally**: Install and test after each significant change
3. **Use real scenarios**: Test with actual use cases, not synthetic examples
4. **Clean installs**: Delete from `.claude/` and reinstall for clean environment
5. **Check all components**: Test commands, skills, and any bundled scripts

## Common Issues and Solutions

### Command Doesn't Appear

**Symptoms:** `/your-command` says command not found

**Solutions:**
1. Verify command file exists: `ls .claude/commands/`
2. Check command has YAML frontmatter with description
3. Restart Claude Code (commands loaded at startup)
4. Run `/help` to see if command is registered
5. Check for typos in command filename

### Skill Doesn't Activate

**Symptoms:** Claude doesn't use the skill when prompted

**Solutions:**
1. Verify skill installed: `ls .claude/skills/<skill-name>/`
2. Check SKILL.md has proper YAML frontmatter
3. Improve skill description to match use case
4. Explicitly invoke: "Use <skill-name> to..."
5. Restart Claude Code session

### Changes Don't Appear

**Symptoms:** Old version of behavior persists

**Solutions:**
1. Re-run install script to ensure latest files copied
2. Verify files in `.claude/` match source files
3. Restart Claude Code (fresh session)
4. Check timestamps: `ls -lt .claude/commands/` and `ls -lt .claude/skills/`

### Scripts Not Found

**Symptoms:** Skill tries to execute script but fails with "not found"

**Solutions:**
1. Verify script paths in SKILL.md are correct
2. Check scripts were copied with skill: `ls .claude/skills/<skill-name>/scripts/`
3. Verify scripts are executable: `chmod +x .claude/skills/<skill-name>/scripts/*.sh`
4. Use absolute paths in SKILL.md if relative paths fail

## Testing with Real Data

For plugins that interact with external systems:

1. **Set up environment:**
   ```bash
   # Verify necessary environment variables
   env | grep RELEVANT_VAR

   # Check configuration files
   cat ~/.config/tool.json
   ```

2. **Test with real inputs:**
   ```bash
   # Use actual command with real arguments
   /your-command real-argument

   # Or invoke skill naturally
   "Use <skill-name> to process actual-file.md"
   ```

3. **Verify outputs:**
   ```bash
   # Check created files
   ls -la /tmp/output/

   # Verify content
   cat /tmp/output/result.json | jq .
   ```

## Distribution Workflow

Once testing is complete and plugin is ready for distribution:

1. **Final validation:**
   ```bash
   # Verify all components work
   jq . <plugin-name>/.claude-plugin/plugin.json
   find <plugin-name>/commands/ -name "*.md" -exec head -5 {} \;
   find <plugin-name>/skills/ -name "SKILL.md" -print
   ```

2. **Package plugin:**
   - Ensure README.md documents installation and usage
   - Update version in plugin.json
   - Test one more time with fresh install
   - Tag release in git

3. **Publish:**
   - Add to marketplace (GitHub repo or local marketplace)
   - Share installation instructions
   - Document expected behavior and requirements

## Scripts Reference

### install-plugin-for-testing.sh

Installs a plugin for local testing by copying to `.claude/` directories.

**Usage:**
```bash
./plugin-tester/scripts/install-plugin-for-testing.sh <plugin-name>
```

**Behavior:**
- Validates plugin structure (checks `.claude-plugin/plugin.json`)
- Copies commands to `.claude/commands/`
- Copies skills to `.claude/skills/`
- Reports what was installed and where
- Provides restart instructions

**What it does:**
- Reads plugin metadata from `plugin.json`
- Iterates through `commands/*.md` files and copies to `.claude/commands/`
- Iterates through `skills/*/` directories and copies to `.claude/skills/`
- Detects new vs update installations
- Counts installed components

**Requirements:**
- Plugin must have `.claude-plugin/plugin.json`
- `jq` must be installed for JSON parsing
- `rsync` for skill directory copying

**Exit codes:**
- 0: Success
- 1: Validation error (missing plugin, bad structure)

## File Locations

### Plugin Source
```
<plugin-name>/
├── .claude-plugin/plugin.json    # Required metadata
├── commands/                      # Optional: slash commands
│   └── *.md                      # Command definitions
├── skills/                        # Optional: skills
│   └── <skill-name>/             # Skill directory
│       └── SKILL.md              # Required for each skill
└── README.md                      # Documentation
```

### Installed Locations
```
.claude/
├── commands/                      # Installed commands
│   └── *.md                      # Copied from plugin
└── skills/                        # Installed skills
    └── <skill-name>/             # Copied from plugin
        ├── SKILL.md
        ├── scripts/              # Scripts if present
        └── references/           # References if present
```

## See Also

- [Claude Code Skills Documentation](https://docs.claude.com/en/docs/claude-code/skills)
- [Claude Code Plugins Documentation](https://docs.claude.com/en/docs/claude-code/plugins)
- [Claude Code Slash Commands](https://docs.claude.com/en/docs/claude-code/slash-commands)
- skill-tester skill - For testing standalone skills (simpler, no plugin structure)
