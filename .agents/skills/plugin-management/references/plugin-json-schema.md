# plugin.json Schema Reference

## File Location

Required location: `.claude-plugin/plugin.json`

## Complete Schema

```json
{
  "name": "string (required)",
  "version": "string (optional, semantic versioning)",
  "description": "string (optional but recommended)",
  "author": {
    "name": "string",
    "email": "string",
    "url": "string"
  },
  "homepage": "string (documentation URL)",
  "repository": "string (source code location)",
  "license": "string (MIT, Apache-2.0, etc.)",
  "keywords": ["array", "of", "tags"],
  "category": "string",
  "commands": "string or array (paths to command files/dirs)",
  "agents": "string or array (paths to agent files)",
  "hooks": "string (path to hooks.json) or object (inline)",
  "mcpServers": {
    "server-name": {
      "command": "string",
      "args": ["array", "of", "arguments"],
      "env": {
        "KEY": "value"
      }
    }
  },
  "strict": "boolean (validation mode)"
}
```

## Required Fields

### name
- **Type**: String
- **Required**: Yes
- **Description**: Unique identifier for the plugin
- **Format**: Lowercase with hyphens (e.g., `my-plugin`)
- **Constraints**: Must match plugin directory name

```json
{
  "name": "code-review-enforcer"
}
```

## Recommended Fields

### version
- **Type**: String
- **Required**: No (but strongly recommended)
- **Format**: Semantic versioning (MAJOR.MINOR.PATCH)
- **Examples**: "1.0.0", "2.3.1", "0.1.0-beta"

```json
{
  "version": "1.2.0"
}
```

### description
- **Type**: String
- **Required**: No (but strongly recommended)
- **Purpose**: Brief explanation of plugin functionality
- **Best Practice**: Clear, concise description that helps users understand when to use the plugin

```json
{
  "description": "Enforces code review standards and runs mandatory tests before PRs"
}
```

### author
- **Type**: Object with name, email, and URL fields
- **Required**: No
- **Fields**: All optional within the object

```json
{
  "author": {
    "name": "Development Team",
    "email": "dev@company.com",
    "url": "https://company.com"
  }
}
```

Minimal author format:
```json
{
  "author": {
    "name": "Your Name"
  }
}
```

## Optional Metadata Fields

### homepage
- **Type**: String (URL)
- **Purpose**: Link to plugin documentation

```json
{
  "homepage": "https://docs.company.com/plugins/code-review"
}
```

### repository
- **Type**: String (URL)
- **Purpose**: Link to source code repository

```json
{
  "repository": "https://github.com/company/code-review-plugin"
}
```

### license
- **Type**: String
- **Common Values**: "MIT", "Apache-2.0", "BSD-3-Clause", "GPL-3.0"

```json
{
  "license": "MIT"
}
```

### keywords
- **Type**: Array of strings
- **Purpose**: Discovery tags for marketplace search

```json
{
  "keywords": ["code-review", "testing", "quality", "standards"]
}
```

### category
- **Type**: String
- **Purpose**: Plugin categorization in marketplaces

```json
{
  "category": "development-workflow"
}
```

## Component Configuration Fields

### commands
- **Type**: String or Array of strings
- **Purpose**: Specify custom command file locations
- **Default**: Automatically discovers `commands/` directory
- **Supplementary**: Custom paths add to (not replace) default

Single path:
```json
{
  "commands": "./custom-commands"
}
```

Multiple paths:
```json
{
  "commands": ["./commands", "./team-commands", "./legacy-commands"]
}
```

### agents
- **Type**: String or Array of strings
- **Purpose**: Specify custom agent file locations
- **Default**: Automatically discovers `agents/` directory

```json
{
  "agents": ["./agents", "./specialized-agents"]
}
```

### hooks
- **Type**: String (path) or Object (inline configuration)
- **Purpose**: Event handler configuration

Path format (references external file):
```json
{
  "hooks": "./hooks/hooks.json"
}
```

Inline format:
```json
{
  "hooks": {
    "PreToolUse": {
      "action": "validate",
      "script": "./scripts/validate.sh"
    }
  }
}
```

### mcpServers
- **Type**: Object with server configurations
- **Purpose**: Define Model Context Protocol server connections
- **Environment Variable**: Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths

```json
{
  "mcpServers": {
    "internal-api": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/servers/api-server.js"],
      "env": {
        "API_URL": "https://internal.company.com/api",
        "API_KEY": "${COMPANY_API_KEY}"
      }
    },
    "database": {
      "command": "python",
      "args": ["-m", "mcp_server_postgres", "${DATABASE_URL}"],
      "env": {
        "DATABASE_URL": "${DB_CONNECTION_STRING}"
      }
    }
  }
}
```

## Advanced Fields

### strict
- **Type**: Boolean
- **Purpose**: Enable strict validation mode
- **Default**: false

```json
{
  "strict": true
}
```

## Complete Example

Minimal plugin.json:
```json
{
  "name": "my-plugin",
  "description": "A simple plugin for demonstration",
  "version": "1.0.0",
  "author": {
    "name": "Plugin Developer"
  }
}
```

Comprehensive plugin.json:
```json
{
  "name": "team-workflow-enforcer",
  "version": "2.1.0",
  "description": "Enforces team coding standards, runs mandatory tests, and provides debugging workflows",
  "author": {
    "name": "Engineering Team",
    "email": "engineering@company.com",
    "url": "https://company.com/engineering"
  },
  "homepage": "https://docs.company.com/plugins/workflow-enforcer",
  "repository": "https://github.com/company/workflow-enforcer-plugin",
  "license": "MIT",
  "keywords": ["workflow", "testing", "code-review", "standards", "debugging"],
  "category": "development-tools",
  "commands": ["./commands", "./debugging-commands"],
  "agents": "./agents",
  "hooks": {
    "PreToolUse": {
      "action": "validate",
      "tools": ["Bash", "Write", "Edit"],
      "script": "./hooks/validate-tool-use.sh"
    },
    "UserPromptSubmit": {
      "action": "enhance",
      "script": "./hooks/add-context.sh"
    }
  },
  "mcpServers": {
    "jira": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/servers/jira-server.js"],
      "env": {
        "JIRA_URL": "${JIRA_URL}",
        "JIRA_TOKEN": "${JIRA_API_TOKEN}"
      }
    },
    "internal-docs": {
      "command": "python",
      "args": ["-m", "company_docs_server"],
      "env": {
        "DOCS_URL": "https://docs.company.internal"
      }
    }
  }
}
```

## Path Rules

1. **Relative Paths Only**: All paths must be relative to plugin root
2. **Format**: Start with `./` for clarity
3. **Plugin Root Variable**: Use `${CLAUDE_PLUGIN_ROOT}` in MCP server configs for portability
4. **Array Support**: Most path fields accept string or array of strings

## Validation

Use the plugin validator to check plugin.json format:
```bash
claude validate plugin ./path/to/plugin
```

Common validation errors:
- Missing required `name` field
- Invalid semantic versioning format
- Incorrect path formats (must be relative)
- Invalid JSON syntax
- Referenced files don't exist
