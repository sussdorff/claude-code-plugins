# Plugin Developer

Tools and workflows for developing Claude Code plugins locally.

## Overview

The plugin-developer plugin provides tools and workflows for iterative plugin development. It includes skills that automate the installation of plugins from development directories to `.claude/commands/` and `.claude/skills/` for local testing, handle validation, and clearly communicate when Claude Code restart is required.

This is a meta-plugin that understands the local development workflow for Claude Code plugins.

## Purpose

When developing Claude Code plugins, you need to test them locally before distribution. The plugin-developer plugin includes the plugin-tester skill which:

- Installs plugins from development directories to `.claude/` for local testing
- Validates plugin structure before installation
- Handles both commands and skills
- Clearly communicates when restart is required
- Tracks new vs update installations

## Features

### Automated Installation
- Copy commands to `.claude/commands/`
- Copy skills to `.claude/skills/`
- Preserve directory structure and file permissions
- Track what was installed for clear feedback

### Plugin Validation
- Verify `.claude-plugin/plugin.json` exists and is valid
- Check command files have proper structure
- Validate skill directories contain SKILL.md
- Report validation errors clearly

### Smart Workflow
- Detect new vs update installations
- Count installed components
- Provide restart instructions
- Show file locations for troubleshooting

## Workflow

```
1. Edit plugin files (commands, skills, scripts)
   ↓
2. Install for testing
   ./plugin-developer/skills/plugin-tester/scripts/install-plugin-for-testing.sh <plugin-name>
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

## Usage

### Install Plugin for Testing

Use the plugin-tester skill's installation script:

```bash
./plugin-developer/skills/plugin-tester/scripts/install-plugin-for-testing.sh <plugin-name>
```

**Example:**
```bash
./plugin-developer/skills/plugin-tester/scripts/install-plugin-for-testing.sh reference-file-compactor
```

**Output:**
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

## Key Concepts

### Plugins vs Skills vs Commands

**Plugins** (distribution unit):
- Contain `.claude-plugin/plugin.json` metadata
- Bundle commands, skills, agents, hooks together
- Packaged for distribution via marketplaces

**Commands** (slash commands):
- Markdown files in `commands/` directory
- User-invoked with `/command-name`
- Loaded at Claude Code startup

**Skills** (AI capabilities):
- Directories with `SKILL.md` in `skills/` directory
- Model-invoked based on SKILL.md description
- Loaded at Claude Code startup

### Local Testing vs Distribution

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

## Project Structure

```
plugin-developer/                   # Plugin package
├── .claude-plugin/
│   └── plugin.json                # Plugin metadata
├── skills/
│   ├── plugin-creator/            # Plugin creation skill
│   │   ├── SKILL.md               # Plugin development workflow
│   │   ├── references/            # Comprehensive documentation
│   │   │   ├── plugin-structure.md
│   │   │   ├── plugin-json-schema.md
│   │   │   ├── when-to-use-plugins.md
│   │   │   └── best-practices.md
│   │   └── assets/
│   │       └── plugin-template/   # Plugin template files
│   ├── marketplace-manager/       # Marketplace management skill
│   │   ├── SKILL.md               # Marketplace management workflow
│   │   ├── references/            # Comprehensive documentation
│   │   │   ├── marketplace-json-schema.md
│   │   │   ├── marketplace-workflows.md
│   │   │   └── team-collaboration.md
│   │   └── assets/
│   │       └── marketplace-templates/  # Marketplace templates
│   ├── plugin-tester/             # Plugin testing skill
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── install-plugin-for-testing.sh
│   └── skill-tester/              # Skill testing skill
│       ├── SKILL.md
│       ├── references/
│       │   └── testing-workflow.md
│       └── scripts/
│           ├── install-skill-for-testing.zsh
│           └── validate-skill.py
└── README.md                      # This file
```

## Included Skills

### plugin-creator

Comprehensive skill for creating and developing Claude Code plugins. Provides:
- Step-by-step plugin development workflow
- Decision guidance on when to use plugins vs skills
- Complete plugin structure documentation
- plugin.json schema and configuration
- Development best practices
- Plugin templates and examples

See plugin-developer/skills/plugin-creator/SKILL.md for full documentation.

### marketplace-manager

Comprehensive skill for creating and managing Claude Code plugin marketplaces. Provides:
- Step-by-step marketplace creation workflow
- marketplace.json schema and configuration
- Plugin source management (local, GitHub, Git URL)
- Team distribution and governance strategies
- Marketplace templates for quick start

See plugin-developer/skills/marketplace-manager/SKILL.md for full documentation.

### plugin-tester

Meta skill for testing plugins under development in the claude-code-plugins project. Handles:
- Installing plugins from development directories
- Local marketplace setup
- Validation and testing workflow
- Restart and iteration guidance

See plugin-developer/skills/plugin-tester/SKILL.md for full documentation.

### skill-tester

Meta skill for testing standalone skills (without plugin structure). Provides:
- Skill installation for local testing
- Validation of skill structure
- Testing workflow for skill development

See plugin-developer/skills/skill-tester/SKILL.md for full documentation.

## Plugin Structure

Plugins in this project follow the standard Claude Code plugin structure:

```
claude-code-plugins/
├── your-plugin/                   # Plugin under development
│   ├── .claude-plugin/
│   │   └── plugin.json           # Plugin metadata
│   ├── commands/                  # Optional: slash commands
│   │   └── *.md                  # Command definitions
│   ├── skills/                    # Optional: skills
│   │   └── <skill-name>/         # Skill directory
│   │       └── SKILL.md          # Required for each skill
│   └── README.md                  # Documentation
└── .claude/                       # Local testing infrastructure
    ├── commands/                  # Installed commands
    └── skills/                    # Installed skills
```

## Common Issues

### Command Doesn't Appear

**Symptoms:** `/your-command` says command not found

**Solutions:**
1. Verify command file exists: `ls .claude/commands/`
2. Check command has YAML frontmatter with description
3. Restart Claude Code (commands loaded at startup)
4. Run `/help` to see if command is registered

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

## Requirements

- `jq` - JSON parsing for plugin.json
- `rsync` - Directory copying for skills
- Bash 3.2+ (macOS compatible)

## Contributing

To enhance this plugin:

1. **Test with your plugins**: Use for developing your own plugins
2. **Report edge cases**: Plugin structures that don't install correctly
3. **Improve validation**: Additional checks for plugin quality
4. **Script improvements**: Better error handling, performance

## License

See repository LICENSE file.

## Credits

Part of the Claude Code Plugins marketplace.

**Approach**: Automated local testing workflow for Claude Code plugin development.
