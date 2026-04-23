# Marketplace Management Workflows

## Creating a Marketplace

### Quick Setup (GitHub)

```bash
mkdir my-marketplace && cd my-marketplace
git init
mkdir -p .claude-plugin plugins
cat > .claude-plugin/marketplace.json << 'EOF'
{
  "name": "my-marketplace",
  "owner": {"name": "Your Name", "email": "you@example.com"},
  "metadata": {"description": "My marketplace", "version": "1.0.0", "pluginRoot": "./plugins"},
  "plugins": []
}
EOF
git add . && git commit -m "Initial marketplace"
# push to GitHub, then: /plugin marketplace add username/my-marketplace
```

### Local Development Marketplace

```json
{
  "name": "local-dev",
  "owner": {"name": "Developer"},
  "plugins": [{"name": "test-plugin", "source": "./test-plugin"}]
}
```

## Adding Plugins

### Local plugin
```json
{
  "plugins": [
    {"name": "my-plugin", "source": "./my-plugin", "description": "...", "version": "1.0.0", "category": "development-tools"}
  ]
}
```

### GitHub plugin
```json
{
  "plugins": [
    {"name": "external-plugin", "source": {"source": "github", "repo": "username/plugin-repo", "subdir": "plugin-dir", "ref": "v1.0.0"}}
  ]
}
```

### Git URL plugin
```json
{
  "plugins": [
    {"name": "gitlab-plugin", "source": {"source": "url", "url": "https://gitlab.com/org/plugins.git", "subdir": "plugin-name", "ref": "main"}}
  ]
}
```

## Updating the Marketplace

Add/update/remove from plugins array, validate JSON, commit and push:
```bash
cat .claude-plugin/marketplace.json | jq .   # validate
git add .claude-plugin/marketplace.json
git commit -m "Update marketplace"
git push
# Users: /plugin marketplace update marketplace-name
```

## Multi-Plugin Structures

**Monorepo** (all plugins in one repo, `pluginRoot: "./plugins"`):
```
marketplace-repo/
├── .claude-plugin/marketplace.json
└── plugins/
    ├── plugin-a/
    ├── plugin-b/
    └── plugin-c/
```

**Separate repos** (marketplace.json references external GitHub repos):
```json
{"plugins": [
  {"name": "plugin-a", "source": {"source": "github", "repo": "org/plugin-a"}},
  {"name": "plugin-b", "source": {"source": "github", "repo": "org/plugin-b"}}
]}
```

## Versioning

Use semantic versioning. Pin production plugins to tags:
```json
{"source": {"source": "github", "repo": "org/plugin", "ref": "v2.1.0"}}
```

Bump marketplace `metadata.version` on any change. MAJOR = breaking (removed plugins), MINOR = new plugins, PATCH = fixes.

## Deprecation

Mark deprecated with tag + description note, announce migration path, remove after 1-2 version cycles.

## Troubleshooting

**Marketplace won't add**: Check repo exists, `.claude-plugin/marketplace.json` exists, valid JSON, required fields present.

**Plugin won't install**: Verify plugin exists in marketplace.json, source path is correct, no name conflicts.

**Updates not appearing**: Run `/plugin marketplace update marketplace-name`, then reinstall.

```bash
/plugin uninstall conflicting-plugin
/plugin install conflicting-plugin@correct-marketplace
```
