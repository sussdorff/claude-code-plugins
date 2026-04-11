---
name: plugin-management
model: sonnet
description: Create, test, and distribute Claude Code plugins. Use when building plugins, converting skills to packages, or managing marketplace distribution. Triggers on create plugin, plugin, marketplace, distribute plugin, test plugin, plugin.json.
disableModelInvocation: true
---

# Plugin Management

Unified skill for the full plugin lifecycle: **Create** -> **Test** -> **Distribute**.

## When to Use

- Creating a new Claude Code plugin from scratch
- Converting existing skills/commands into a distributable plugin
- Testing plugins locally during development
- Setting up a marketplace for team distribution
- Deciding whether to build a plugin vs individual components

## Quick Decision: Plugin vs Components

| Scenario | Approach |
|----------|----------|
| Multiple related components that work together | Plugin |
| Single command or skill for personal use | Individual component |
| Need team standardization or enforcement | Plugin |
| Marketplace distribution desired | Plugin |
| Simple workflow for small team | Git-shared `.claude/` files |

See `references/when-to-use-plugins.md` for detailed decision guidance.

## Phase 1: Create

### Plugin Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest (required)
├── commands/                 # Slash commands (*.md)
├── skills/                   # Skills (subdirs with SKILL.md)
├── agents/                   # Specialized subagents
├── hooks/                    # Event handlers
├── mcp-servers/             # External tool integrations
└── README.md
```

### plugin.json Manifest

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "What this plugin does",
  "author": "Your Name",
  "components": {
    "commands": ["commands/*.md"],
    "skills": ["skills/*/"],
    "agents": ["agents/*/"],
    "hooks": ["hooks/*.py"]
  }
}
```

See `references/plugin-json-schema.md` for full schema and `references/plugin-structure.md` for directory layout details.

### Component Types

| Component | Purpose | User-triggered? |
|-----------|---------|-----------------|
| Commands | Slash commands (`/deploy`, `/test`) | Yes |
| Skills | Context-triggered capabilities | No (model-invoked) |
| Agents | Specialized subagent workflows | Via Task tool |
| Hooks | Event handlers (security, formatting) | Automatic |
| MCP Servers | External tool integrations | Via tool calls |

### Best Practices

See `references/best-practices.md` for:
- Plugin design principles
- Component organization
- Error handling patterns
- Documentation requirements
- Version management

## Phase 2: Test

Local testing workflow for plugins under development.

### Install Plugin Locally

```bash
# Copy plugin components to .claude/ for testing
# Commands -> .claude/commands/
# Skills -> .claude/skills/

# Manual approach:
cp -r my-plugin/commands/* .claude/commands/
cp -r my-plugin/skills/* .claude/skills/
```

### Test Cycle

1. **Validate structure** - Check plugin.json, verify all referenced files exist
2. **Install locally** - Copy components to `.claude/` directories
3. **Restart Claude Code** - Required after adding new skills/commands
4. **Test functionality** - Invoke commands, verify skill triggers
5. **Iterate** - Modify, re-install, re-test

### Validation Checklist

- [ ] `plugin.json` is valid JSON with required fields
- [ ] All referenced component files exist
- [ ] Commands have proper markdown structure
- [ ] Skills have valid frontmatter (name, description)
- [ ] Hooks are executable and handle stdin JSON
- [ ] No hardcoded absolute paths in components

## Phase 3: Distribute

### Marketplace Setup

A marketplace is a JSON catalog for centralized plugin discovery and distribution.

**Types:**
| Type | Scope | Location |
|------|-------|----------|
| Local | Development | `file:///path/to/marketplace.json` |
| Team | Organization | Git repo or internal URL |
| Public | Everyone | GitHub or hosted URL |

### marketplace.json

```json
{
  "name": "My Marketplace",
  "version": "1.0.0",
  "plugins": [
    {
      "name": "my-plugin",
      "version": "1.0.0",
      "description": "What it does",
      "source": "https://github.com/user/my-plugin",
      "components": ["commands", "skills"]
    }
  ]
}
```

See `references/marketplace-json-schema.md` for full schema and `references/marketplace-workflows.md` for distribution workflows.

### Team Distribution

See `references/team-collaboration.md` for:
- Setting up team-wide plugin standards
- Version management across teams
- Governance and approval workflows
- Migration strategies

## Do NOT

- Do NOT create a plugin for a single command or skill meant for personal use. WHY: plugins add packaging overhead (plugin.json, distribution) — use individual `.claude/` components for personal workflows.
- Do NOT hardcode absolute paths in plugin components. WHY: plugins are distributed to other machines where paths differ — use relative paths or environment variables.
- Do NOT skip plugin.json validation before distributing. WHY: invalid manifests cause silent installation failures — consumers see no error, just missing functionality.
- Do NOT install plugin components into `.claude/` without restarting Claude Code. WHY: skills and commands are only loaded at session start — changes are invisible until restart.
- Do NOT mix plugin testing with production `.claude/` state without backup. WHY: copying plugin components overwrites existing files — a broken plugin can disable working commands.

## Reference Materials

| Reference | Contents |
|-----------|----------|
| `references/when-to-use-plugins.md` | Decision tree, plugin vs components |
| `references/plugin-structure.md` | Directory layout, component specs |
| `references/plugin-json-schema.md` | Full manifest schema |
| `references/best-practices.md` | Design principles, patterns |
| `references/marketplace-json-schema.md` | Marketplace catalog schema |
| `references/marketplace-workflows.md` | Distribution workflows |
| `references/team-collaboration.md` | Team setup, governance |
| `assets/marketplace-templates/` | Starter templates |
