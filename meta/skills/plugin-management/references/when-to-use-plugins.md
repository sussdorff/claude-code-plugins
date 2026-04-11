# When to Use Plugins: Decision Guide

## Quick Decision Tree

```
Need to customize Claude Code?
│
├─ Single capability for personal use?
│  └─ Use: Individual skill or command in .claude/
│
├─ Share across team/projects?
│  ├─ Single command or workflow?
│  │  └─ Consider: Standalone command or skill first
│  │
│  └─ Multiple related components?
│     └─ Use: Plugin
│
└─ Distribution to wider community?
   └─ Use: Plugin (via marketplace)
```

## Plugins vs Skills vs Commands

### Use Individual Commands When:

**Scenario**: Single-purpose, user-invoked shortcuts

- Creating shortcuts for frequently-used operations
- Simple, standalone functionality
- User knows exactly when to invoke it
- No need for bundled resources
- Personal use or small team sharing via git

**Example**: `/run-tests` command that executes test suite

**Distribution**: Copy `.md` file to `.claude/commands/` directory

### Use Individual Skills When:

**Scenario**: Model-invoked capabilities with optional resources

- Specialized knowledge or workflows Claude should use contextually
- Might include bundled scripts, references, or assets
- Claude determines when to use it based on description
- Domain-specific expertise
- Personal use or team sharing via git

**Example**: Database query skill with schema documentation

**Distribution**: Copy skill directory to `.claude/skills/`

### Use Plugins When:

**Scenario**: Distribution unit for multiple components

✅ **Bundle multiple related components together**
- Commands + Skills that work together
- Commands + Hooks for enforcement
- Skills + MCP servers for tool integration
- Complete workflow solutions

✅ **Team standardization**
- Enforce coding standards across team
- Lock in mandatory workflows
- Ensure consistent tooling setup
- Repository-level configuration

✅ **Marketplace distribution**
- Share with wider community
- Version management needed
- Professional packaging
- Discovery through marketplaces

✅ **Complex integrations**
- MCP server connections requiring setup
- Hooks that modify Claude Code behavior
- Multi-component systems
- Configuration management

**Example**: "Code Review Enforcer" plugin with:
- `/review` command for initiating reviews
- Pre-commit hook for validation
- Code review skill for guidance
- Jira integration via MCP server

**Distribution**: Package as plugin, publish to marketplace

## Common Use Cases

### Enforcing Standards

**When to use plugins**: Team leads need to lock in workflows

**Example scenarios**:
- Force code reviews before PRs
- Run mandatory tests on every commit
- Enforce commit message formats
- Validate code style automatically

**Components**:
- Hooks (enforce policies)
- Commands (standardized workflows)
- Skills (guidance on standards)

**Why plugin**: Bundled enforcement + education, team-wide consistency

### Supporting Users

**When to use plugins**: Open source maintainers helping developers

**Example scenarios**:
- Package setup commands for complex libraries
- Common troubleshooting workflows
- API usage examples and guidance
- Integration templates

**Components**:
- Commands (setup shortcuts)
- Skills (usage guidance)
- Assets (configuration templates)

**Why plugin**: Complete support experience, reduces GitHub issues

### Sharing Workflows

**When to use plugins**: Perfected workflows worth sharing

**Example scenarios**:
- Debugging setup with specific tools
- Deployment pipelines
- Testing strategies
- Performance optimization workflows

**Components**:
- Commands (workflow triggers)
- Skills (procedural knowledge)
- Scripts (automation)
- References (best practices)

**Why plugin**: Package entire workflow, easy team adoption

### Connecting Tools

**When to use plugins**: Internal/external service integration

**Example scenarios**:
- Connect to company APIs
- Database query tools
- Project management integration (Jira, Linear)
- Documentation access

**Components**:
- MCP servers (tool connections)
- Commands (tool operations)
- Skills (tool usage guidance)

**Why plugin**: Proper security, configuration, and setup handling

### Bundling Customizations

**When to use plugins**: Multiple customizations that work together

**Example scenarios**:
- Company-wide development environment
- Framework-specific tooling
- Project template with commands and skills
- Language-specific helpers

**Components**:
- Any combination of commands, skills, agents, hooks, MCP servers

**Why plugin**: Cohesive experience, single installation

## Plugin vs Skill: Detailed Comparison

| Aspect | Skill | Plugin |
|--------|-------|--------|
| **Purpose** | Single capability | Distribution unit |
| **Invocation** | Model-determined | Installation-based |
| **Components** | SKILL.md + bundled resources | Commands, Skills, Agents, Hooks, MCP servers |
| **Distribution** | Git repository, manual copy | Marketplace, `/plugin install` |
| **Versioning** | Git-based | plugin.json version field |
| **Discovery** | Description in SKILL.md | Marketplace listing |
| **Sharing** | Copy directory | Package and publish |
| **Team Use** | Manual installation | Repository-level auto-install |
| **Updates** | Git pull | Plugin update command |

## Red Flags (When NOT to Use Plugins)

❌ **Single simple command** → Use standalone command in `.claude/commands/`

❌ **Personal-only use** → Use individual skills/commands

❌ **No need for distribution** → Git repository with `.claude/` contents

❌ **Experimental/changing rapidly** → Develop as individual components first

❌ **Very specific to one project** → Project-level `.claude/` directory

## Development Progression

Typical evolution from concept to plugin:

```
1. Individual Command/Skill
   ↓ (works well, want to add related features)
2. Multiple Commands/Skills in .claude/
   ↓ (want to share with team)
3. Git Repository with .claude/ contents
   ↓ (ready for wider distribution)
4. Plugin with marketplace.json
   ↓ (publishing)
5. Marketplace Distribution
```

**Key insight**: Don't start with a plugin. Develop components individually, then package as plugin when ready for distribution.

## Team vs Personal vs Public

### Personal Use
- **Location**: `~/.claude/skills/` and `~/.claude/commands/`
- **Scope**: Just you
- **Sharing**: Not shared
- **Best for**: Experimental, personal productivity

### Team Use (Option 1: Direct)
- **Location**: Project `.claude/skills/` and `.claude/commands/`
- **Scope**: Project team
- **Sharing**: Via git repository
- **Best for**: Project-specific tools, quick sharing

### Team Use (Option 2: Plugin)
- **Location**: Plugin via marketplace
- **Scope**: Organization or team
- **Sharing**: Repository-level `.claude/settings.json` auto-installs
- **Best for**: Standardization, enforcement, consistency

### Public Distribution
- **Location**: Public marketplace
- **Scope**: Community
- **Sharing**: Marketplace discovery
- **Best for**: Open source support, community tools

## Decision Checklist

Use this checklist to decide between individual components and plugins:

**Use Individual Command/Skill if**:
- [ ] Single, standalone functionality
- [ ] Personal use or small team
- [ ] No need for bundling
- [ ] Git-based sharing is sufficient
- [ ] Still iterating on design

**Use Plugin if**:
- [ ] Multiple related components
- [ ] Need version management
- [ ] Team-wide standardization required
- [ ] Marketplace distribution desired
- [ ] Includes MCP servers or hooks
- [ ] Professional packaging needed
- [ ] Repository-level auto-install wanted

## Real-World Examples

### Example 1: Database Query Helper

**Initial approach**: Skill with SQL query patterns
**When to become plugin**: Add MCP server for database connection
**Final structure**:
- `database-helper` plugin with:
  - Query skill (guidance)
  - `/query` command (shortcuts)
  - MCP server (connection)
  - References (schema docs)

### Example 2: Code Review Standards

**Initial approach**: Hook in `.claude/hooks/`
**When to become plugin**: Add command and documentation skill
**Final structure**:
- `code-review-enforcer` plugin with:
  - Pre-commit hook (enforcement)
  - `/review` command (initiate review)
  - Review skill (guidance)
  - References (standards docs)

### Example 3: API Client Helper

**Initial approach**: Command with API examples
**When to become plugin**: Team wants standardized tool
**Final structure**:
- `api-client` plugin with:
  - Commands (API operations)
  - Skill (usage patterns)
  - MCP server (authentication)
  - Assets (request templates)

## Summary

**Start small**: Individual commands or skills
**Bundle when**: Multiple components work together
**Use plugins for**: Distribution, standardization, and team consistency
**Marketplace when**: Ready for public or wide organizational use
