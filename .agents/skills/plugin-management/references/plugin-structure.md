# Plugin Structure Reference

## Directory Layout

Standard plugin structure follows this hierarchy:

```
plugin-root/
├── .claude-plugin/
│   └── plugin.json           # Required manifest with metadata
├── commands/                  # Optional: Slash commands
│   └── command-name.md       # User-invoked commands
├── agents/                    # Optional: Specialized subagents
│   └── agent-name.md         # Context-invoked agents
├── skills/                    # Optional: Agent Skills
│   └── skill-name/           # Skill directory
│       ├── SKILL.md          # Required for each skill
│       ├── scripts/          # Optional: Executable scripts
│       ├── references/       # Optional: Documentation
│       └── assets/           # Optional: Output resources
├── hooks/                     # Optional: Event handlers
│   └── hooks.json            # Hook configurations
├── .mcp.json                 # Optional: MCP server config
└── README.md                 # Documentation for users
```

## Critical Rules

1. **Manifest Location**: The `.claude-plugin/` directory contains ONLY the plugin.json manifest
2. **Component Directories**: All other directories (commands, agents, skills, hooks) must exist at the plugin root level
3. **Path Format**: All paths in plugin.json must be relative and start with `./`
4. **Environment Variable**: Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths in configurations

## Five Component Types

### 1. Commands

Markdown files that create custom slash commands for frequently-used operations.

**Location**: `commands/` directory (default) or custom path in plugin.json
**Format**: Markdown with YAML frontmatter
**Invocation**: User-triggered via `/command-name`
**Use Case**: Shortcuts for common operations

Example command file structure:
```markdown
---
description: Brief description of what this command does
---

# Command Instructions

Detailed instructions for Claude to execute when this command is invoked.
```

### 2. Agents

Specialized subagents for particular development tasks, invoked contextually by Claude.

**Location**: `agents/` directory (default) or custom path in plugin.json
**Format**: Markdown with agent instructions
**Invocation**: Model-invoked based on context
**Use Case**: Purpose-built agents for specialized workflows

### 3. Skills

Agent Skills that extend Claude's capabilities with specialized knowledge and workflows.

**Location**: `skills/` directory with subdirectories for each skill
**Format**: Each skill requires `SKILL.md` with YAML frontmatter
**Invocation**: Model-invoked based on skill description
**Use Case**: Modular capabilities with bundled resources
**Discovery**: "Plugin Skills are automatically discovered when the plugin is installed"

Each skill can include:
- `SKILL.md` - Required, contains instructions
- `scripts/` - Optional, executable code
- `references/` - Optional, reference documentation
- `assets/` - Optional, files for output

### 4. Hooks

Event handlers that customize Claude Code's behavior at key workflow points.

**Location**: `hooks/hooks.json` or inline in plugin.json
**Format**: JSON configuration with event matchers and actions
**Events**: PreToolUse, PostToolUse, UserPromptSubmit, etc.
**Use Case**: Enforce standards, add validation, customize behavior

Hook configuration structure:
```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "action": "block or modify",
      "condition": "when to trigger"
    }
  ]
}
```

### 5. MCP Servers

Connections to external tools and data sources via Model Context Protocol.

**Location**: `.mcp.json` or inline in plugin.json under `mcpServers`
**Format**: JSON with command, args, and environment variables
**Use Case**: Connect to internal tools, APIs, and data sources
**Portability**: Use `${CLAUDE_PLUGIN_ROOT}` for relative paths

Example MCP server configuration:
```json
{
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/server.js"],
      "env": {
        "API_KEY": "${ENV_VAR}"
      }
    }
  }
}
```

## Progressive Loading System

Plugins use a three-level loading approach:

1. **Metadata** - Always loaded (name + description from plugin.json)
2. **Component Files** - Loaded when plugin functionality is invoked
3. **Bundled Resources** - Loaded as needed by Claude during execution

This design minimizes context usage while maintaining full capability access.

## Component Discovery

**Default Discovery**: Claude automatically discovers components in standard directories:
- `commands/` for slash commands
- `agents/` for subagents
- `skills/` for Agent Skills
- `hooks/hooks.json` for hooks
- `.mcp.json` for MCP servers

**Custom Paths**: Use plugin.json fields to specify additional or alternative locations:
- `commands`: String or array of paths
- `agents`: String or array of paths
- `hooks`: Path to hooks.json or inline configuration
- `mcpServers`: Inline configuration referencing plugin files

**Supplementary Nature**: Custom paths supplement (not replace) default directories.

## Path Conventions

**Relative Paths**: All paths must be relative to plugin root
**Correct Format**: `./path/to/file` or `./directory`
**Array Format**: `["./commands", "./custom-commands"]`
**Environment Variables**: `${CLAUDE_PLUGIN_ROOT}` for portability

## Distribution Structure

When distributing, maintain this structure in your repository:

```
repository-root/
├── plugin-name/              # Plugin directory
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── commands/
│   ├── skills/
│   └── README.md
└── .claude-plugin/           # Marketplace manifest
    └── marketplace.json
```

The marketplace.json enables discovery, while each plugin subdirectory contains the complete plugin structure.
