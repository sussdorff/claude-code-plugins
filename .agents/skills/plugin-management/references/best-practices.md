# Plugin Development Best Practices

## Development Workflow

1. **Develop individually** — create commands/skills in `.claude/` first, test with real tasks
2. **Bundle when stable** — package as plugin after proving value
3. **Use local marketplace for testing** — mimics real installation, catches integration issues early

```json
// Local test marketplace.json
{"name": "local-dev", "plugins": [{"name": "my-plugin", "source": "./my-plugin"}]}
```

After changes: `/plugin uninstall my-plugin && /plugin install my-plugin@local-dev`

## Design Principles

**Single Responsibility**: One clear purpose per plugin. "database-query-helper" not "dev-tools".

**Progressive Disclosure**: Keep SKILL.md concise, move details to `references/`. Use scripts for code, not inline markdown.

**Composability**: Plugins should work independently — no hard dependencies on other plugins.

**Semantic Versioning**: MAJOR = breaking, MINOR = new features, PATCH = fixes.

## Component Guidelines

**Commands**: Use verb-noun format (`/run-tests`, `/deploy-prod`). Each command does one thing. Include examples.

**Skills**: Descriptive SKILL.md triggers correct invocation. Keep under 5k words, move patterns to `references/`. Use scripts over inline code.

**Hooks**: Validate, don't over-block. Provide clear feedback: what was caught, why it's a problem, how to fix it.

**MCP Servers**: Use `${CLAUDE_PLUGIN_ROOT}/server.js` not absolute paths. Document required env vars in README.

## Security

- Never hardcode secrets — use `${ENV_VAR}` in plugin.json, document in README
- Validate inputs in hooks (sanitize file paths, check for injection)
- Request minimal permissions in MCP servers

## Documentation

Every plugin needs README.md covering: overview, features, installation, usage examples, configuration, component list, requirements.

## Pre-Release Checklist

- [ ] All components tested (individually + integrated)
- [ ] README complete and accurate
- [ ] plugin.json has version, description, author
- [ ] No hardcoded secrets
- [ ] Examples for all commands
- [ ] Skill descriptions trigger appropriately
- [ ] Scripts have error handling
- [ ] Environment variables documented

## Maintenance

- Update version in plugin.json with every release
- Maintain CHANGELOG.md
- Deprecation path: document → warn → remove in next major (provide migration guide)
- Keep backward compatibility within major versions
