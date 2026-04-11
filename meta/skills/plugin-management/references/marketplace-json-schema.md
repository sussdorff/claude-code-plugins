# marketplace.json Schema Reference

## File Location

Required location: `.claude-plugin/marketplace.json`

This file must be at the root of your marketplace repository.

## Complete Schema

```json
{
  "name": "string (required)",
  "owner": {
    "name": "string (required)",
    "email": "string (optional)"
  },
  "metadata": {
    "description": "string (optional)",
    "version": "string (optional)",
    "pluginRoot": "string (optional, base path for relative sources)"
  },
  "plugins": [
    {
      "name": "string (required)",
      "source": "string or object (required)",
      "description": "string (optional)",
      "version": "string (optional)",
      "author": {
        "name": "string",
        "email": "string"
      },
      "homepage": "string (optional)",
      "repository": "string (optional)",
      "license": "string (optional)",
      "keywords": ["array", "of", "strings"],
      "category": "string (optional)",
      "tags": ["array", "of", "strings"],
      "strict": "boolean (default: true)",
      "commands": "string or array (optional)",
      "agents": "string or array (optional)",
      "hooks": "string or object (optional)",
      "mcpServers": "object (optional)"
    }
  ]
}
```

## Required Fields

### name
- **Type**: String
- **Required**: Yes
- **Description**: Unique identifier for the marketplace
- **Format**: Kebab-case (e.g., `team-plugins`, `my-marketplace`)

```json
{
  "name": "team-plugins"
}
```

### owner
- **Type**: Object
- **Required**: Yes
- **Fields**:
  - `name` (required): Person or organization maintaining the marketplace
  - `email` (optional): Contact email

```json
{
  "owner": {
    "name": "Engineering Team",
    "email": "engineering@company.com"
  }
}
```

### plugins
- **Type**: Array
- **Required**: Yes
- **Description**: List of available plugins in the marketplace

```json
{
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./plugins/my-plugin"
    }
  ]
}
```

## Optional Marketplace Fields

### metadata
- **Type**: Object
- **Purpose**: Additional marketplace information

**Fields**:
- `description`: Brief overview of marketplace purpose
- `version`: Marketplace version (semantic versioning)
- `pluginRoot`: Base path for relative plugin sources

```json
{
  "metadata": {
    "description": "Internal tools and workflows for the engineering team",
    "version": "1.2.0",
    "pluginRoot": "./plugins"
  }
}
```

## Plugin Entry Fields

### name (plugin)
- **Type**: String
- **Required**: Yes (in each plugin entry)
- **Description**: Plugin identifier, must match plugin's plugin.json name
- **Format**: Kebab-case

```json
{
  "plugins": [
    {
      "name": "database-helper"
    }
  ]
}
```

### source (plugin)
- **Type**: String or Object
- **Required**: Yes (in each plugin entry)
- **Description**: Location to fetch the plugin from

**Three formats supported:**

**1. Relative Path** (for local development):
```json
{
  "source": "./plugins/my-plugin"
}
```

**2. GitHub Repository**:
```json
{
  "source": {
    "source": "github",
    "repo": "owner/repository",
    "subdir": "plugins/my-plugin"
  }
}
```

Optional GitHub fields:
- `subdir`: Path within repository to plugin
- `ref`: Branch, tag, or commit SHA
- `path`: Alternative to subdir

**3. Git URL**:
```json
{
  "source": {
    "source": "url",
    "url": "https://gitlab.com/org/plugins.git",
    "subdir": "my-plugin",
    "ref": "main"
  }
}
```

### Plugin Metadata Override

Plugin entries can override or supplement metadata from the plugin's plugin.json:

```json
{
  "plugins": [
    {
      "name": "database-helper",
      "source": "./plugins/database-helper",
      "description": "Override description for marketplace",
      "version": "2.1.0",
      "author": {
        "name": "Database Team"
      },
      "homepage": "https://docs.company.com/database-plugin",
      "repository": "https://github.com/company/database-helper",
      "license": "MIT",
      "keywords": ["database", "sql", "postgres"],
      "category": "database-tools",
      "tags": ["internal", "production"]
    }
  ]
}
```

### strict
- **Type**: Boolean
- **Default**: true
- **Purpose**: Require plugin.json in plugin directory

```json
{
  "plugins": [
    {
      "name": "legacy-plugin",
      "source": "./legacy",
      "strict": false
    }
  ]
}
```

When `strict: false`, plugin can omit plugin.json and define components directly in marketplace.json.

### Component Configuration

Override component paths in marketplace.json:

```json
{
  "plugins": [
    {
      "name": "custom-plugin",
      "source": "./custom",
      "commands": ["./commands", "./extra-commands"],
      "agents": "./specialized-agents",
      "hooks": {
        "PreToolUse": {
          "action": "validate",
          "script": "./hooks/validate.sh"
        }
      },
      "mcpServers": {
        "api": {
          "command": "node",
          "args": ["./server.js"]
        }
      }
    }
  ]
}
```

## Complete Examples

### Minimal Marketplace

```json
{
  "name": "my-marketplace",
  "owner": {
    "name": "Your Name"
  },
  "plugins": [
    {
      "name": "simple-plugin",
      "source": "./plugins/simple-plugin"
    }
  ]
}
```

### Local Development Marketplace

```json
{
  "name": "local-dev",
  "owner": {
    "name": "Development Team",
    "email": "dev@company.com"
  },
  "metadata": {
    "description": "Local marketplace for plugin development and testing",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "plugin-one",
      "source": "./plugin-one"
    },
    {
      "name": "plugin-two",
      "source": "./plugin-two"
    },
    {
      "name": "plugin-three",
      "source": "./plugin-three"
    }
  ]
}
```

### GitHub-Based Team Marketplace

```json
{
  "name": "engineering-tools",
  "owner": {
    "name": "Engineering Team",
    "email": "engineering@company.com"
  },
  "metadata": {
    "description": "Standardized tools and workflows for engineering team",
    "version": "2.3.0"
  },
  "plugins": [
    {
      "name": "code-review-enforcer",
      "source": {
        "source": "github",
        "repo": "company/claude-plugins",
        "subdir": "code-review-enforcer"
      },
      "description": "Enforce code review standards before PRs",
      "category": "code-quality",
      "keywords": ["review", "quality", "standards"]
    },
    {
      "name": "deployment-helper",
      "source": {
        "source": "github",
        "repo": "company/claude-plugins",
        "subdir": "deployment-helper"
      },
      "description": "Deployment workflows for staging and production",
      "category": "deployment",
      "keywords": ["deploy", "production", "staging"]
    },
    {
      "name": "database-tools",
      "source": {
        "source": "github",
        "repo": "company/claude-plugins",
        "subdir": "database-tools",
        "ref": "v2.1.0"
      },
      "description": "Database query and schema management",
      "category": "database",
      "keywords": ["database", "sql", "postgres"]
    }
  ]
}
```

### Multi-Source Marketplace

```json
{
  "name": "multi-source",
  "owner": {
    "name": "Platform Team"
  },
  "plugins": [
    {
      "name": "local-plugin",
      "source": "./local-plugins/my-plugin",
      "description": "Local development plugin"
    },
    {
      "name": "github-plugin",
      "source": {
        "source": "github",
        "repo": "user/repo",
        "subdir": "plugin-dir"
      },
      "description": "Plugin from GitHub"
    },
    {
      "name": "gitlab-plugin",
      "source": {
        "source": "url",
        "url": "https://gitlab.com/org/plugins.git",
        "subdir": "plugin-name",
        "ref": "main"
      },
      "description": "Plugin from GitLab"
    }
  ]
}
```

## Repository Structure

### GitHub Marketplace (Recommended)

```
repository-root/
├── .claude-plugin/
│   └── marketplace.json      # Marketplace manifest
├── plugin-one/               # Plugin directories
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── commands/
│   ├── skills/
│   └── README.md
├── plugin-two/
│   ├── .claude-plugin/
│   │   └── plugin.json
│   └── ...
├── plugin-three/
│   └── ...
└── README.md                 # Marketplace documentation
```

### Monorepo with Nested Plugins

```
repository-root/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/                  # Plugin subdirectory
│   ├── database-tools/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── ...
│   ├── deployment-helper/
│   │   └── ...
│   └── testing-tools/
│       └── ...
└── README.md
```

marketplace.json with pluginRoot:
```json
{
  "name": "my-marketplace",
  "owner": {"name": "Team"},
  "metadata": {
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "database-tools",
      "source": "./database-tools"
    }
  ]
}
```

## Validation

### Common Errors

**Missing required fields:**
```
Error: marketplace.json missing required field "name"
Error: marketplace.json missing required field "owner"
Error: Plugin entry missing required field "name"
Error: Plugin entry missing required field "source"
```

**Invalid JSON syntax:**
```
Error: Invalid JSON in marketplace.json
```

**Invalid plugin source:**
```
Error: Plugin "my-plugin" source path "./invalid" does not exist
Error: Invalid GitHub repo format, expected "owner/repo"
```

### Validation Checklist

Before publishing:
- [ ] Valid JSON syntax
- [ ] Required fields present (name, owner, plugins)
- [ ] All plugin sources accessible
- [ ] Plugin names match plugin.json names
- [ ] Relative paths correct
- [ ] GitHub repos exist and accessible
- [ ] Git URLs valid and accessible
- [ ] Tested with `/plugin install`

## Path Resolution

### Relative Paths

Relative to marketplace.json location:
- `"./plugins/my-plugin"` → same repo
- `"../other-repo/plugin"` → parent directory (local only)

### pluginRoot

Base path for all relative sources:
```json
{
  "metadata": {
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./my-plugin"
    }
  ]
}
```

Resolves to: `./plugins/my-plugin`

### GitHub Paths

```json
{
  "source": {
    "source": "github",
    "repo": "owner/repo",
    "subdir": "path/to/plugin"
  }
}
```

Fetches from: `https://github.com/owner/repo` at path `path/to/plugin`

## Best Practices

### Naming

- Use kebab-case for marketplace names
- Make names descriptive: `engineering-tools` not `plugins`
- Match plugin names to plugin.json

### Organization

- Group related plugins in one marketplace
- Use categories and keywords for discovery
- Keep marketplace focused on specific audience

### Versioning

- Version the marketplace in metadata
- Pin plugin versions with git refs for stability
- Update marketplace version on changes

### Documentation

- Include README.md explaining marketplace
- Document plugin purposes
- Provide installation instructions
- List requirements and setup

### Testing

- Test locally before publishing
- Verify all plugins install correctly
- Check for conflicts between plugins
- Test with clean Claude Code environment

### Security

- Review plugin code before adding to marketplace
- Use git refs/tags to pin trusted versions
- Document security requirements
- Implement approval process for team marketplaces
