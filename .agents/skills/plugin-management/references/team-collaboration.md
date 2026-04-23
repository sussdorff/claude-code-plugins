# Team Collaboration with Marketplaces

## Team Marketplace Setup

### Centralized (single repo, all team plugins)

```
company-plugins/
├── .claude-plugin/marketplace.json
├── plugins/
│   ├── code-standards/
│   ├── deployment/
│   └── testing/
└── README.md
```

```json
{
  "name": "company-engineering",
  "owner": {"name": "Engineering Team", "email": "engineering@company.com"},
  "metadata": {"description": "Standard engineering tools", "version": "2.1.0", "pluginRoot": "./plugins"},
  "plugins": [...]
}
```

### Multi-Marketplace (separate repos per team)

```json
{
  "extraKnownMarketplaces": {
    "frontend-tools": {"source": {"source": "github", "repo": "company/frontend-plugins"}},
    "backend-tools": {"source": {"source": "github", "repo": "company/backend-plugins"}}
  }
}
```

## Onboarding New Team Members

Add to project `.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "company-tools": {"source": {"source": "github", "repo": "company/claude-plugins"}}
  }
}
```

On first trust of the repository, marketplace auto-installs. Document in README:
```
## Claude Code Setup
1. Trust this repository in Claude Code
2. Install plugins: /plugin install code-standards@company-tools
```

## Governance

**Centralized**: Core team reviews all PRs. Use PR template: plugin.json ✓, README ✓, tested ✓, no secrets ✓.

**Distributed**: Use CODEOWNERS to assign team ownership per plugin directory.

**Automated validation (.github/workflows/validate.yml):**
```yaml
- name: Validate plugin.json files
  run: for plugin in plugins/*/; do jq . "$plugin/.claude-plugin/plugin.json"; done
```

## Security Checklist

- [ ] No hardcoded secrets or credentials
- [ ] Environment variables for sensitive data
- [ ] Input validation for hooks
- [ ] No arbitrary code execution
- [ ] Audit log for sensitive operations

## Versioning and Breaking Changes

Bump marketplace version on any change. Communicate breaking changes:
- Week 1: New version available (opt-in)
- Week 3: Old version deprecated  
- Week 5: Old version removed

Provide migration guide in CHANGELOG.md.

## Best Practices Summary

Maintainers: version your marketplace, document all changes, test before publishing, communicate breaking changes with migration guides.

Contributors: follow contribution guidelines, document thoroughly, test locally, respond to review feedback.
