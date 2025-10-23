---
name: plugin-creator
description: This skill should be used when creating, developing, or designing Claude Code plugins. Use when the user wants to build a plugin, package commands and skills for distribution, or needs guidance on plugin structure, components, and best practices. Applicable for both new plugin creation and converting existing skills/commands into plugins.
---

# Plugin Creator

## Overview

This skill provides comprehensive guidance for creating Claude Code plugins, from initial design through implementation and distribution. Plugins are lightweight packages that bundle commands, skills, agents, hooks, and MCP servers for team standardization and marketplace distribution.

## When to Use This Skill

Use this skill when:
- Creating a new Claude Code plugin from scratch
- Converting existing skills or commands into a distributable plugin
- Designing plugin structure and choosing components
- Determining whether to build a plugin vs individual components
- Implementing plugin.json configuration
- Packaging plugins for team or marketplace distribution
- Following plugin development best practices
- Troubleshooting plugin structure or component issues

## Plugin Development Workflow

Follow this workflow for creating effective plugins. Each step references detailed guidance in the bundled references.

### Step 1: Determine If a Plugin Is Needed

Before creating a plugin, evaluate whether it's the right approach.

**Decision Criteria:**
- Multiple related components that work together? → Plugin
- Single command or skill for personal use? → Individual component
- Need team standardization or enforcement? → Plugin
- Marketplace distribution desired? → Plugin
- Simple workflow for small team? → Git-shared `.claude/` files

**Reference**: See `references/when-to-use-plugins.md` for comprehensive decision guidance, including:
- Quick decision tree
- Plugins vs Skills vs Commands comparison
- Common use cases (enforcing standards, supporting users, sharing workflows, connecting tools)
- Red flags for when NOT to use plugins
- Development progression from individual components to plugins

**Output**: Clear decision on whether to build a plugin or use individual components.

### Step 2: Design Plugin Structure

Determine which components the plugin needs and how they should be organized.

**Component Types Available:**
1. **Commands** - User-invoked slash commands (e.g., `/deploy`, `/test`)
2. **Skills** - Model-invoked capabilities with optional bundled resources
3. **Agents** - Specialized subagents for particular workflows
4. **Hooks** - Event handlers for enforcing standards or modifying behavior
5. **MCP Servers** - Connections to external tools and data sources

**Design Questions:**
- What operations should be user-triggered? → Commands
- What capabilities should Claude invoke contextually? → Skills
- What specialized workflows need dedicated agents? → Agents
- What standards or validations need enforcement? → Hooks
- What external tools need integration? → MCP Servers

**Reference**: See `references/plugin-structure.md` for:
- Complete directory layout
- Critical structure rules
- Detailed component specifications
- Progressive loading system
- Path conventions and environment variables

**Output**: Component plan specifying which types to include and their purposes.

### Step 3: Initialize Plugin Structure

Create the plugin directory structure with all required files.

**Directory Creation:**

```bash
mkdir -p plugin-name/.claude-plugin
mkdir -p plugin-name/commands      # If using commands
mkdir -p plugin-name/skills        # If using skills
mkdir -p plugin-name/agents        # If using agents
mkdir -p plugin-name/hooks         # If using hooks
```

**Template Usage:**

Copy the plugin template from assets as a starting point:

```bash
cp -r assets/plugin-template/ /path/to/plugin-name/
```

The template includes:
- `.claude-plugin/plugin.json` with all fields documented
- `README.md` with standard sections
- `commands/example-command.md` showing command structure
- `skills/example-skill/SKILL.md` showing skill structure

**Critical Rules:**
- `.claude-plugin/` contains ONLY plugin.json
- All component directories at plugin root level
- Use relative paths starting with `./`
- Skills require subdirectories with SKILL.md

**Output**: Complete plugin directory structure ready for implementation.

### Step 4: Create plugin.json Manifest

Configure the plugin metadata and component paths.

**Required Fields:**
```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Brief, clear description",
  "author": {
    "name": "Your Name"
  }
}
```

**Recommended Fields:**
- `homepage`: Documentation URL
- `repository`: Source code location
- `license`: License identifier (MIT, Apache-2.0, etc.)
- `keywords`: Array of discovery tags
- `category`: Plugin categorization

**Component Configuration:**
- `commands`: String or array of command paths (supplements `commands/`)
- `agents`: String or array of agent paths (supplements `agents/`)
- `hooks`: Path to hooks.json or inline configuration
- `mcpServers`: Inline MCP server configurations

**Reference**: See `references/plugin-json-schema.md` for:
- Complete schema with all fields
- Field descriptions and examples
- Path rules and conventions
- MCP server configuration
- Validation requirements
- Multiple real-world examples

**Output**: Complete plugin.json with proper metadata and component configuration.

### Step 5: Implement Components

Create the actual commands, skills, agents, hooks, and MCP servers.

#### Commands

Create markdown files in `commands/` directory:

**Structure:**
```markdown
---
description: Brief description of command purpose and when to use it
---

# Command Name

Detailed instructions for Claude to execute when invoked.
```

**Best Practices:**
- Use verb-noun naming (e.g., `run-tests.md`, `deploy-prod.md`)
- Keep focused on single operation
- Include concrete examples
- Provide step-by-step execution guidance

#### Skills

Create skill directories in `skills/` with SKILL.md:

**Structure:**
```markdown
---
name: skill-name
description: Specific, triggering description with keywords and scenarios
---

# Skill Name

## Overview
Brief explanation

## When to Use
Specific triggering scenarios

## How to Use
Step-by-step guidance

## Resources
References to bundled scripts, references, assets
```

**Bundled Resources:**
- `scripts/` - Executable code (Python, Bash, etc.)
- `references/` - Documentation loaded into context as needed
- `assets/` - Files used in output (templates, icons, etc.)

**Python Script Standards:**

Choose the appropriate approach based on your script's dependencies:

**Scripts with external dependencies** → Use `uv` + PEP 723:

```python
#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pyyaml>=6.0",
#   "jsonschema>=4.0",
#   "pytest>=8.0"
# ]
# ///
"""
Script description
"""

import yaml
import jsonschema
import pytest

# Your code here...
```

**Scripts with stdlib only** → Use plain Python:

```python
#!/usr/bin/env python3
"""
Script description
"""

import sys
import json
from pathlib import Path

# Your code here...
```

**Why this approach:**
- **PEP 723**: Self-contained, portable, no manual dependency installation (required for external deps)
- **Plain python3**: Simpler for stdlib-only scripts, no UV requirement

**When to use skill-level `requirements.txt` instead:**
- Only when you have importable Python modules (not just scripts)
- Example: `core/` directory with shared utilities imported by scripts

**Best Practices:**
- Descriptive name and description determine invocation
- Keep SKILL.md concise (<5k words)
- Move detailed docs to `references/`
- Use scripts for repetitive code
- Store templates in `assets/`
- Use PEP 723 + `uv` for scripts with external dependencies
- Use plain `python3` for stdlib-only scripts

#### Hooks

Create `hooks/hooks.json` or configure inline in plugin.json:

**Structure:**
```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "action": "validate|block|modify",
      "condition": "when to trigger",
      "script": "./hooks/validate.sh"
    }
  ]
}
```

**Available Events:**
- PreToolUse - Before tool execution
- PostToolUse - After tool execution
- UserPromptSubmit - When user sends prompt

**Best Practices:**
- Validate, don't block unnecessarily
- Provide clear feedback on violations
- Include escape hatches for special cases
- Test thoroughly with various workflows

#### MCP Servers

Configure in plugin.json under `mcpServers`:

**Structure:**
```json
{
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/server.js"],
      "env": {
        "API_KEY": "${ENV_VAR_NAME}"
      }
    }
  }
}
```

**Best Practices:**
- Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths
- Reference environment variables with `${VAR_NAME}`
- Document required env vars in README
- Handle connection errors gracefully

**Reference**: See `references/best-practices.md` for:
- Component-specific best practices
- Security considerations
- Performance optimization
- Testing strategies
- Common pitfalls and solutions

**Output**: Fully implemented plugin components ready for testing.

---

## Using Anthropic-Provided Skills

When creating plugins, leverage Anthropic's official skills instead of recreating functionality.

### Available Anthropic Skills

Anthropic provides comprehensive skills in the `example-skills` plugin:

**For Component Creation:**
- **skill-creator** - Guide for creating effective skills with bundled resources
- **mcp-builder** - Guide for creating MCP servers (FastMCP/Node SDK)

**For Document Skills:**
- **docx** - Word document creation/editing with tracked changes
- **xlsx** - Spreadsheet creation/editing with formulas and analysis
- **pptx** - Presentation creation/editing with layouts
- **pdf** - PDF manipulation (extract, create, merge, split, forms)

**For Development:**
- **webapp-testing** - Playwright-based web app testing

**For Design/Creative:**
- **canvas-design** - Visual art creation in PNG/PDF documents
- **algorithmic-art** - Generative art using p5.js
- **slack-gif-creator** - Animated GIFs for Slack
- **theme-factory** - Artifact styling with themes

**For Business:**
- **internal-comms** - Internal communications templates
- **brand-guidelines** - Anthropic brand colors/typography

### When to Use Anthropic Skills

**In your plugin's SKILL.md files:**

Reference Anthropic skills instead of duplicating their guidance:

```markdown
## Creating Skills

For skill authoring guidance, use Anthropic's skill-creator skill:
- Comprehensive workflow from planning to packaging
- Bundled resources best practices
- Progressive disclosure patterns
- Validation and testing guidance

To create a skill, invoke: "Use the skill-creator to help me create a new skill"
```

**In your plugin's documentation:**

```markdown
## Creating Components

### Skills
This plugin focuses on [your specific domain]. For general skill creation guidance,
use Anthropic's @skill-creator skill from the example-skills plugin.

### MCP Servers
For creating new MCP servers, use Anthropic's @mcp-builder skill which provides
comprehensive guidance on FastMCP (Python) and MCP SDK (Node/TypeScript).

### Agents
For creating agents, use the agent-creator skill from the plugin-developer plugin.
```

### Integration Pattern

**Don't duplicate** - Reference Anthropic skills in your documentation:

❌ **Bad - Duplicates Anthropic's guidance:**
```markdown
## How to Create a Skill

To create a skill:
1. Create a directory with SKILL.md
2. Add YAML frontmatter with name and description
3. Include scripts/, references/, and assets/ as needed
[... 50 more lines duplicating skill-creator ...]
```

✅ **Good - References Anthropic skill:**
```markdown
## How to Create a Skill

For comprehensive skill creation guidance, use Anthropic's skill-creator skill:

\`\`\`
"Use skill-creator to help me create a new skill for [your domain]"
\`\`\`

This plugin provides [your domain-specific] templates and examples to complement
the general skill creation workflow.
```

### Benefits

**Avoid duplication:**
- Anthropic maintains canonical skill/MCP creation guidance
- Your plugin focuses on domain-specific knowledge
- Users get consistent, up-to-date best practices

**Compose skills:**
- Anthropic skills handle general component creation
- Your plugin skills provide domain expertise
- Users benefit from both working together

**Stay current:**
- Anthropic updates their skills with latest best practices
- Your plugin doesn't need updates for component creation changes
- Users always get current guidance

### Example: Domain-Specific Plugin

**Good pattern for a database plugin:**

```markdown
## Database Plugin Components

### Creating Database Query Skills

This plugin provides database-specific query patterns and schema documentation.
For general skill creation guidance, use @skill-creator from Anthropic.

**What this plugin provides:**
- Database schema references
- Query optimization patterns
- Connection management examples
- Domain-specific templates

**What Anthropic's skills provide:**
- Skill structure and creation workflow (@skill-creator)
- MCP server creation for database connections (@mcp-builder)
```

---

### Step 6: Create Documentation

Write comprehensive README.md for users.

**Required Sections:**
1. **Title and brief description** - What the plugin does (1-2 sentences)
2. **Overview** - Detailed purpose and why it exists
3. **Features** - Bulleted list of capabilities
4. **Installation** - How to install the plugin
5. **Usage** - Examples of commands and skills
6. **Configuration** - Required setup or environment variables
7. **Components** - List of included commands, skills, agents, hooks, MCP servers
8. **Requirements** - Dependencies and prerequisites
9. **Contributing** - How to improve the plugin
10. **License** - License information

**Best Practices:**
- Include concrete examples for every command
- Document all environment variables
- Explain triggering scenarios for skills
- Show realistic use cases
- Keep instructions clear and actionable

**Template**: Use `assets/plugin-template/README.md` as starting point.

**Output**: Professional documentation that enables users to quickly understand and adopt the plugin.

### Step 7: Test Locally

Validate the plugin works correctly before distribution.

**Local Marketplace Setup:**

Create a local marketplace for testing:

```bash
# In your project root
mkdir -p .claude-plugin
cat > .claude-plugin/marketplace.json << EOF
{
  "name": "local-dev",
  "plugins": [
    {
      "name": "your-plugin",
      "source": "./your-plugin"
    }
  ]
}
EOF
```

**Installation Testing:**

```bash
# Install plugin
/plugin install your-plugin@local-dev

# Test commands
/your-command

# Test skills
(Use phrases that should trigger skills)

# Test hooks
(Perform operations that should trigger hooks)

# Test MCP servers
(Operations that use MCP connections)
```

**Validation Checklist:**
- [ ] Plugin installs without errors
- [ ] Commands appear and execute correctly
- [ ] Skills trigger appropriately
- [ ] Hooks enforce standards properly
- [ ] MCP servers connect successfully
- [ ] All components work together
- [ ] No conflicts with other plugins
- [ ] Uninstall removes cleanly

**Iteration:**

After testing:
1. Identify issues or improvements
2. Modify components
3. Uninstall and reinstall: `/plugin uninstall your-plugin` then `/plugin install your-plugin@local-dev`
4. Retest
5. Repeat until stable

**Reference**: See `references/best-practices.md` section on "Testing Strategy" for:
- Component-specific testing approaches
- Integration testing
- Edge case scenarios
- Performance validation

**Output**: Thoroughly tested plugin ready for distribution.

### Step 8: Package for Distribution

Prepare the plugin for sharing via marketplaces.

**Final Validation:**

Before distribution, ensure:
- [ ] plugin.json has correct version, description, author
- [ ] README.md is complete and accurate
- [ ] All examples work as documented
- [ ] No hardcoded secrets or credentials
- [ ] Environment variables documented
- [ ] License file included
- [ ] CHANGELOG.md created (if versioning)

**Semantic Versioning:**

Set appropriate version in plugin.json:
- `1.0.0` - Initial stable release
- `1.1.0` - Added new features (backward compatible)
- `1.0.1` - Bug fixes (backward compatible)
- `2.0.0` - Breaking changes (incompatible updates)

**Marketplace Publication:**

For team distribution:
1. Create or add to team marketplace
2. Update marketplace.json with plugin entry
3. Push to shared git repository
4. Team members trust repository and install

For public distribution:
1. Create public marketplace or submit to existing
2. Include comprehensive documentation
3. Test with clean Claude Code installation
4. Announce to community

**Reference**: See `references/best-practices.md` sections on:
- Distribution best practices
- Marketplace organization
- Version management
- Maintenance strategy

**Output**: Professionally packaged plugin ready for team or community use.

## Quick Reference

### Plugin vs Individual Components

**Use Individual Components (Skills/Commands) When:**
- Single, standalone functionality
- Personal use or small team
- Still iterating on design
- Git-based sharing sufficient

**Use Plugin When:**
- Multiple related components
- Team standardization needed
- Marketplace distribution desired
- Includes hooks or MCP servers
- Professional packaging required

### Common Plugin Patterns

**1. Enforcement Plugin**
- Hooks (standards enforcement)
- Commands (standardized operations)
- Skills (guidance)

**2. Tool Integration Plugin**
- MCP Servers (tool connections)
- Commands (tool operations)
- Skills (usage patterns)

**3. Workflow Plugin**
- Commands (workflow triggers)
- Skills (procedural knowledge)
- Scripts (automation)

**4. Support Plugin**
- Commands (common operations)
- Skills (usage guidance)
- Assets (templates)

### Key Resources

**Detailed References:**
- `references/plugin-structure.md` - Complete structure specifications
- `references/plugin-json-schema.md` - plugin.json format and fields
- `references/when-to-use-plugins.md` - Decision guidance
- `references/best-practices.md` - Development best practices

**Templates:**
- `assets/plugin-template/` - Complete plugin template with examples

## Troubleshooting

### Plugin Won't Install

**Check:**
- plugin.json exists at `.claude-plugin/plugin.json`
- JSON is valid (no syntax errors)
- Required `name` field present
- Component directories at plugin root (not inside `.claude-plugin/`)

### Command Doesn't Appear

**Check:**
- Command file in `commands/` directory
- Markdown has YAML frontmatter with description
- Plugin installed successfully
- Restarted Claude Code after installation

### Skill Doesn't Trigger

**Check:**
- Skill has SKILL.md in `skills/skill-name/` structure
- YAML frontmatter has name and description
- Description includes triggering keywords
- Description is specific enough to match use cases

### Hook Not Working

**Check:**
- hooks.json exists or inline configuration correct
- Hook event name matches available events
- Hook script is executable
- Script returns proper exit codes
- Hook doesn't block normal workflows

### MCP Server Won't Connect

**Check:**
- Environment variables set correctly
- Server command executable
- `${CLAUDE_PLUGIN_ROOT}` used for plugin-relative paths
- Network connectivity (if remote service)
- Error messages in Claude Code logs

## Examples

### Example 1: Simple Command Plugin

**Purpose**: Add deployment shortcuts

**Components**:
- Commands: `/deploy-staging`, `/deploy-prod`

**Structure**:
```
deploy-helper/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── deploy-staging.md
│   └── deploy-prod.md
└── README.md
```

### Example 2: Database Helper Plugin

**Purpose**: Database query assistance

**Components**:
- Skill: Query guidance with schema docs
- Commands: `/query-db`, `/explain-schema`
- MCP Server: Database connection

**Structure**:
```
database-helper/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── query-db.md
│   └── explain-schema.md
├── skills/
│   └── database-query/
│       ├── SKILL.md
│       └── references/
│           └── schema.md
├── .mcp.json
└── README.md
```

### Example 3: Code Review Enforcer Plugin

**Purpose**: Enforce review standards

**Components**:
- Hook: Pre-commit validation
- Commands: `/review`, `/check-standards`
- Skill: Review guidance

**Structure**:
```
code-review-enforcer/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── review.md
│   └── check-standards.md
├── skills/
│   └── code-review/
│       ├── SKILL.md
│       └── references/
│           └── standards.md
├── hooks/
│   ├── hooks.json
│   └── validate.sh
└── README.md
```

## Summary

Create effective Claude Code plugins by:
1. **Deciding**: Confirm plugin is the right approach
2. **Designing**: Choose appropriate components
3. **Initializing**: Set up proper directory structure
4. **Configuring**: Create plugin.json manifest
5. **Implementing**: Build commands, skills, agents, hooks, MCP servers
6. **Documenting**: Write comprehensive README
7. **Testing**: Validate with local marketplace
8. **Distributing**: Package for team or community

Leverage the bundled references for detailed guidance on structure, configuration, decision-making, and best practices throughout the development process.
