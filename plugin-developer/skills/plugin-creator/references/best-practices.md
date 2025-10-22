# Plugin Development Best Practices

## Development Workflow

### Start Local, Ship When Ready

1. **Develop individually**: Create commands/skills in `.claude/` first
2. **Test thoroughly**: Use with real tasks, iterate on design
3. **Bundle when stable**: Package as plugin after proving value
4. **Publish thoughtfully**: Share via marketplace when ready

**Why**: Plugins are harder to iterate on than individual files. Perfect the components first.

### Use Local Marketplaces for Testing

Create a local marketplace for development testing:

```bash
# Project structure for development
project/
├── .claude-plugin/
│   └── marketplace.json          # Local marketplace
└── my-plugin/
    ├── .claude-plugin/
    │   └── plugin.json
    ├── commands/
    └── skills/
```

marketplace.json:
```json
{
  "name": "local-dev",
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./my-plugin"
    }
  ]
}
```

Install and test:
```bash
/plugin install my-plugin@local-dev
```

**Why**: Mimics real installation, catches integration issues early.

### Iterate with Uninstall/Reinstall

After changes:
```bash
/plugin uninstall my-plugin
/plugin install my-plugin@local-dev
```

**Why**: Ensures Claude loads latest version, prevents stale cache issues.

## Plugin Design Principles

### Single Responsibility

Each plugin should have a clear, focused purpose.

✅ **Good**: "database-query-helper" - database operations
❌ **Bad**: "dev-tools" - database + git + testing + deployment

**Why**: Focused plugins are easier to understand, maintain, and toggle on/off.

### Progressive Disclosure

Minimize what loads into context by default:

1. **Metadata only**: Name and description always loaded
2. **Components on demand**: Commands/skills loaded when triggered
3. **Resources as needed**: Scripts executed, references read when required

**Implementation**:
- Keep SKILL.md concise, move details to references/
- Use scripts for deterministic operations
- Store templates in assets/ not inline in markdown

**Why**: Reduces context window usage, improves Claude performance.

### Composability

Design plugins to work independently and together.

✅ **Good**: Database plugin + Testing plugin + Code Review plugin (each standalone)
❌ **Bad**: Database plugin requires Testing plugin to function

**Why**: Users can mix and match, easier to maintain, clearer dependencies.

### Semantic Versioning

Use MAJOR.MINOR.PATCH versioning:

- **MAJOR**: Breaking changes (incompatible updates)
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Examples:
- `1.0.0` → `1.1.0`: Added new command (minor)
- `1.1.0` → `1.1.1`: Fixed command bug (patch)
- `1.1.1` → `2.0.0`: Changed command syntax (major)

**Why**: Teams can pin versions, understand update impact.

## Component Best Practices

### Commands

**Clear Names**: Use verb-noun format
- ✅ `/run-tests`, `/deploy-prod`, `/query-db`
- ❌ `/test`, `/prod`, `/db`

**Focused Scope**: Each command does one thing well
- ✅ `/deploy-staging`, `/deploy-prod` (separate)
- ❌ `/deploy --env staging` (complex flags)

**Helpful Descriptions**: Explain what, when, and why
```markdown
---
description: Run full test suite with coverage report, typically before PR creation
---
```

**Why**: Users can discover and understand commands quickly.

### Skills

**Descriptive SKILL.md**: Name and description determine invocation
```yaml
---
name: database-query
description: This skill should be used when querying SQL databases, writing complex queries, or analyzing database schemas. Use for PostgreSQL, MySQL, and SQLite databases.
---
```

**Move Details to References**: Keep SKILL.md under 5k words
- SKILL.md: "See references/query-patterns.md for advanced patterns"
- references/query-patterns.md: 50+ example queries

**Use Scripts for Code**: Avoid rewriting the same code
- ❌ SKILL.md with inline Python script
- ✅ scripts/analyze.py + SKILL.md: "Execute scripts/analyze.py"

**Why**: Efficient context usage, easier maintenance.

### Hooks

**Validate, Don't Block Unnecessarily**

✅ **Good**: Warn about missing tests, allow override
❌ **Bad**: Block all commits without tests

**Provide Clear Feedback**

Hook responses should explain:
- What was caught
- Why it's a problem
- How to fix it

**Test Thoroughly**: Hooks affect all operations
- Test with various tool combinations
- Ensure hooks don't break normal workflows
- Provide escape hatches

**Why**: Hooks are powerful but can frustrate if too restrictive.

### MCP Servers

**Use Plugin Root Variable**

✅ `"${CLAUDE_PLUGIN_ROOT}/server.js"`
❌ `/absolute/path/to/server.js`

**Document Environment Variables**

In README.md, explain required env vars:
```markdown
## Setup

Required environment variables:
- `API_KEY`: Your API key from dashboard
- `API_URL`: API endpoint (default: https://api.example.com)
```

**Handle Errors Gracefully**

MCP servers should:
- Validate configuration on startup
- Return clear error messages
- Fail safely if service unavailable

**Why**: Portable installations, better user experience.

## Documentation Best Practices

### README.md Structure

Every plugin should include:

```markdown
# Plugin Name

Brief description (1-2 sentences)

## Overview
What the plugin does and why it exists

## Features
- Feature 1
- Feature 2
- Feature 3

## Installation
How to install the plugin

## Usage
Examples of commands and skills

## Configuration
Required setup or environment variables

## Components
List of included commands, skills, agents, hooks, MCP servers

## Requirements
Dependencies, environment prerequisites

## Contributing
How others can improve the plugin

## License
```

**Why**: Users can quickly understand and start using the plugin.

### Component Documentation

Each command/skill should document:
- **Purpose**: What it does
- **When to use**: Triggering scenarios
- **Examples**: Realistic use cases
- **Requirements**: Prerequisites or setup

**Why**: Self-documenting, reduces support burden.

## Security Best Practices

### Never Hardcode Secrets

❌ **Bad**:
```json
{
  "mcpServers": {
    "api": {
      "env": {
        "API_KEY": "sk_live_abc123xyz"
      }
    }
  }
}
```

✅ **Good**:
```json
{
  "mcpServers": {
    "api": {
      "env": {
        "API_KEY": "${COMPANY_API_KEY}"
      }
    }
  }
}
```

Document in README:
```markdown
## Setup

Set the following environment variables:
export COMPANY_API_KEY="your-key-here"
```

### Validate Inputs

For hooks that process user input:
- Sanitize file paths
- Validate command arguments
- Check for injection attempts

### Minimal Permissions

MCP servers and scripts should:
- Request only necessary permissions
- Fail safely if permissions denied
- Document what access they need

**Why**: Protects users and their data.

## Testing Strategy

### Test Each Component

**Commands**: Invoke with typical arguments
```bash
/your-command arg1 arg2
```

**Skills**: Use in realistic scenarios
```
"Query the database for users who signed up this week"
```

**Hooks**: Trigger events intentionally
```
# Test PreToolUse hook
(attempt tool use that should be caught)
```

**MCP Servers**: Verify connections
```
# Check server responds
(test typical MCP server operations)
```

### Test Integration

Install full plugin and verify:
- All components load correctly
- Components work together as expected
- No conflicts with other plugins
- Uninstall removes cleanly

### Test Edge Cases

- Missing environment variables
- Invalid inputs
- Network failures (for MCP servers)
- Large files or datasets
- Concurrent operations

**Why**: Robust plugins handle failures gracefully.

## Performance Optimization

### Lazy Loading

Load resources only when needed:
- Don't read all references upfront
- Execute scripts on demand
- Load MCP servers when first used

### Efficient Context Usage

- Keep SKILL.md concise (<5k words)
- Use grep patterns for large references
- Store generated code in scripts, not markdown

### Caching

For expensive operations:
- Cache API responses when appropriate
- Store computed results temporarily
- Document cache invalidation

**Why**: Fast response times, better user experience.

## Maintenance Best Practices

### Version Updates

When releasing updates:
1. Update version in plugin.json
2. Document changes in CHANGELOG.md
3. Test against previous version for compatibility
4. Announce breaking changes clearly

### Deprecation Strategy

When removing features:
1. Mark as deprecated in docs (1 version)
2. Add warnings when used (1 version)
3. Remove in next major version
4. Provide migration guide

### Backward Compatibility

Maintain compatibility within major versions:
- Don't remove commands
- Don't change command behavior
- Don't require new environment variables
- Add new features as additions

**Why**: Users can update without breaking workflows.

## Distribution Best Practices

### Marketplace Organization

Group related plugins:
```
marketplace/
├── .claude-plugin/
│   └── marketplace.json
├── database-tools/
├── testing-tools/
└── deployment-tools/
```

### Clear Naming

Plugin names should be:
- Lowercase with hyphens
- Descriptive of functionality
- Consistent with content

✅ `database-query-helper`
❌ `dbHelper`, `db_query`, `DatabaseStuff`

### Categories and Keywords

Help users discover plugins:
```json
{
  "category": "database",
  "keywords": ["sql", "postgres", "mysql", "query", "database"]
}
```

### License Selection

Choose appropriate license:
- **MIT**: Permissive, easy adoption
- **Apache-2.0**: Permissive with patent protection
- **GPL-3.0**: Copyleft, requires derivatives be open source

**Why**: Clear legal expectations, easier adoption.

## Common Pitfalls

### ❌ Over-Engineering

Starting with complex plugin before validating need.

**Fix**: Build individual components first, bundle when proven.

### ❌ Poor Descriptions

Vague skill descriptions that don't trigger:
```yaml
description: A helpful skill
```

**Fix**: Specific, triggering descriptions:
```yaml
description: This skill should be used when querying SQL databases or writing complex JOIN queries
```

### ❌ Tight Coupling

Plugin requires specific other plugins:
```markdown
Note: This plugin requires the database-plugin to be installed first.
```

**Fix**: Make plugins independent, document integrations as optional.

### ❌ Stale Documentation

README doesn't match current functionality.

**Fix**: Update docs with every feature change, review before release.

### ❌ No Examples

Commands without usage examples:
```markdown
# Deploy Command
Deploys the application.
```

**Fix**: Show realistic examples:
```markdown
# Deploy Command

Deploy application to specified environment.

## Examples

/deploy-staging
/deploy-prod

Use /deploy-staging before creating PR to test in staging environment.
```

## Checklist Before Publishing

Pre-release validation:

- [ ] All components tested individually
- [ ] Full plugin installed and tested
- [ ] README.md complete and accurate
- [ ] plugin.json has version, description, author
- [ ] No hardcoded secrets or credentials
- [ ] Examples included for all commands
- [ ] Skill descriptions trigger appropriately
- [ ] Scripts have proper error handling
- [ ] Environment variables documented
- [ ] License file included
- [ ] CHANGELOG.md created
- [ ] Tested with clean Claude Code installation

**Why**: Professional plugins ready for distribution.
