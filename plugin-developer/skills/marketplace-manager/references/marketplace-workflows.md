# Marketplace Management Workflows

## Creating a New Marketplace

### Step 1: Choose Distribution Method

**Local Development:**
- Fast iteration
- Testing before publishing
- No version control required
- Single developer workflows

**GitHub (Recommended):**
- Version control included
- Collaboration features
- Automatic updates for users
- Professional distribution

**GitLab/Self-Hosted:**
- Private hosting
- Enterprise requirements
- Custom security policies

### Step 2: Create Repository Structure

**For GitHub Marketplace:**

```bash
# Create repository
mkdir my-marketplace
cd my-marketplace
git init

# Create marketplace structure
mkdir -p .claude-plugin
mkdir -p plugins

# Create marketplace.json
cat > .claude-plugin/marketplace.json << 'EOF'
{
  "name": "my-marketplace",
  "owner": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "metadata": {
    "description": "Description of your marketplace",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": []
}
EOF

# Create README
cat > README.md << 'EOF'
# My Marketplace

Description of marketplace purpose and contents.

## Installation

\`\`\`bash
/plugin marketplace add username/my-marketplace
\`\`\`

## Available Plugins

- **plugin-name**: Description
EOF

git add .
git commit -m "Initial marketplace structure"
```

**For Local Development:**

```bash
# Create in project directory
cd /path/to/project
mkdir -p .claude-plugin

cat > .claude-plugin/marketplace.json << 'EOF'
{
  "name": "local-dev",
  "owner": {
    "name": "Developer"
  },
  "plugins": [
    {
      "name": "test-plugin",
      "source": "./test-plugin"
    }
  ]
}
EOF
```

### Step 3: Validate Structure

```bash
# Check JSON syntax
cat .claude-plugin/marketplace.json | jq .

# Verify required fields present
jq -r '.name, .owner.name, .plugins' .claude-plugin/marketplace.json
```

### Step 4: Test Installation

**Local:**
```bash
/plugin marketplace add ./path/to/marketplace
/plugin marketplace list
```

**GitHub (after pushing):**
```bash
/plugin marketplace add username/repository
/plugin marketplace list
```

## Adding Plugins to Marketplace

### Adding Local Plugin

**1. Create plugin in marketplace:**
```bash
# If using pluginRoot
cd plugins
mkdir my-plugin
cd my-plugin

# Create plugin structure
mkdir -p .claude-plugin commands skills
```

**2. Update marketplace.json:**
```json
{
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./my-plugin",
      "description": "Description of plugin",
      "version": "1.0.0",
      "category": "development-tools",
      "keywords": ["keyword1", "keyword2"]
    }
  ]
}
```

**3. Test installation:**
```bash
/plugin install my-plugin@my-marketplace
```

### Adding Plugin from GitHub

**1. Update marketplace.json:**
```json
{
  "plugins": [
    {
      "name": "external-plugin",
      "source": {
        "source": "github",
        "repo": "username/plugin-repo",
        "subdir": "plugin-directory",
        "ref": "v1.0.0"
      },
      "description": "Plugin from external repository"
    }
  ]
}
```

**2. Test:**
```bash
/plugin marketplace update my-marketplace
/plugin install external-plugin@my-marketplace
```

### Adding Plugin from Git URL

**1. Update marketplace.json:**
```json
{
  "plugins": [
    {
      "name": "gitlab-plugin",
      "source": {
        "source": "url",
        "url": "https://gitlab.com/org/plugins.git",
        "subdir": "plugin-name",
        "ref": "main"
      }
    }
  ]
}
```

## Updating Marketplace

### Adding New Plugin

```bash
# 1. Edit marketplace.json - add plugin to plugins array

# 2. Validate JSON
cat .claude-plugin/marketplace.json | jq .

# 3. Commit and push (GitHub)
git add .claude-plugin/marketplace.json
git commit -m "Add new-plugin to marketplace"
git push

# 4. Users update
# Users run: /plugin marketplace update marketplace-name
```

### Updating Plugin Version

**Update plugin version reference:**
```json
{
  "plugins": [
    {
      "name": "my-plugin",
      "source": {
        "source": "github",
        "repo": "org/repo",
        "ref": "v2.0.0"
      },
      "version": "2.0.0"
    }
  ]
}
```

**Update marketplace version:**
```json
{
  "metadata": {
    "version": "1.1.0"
  }
}
```

### Removing Plugin

```bash
# 1. Remove plugin entry from marketplace.json
jq 'del(.plugins[] | select(.name == "plugin-to-remove"))' \
  .claude-plugin/marketplace.json > tmp.json
mv tmp.json .claude-plugin/marketplace.json

# 2. Commit
git add .claude-plugin/marketplace.json
git commit -m "Remove deprecated plugin"
git push

# 3. Users update
# Users run: /plugin marketplace update marketplace-name
# Users run: /plugin uninstall plugin-to-remove (if installed)
```

## Managing Multiple Plugins

### Monorepo Structure

```
marketplace-repo/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   ├── plugin-a/
│   │   ├── .claude-plugin/plugin.json
│   │   └── commands/
│   ├── plugin-b/
│   │   └── ...
│   └── plugin-c/
│       └── ...
└── README.md
```

marketplace.json:
```json
{
  "name": "team-tools",
  "owner": {"name": "Team"},
  "metadata": {
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {"name": "plugin-a", "source": "./plugin-a"},
    {"name": "plugin-b", "source": "./plugin-b"},
    {"name": "plugin-c", "source": "./plugin-c"}
  ]
}
```

### Separate Repositories

```
marketplace-repo/
├── .claude-plugin/
│   └── marketplace.json
└── README.md
```

marketplace.json references external repos:
```json
{
  "plugins": [
    {
      "name": "plugin-a",
      "source": {
        "source": "github",
        "repo": "org/plugin-a"
      }
    },
    {
      "name": "plugin-b",
      "source": {
        "source": "github",
        "repo": "org/plugin-b"
      }
    }
  ]
}
```

### Hybrid Approach

Some plugins in repo, others external:
```json
{
  "metadata": {
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "internal-plugin",
      "source": "./internal-plugin"
    },
    {
      "name": "external-plugin",
      "source": {
        "source": "github",
        "repo": "community/external-plugin"
      }
    }
  ]
}
```

## Team Marketplace Setup

### Creating Team Marketplace

**1. Create GitHub repository:**
```bash
# On GitHub, create repository: company/claude-plugins
# Clone locally
git clone https://github.com/company/claude-plugins.git
cd claude-plugins
```

**2. Set up structure:**
```bash
mkdir -p .claude-plugin plugins

cat > .claude-plugin/marketplace.json << 'EOF'
{
  "name": "company-tools",
  "owner": {
    "name": "Engineering Team",
    "email": "engineering@company.com"
  },
  "metadata": {
    "description": "Company-wide development tools and workflows",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": []
}
EOF
```

**3. Add first plugin:**
```bash
mkdir -p plugins/code-standards
# Create plugin structure...
# Update marketplace.json
```

**4. Commit and push:**
```bash
git add .
git commit -m "Initialize company marketplace"
git push origin main
```

### Configuring Auto-Install for Team

**Option 1: Repository Settings (Recommended)**

Add to project `.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "company-tools": {
      "source": {
        "source": "github",
        "repo": "company/claude-plugins"
      }
    }
  }
}
```

When team members trust the repository, marketplace automatically installs.

**Option 2: Manual Installation**

Team members run:
```bash
/plugin marketplace add company/claude-plugins
```

### Rolling Out New Plugin to Team

**1. Add plugin to marketplace:**
```bash
# Update marketplace.json with new plugin
git add .claude-plugin/marketplace.json
git commit -m "Add deployment-helper plugin"
git push
```

**2. Team members update:**
```bash
# Automatic if using extraKnownMarketplaces
# Manual:
/plugin marketplace update company-tools
/plugin install deployment-helper@company-tools
```

**3. Announce to team:**
```
New plugin available: deployment-helper

Installation:
/plugin install deployment-helper@company-tools

Features:
- /deploy-staging command
- /deploy-prod command
- Automated pre-deployment checks
```

## Versioning Strategies

### Marketplace Versioning

**Semantic Versioning:**
```json
{
  "metadata": {
    "version": "1.2.3"
  }
}
```

- **MAJOR**: Breaking changes, removed plugins
- **MINOR**: New plugins added
- **PATCH**: Bug fixes, documentation updates

### Plugin Version Pinning

**Development (latest):**
```json
{
  "source": {
    "source": "github",
    "repo": "org/plugin"
  }
}
```
Uses default branch (main/master)

**Production (pinned):**
```json
{
  "source": {
    "source": "github",
    "repo": "org/plugin",
    "ref": "v2.1.0"
  }
}
```
Uses specific tag/release

**Staged Rollout:**
```json
{
  "plugins": [
    {
      "name": "stable-plugin",
      "source": {
        "repo": "org/plugin",
        "ref": "v1.0.0"
      }
    },
    {
      "name": "beta-plugin",
      "source": {
        "repo": "org/plugin",
        "ref": "v2.0.0-beta"
      }
    }
  ]
}
```

## Maintenance Workflows

### Regular Updates

**Monthly marketplace review:**
```bash
# 1. Check for plugin updates
# 2. Test new versions
# 3. Update refs in marketplace.json
# 4. Bump marketplace version
# 5. Commit and push
```

### Plugin Deprecation

**1. Mark as deprecated in marketplace:**
```json
{
  "plugins": [
    {
      "name": "old-plugin",
      "source": "./old-plugin",
      "description": "DEPRECATED: Use new-plugin instead",
      "tags": ["deprecated"]
    }
  ]
}
```

**2. Communicate to users:**
- Update README
- Send team announcement
- Provide migration guide

**3. Removal timeline:**
- Version N: Mark deprecated
- Version N+1: Remove from marketplace
- Provide 1-2 version cycles notice

### Handling Breaking Changes

**Plugin with breaking change:**

**1. Version appropriately:**
```json
{
  "plugins": [
    {
      "name": "my-plugin",
      "source": {
        "ref": "v2.0.0"
      },
      "version": "2.0.0",
      "description": "V2.0 - Breaking changes, see migration guide"
    }
  ]
}
```

**2. Provide migration documentation:**
```markdown
## Migration Guide: v1 → v2

### Breaking Changes
- Command renamed: `/old-cmd` → `/new-cmd`
- Environment variable changed: `OLD_VAR` → `NEW_VAR`

### Migration Steps
1. Update environment variables
2. Update command usage
3. Test functionality
```

**3. Bump marketplace major version:**
```json
{
  "metadata": {
    "version": "2.0.0"
  }
}
```

## Testing Strategies

### Local Testing

**1. Create test marketplace:**
```bash
mkdir test-marketplace
cd test-marketplace
mkdir -p .claude-plugin plugins
# Create marketplace.json
```

**2. Add to Claude:**
```bash
/plugin marketplace add ./test-marketplace
```

**3. Test installation:**
```bash
/plugin install test-plugin@test-marketplace
# Test plugin functionality
/plugin uninstall test-plugin
```

**4. Iterate:**
```bash
# Modify plugin
/plugin marketplace update test-marketplace
/plugin install test-plugin@test-marketplace
# Test again
```

### Pre-Release Testing

**1. Create test branch:**
```bash
git checkout -b test-new-plugin
# Add plugin to marketplace
git commit -m "Test: Add new plugin"
git push origin test-new-plugin
```

**2. Test from branch:**
```json
{
  "source": {
    "source": "github",
    "repo": "org/marketplace",
    "ref": "test-new-plugin"
  }
}
```

**3. Validate:**
- Test plugin installation
- Verify functionality
- Check for conflicts
- Review documentation

**4. Merge when ready:**
```bash
git checkout main
git merge test-new-plugin
git push origin main
```

## Troubleshooting

### Marketplace Won't Add

**Check:**
- Repository exists and is accessible
- marketplace.json exists at `.claude-plugin/marketplace.json`
- Valid JSON syntax
- Required fields present

**Commands:**
```bash
# Verify repository
curl https://github.com/user/repo

# Check marketplace.json
curl https://raw.githubusercontent.com/user/repo/main/.claude-plugin/marketplace.json | jq .
```

### Plugin Won't Install

**Check:**
- Plugin exists in marketplace.json
- Source path/URL is correct
- Plugin has valid plugin.json (if strict: true)
- No name conflicts

**Commands:**
```bash
# List marketplace plugins
/plugin marketplace update marketplace-name
/plugin

# Check plugin source
cat .claude-plugin/marketplace.json | jq '.plugins[] | select(.name=="plugin-name")'
```

### Updates Not Appearing

**Solution:**
```bash
# Force marketplace update
/plugin marketplace update marketplace-name

# Reinstall plugin
/plugin uninstall plugin-name
/plugin install plugin-name@marketplace-name
```

### Version Conflicts

**Problem**: Multiple versions of same plugin

**Solution:**
- Uninstall old version
- Clear cache
- Install specific version

```bash
/plugin uninstall conflicting-plugin
/plugin install conflicting-plugin@correct-marketplace
```
