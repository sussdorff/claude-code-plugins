---
name: marketplace-manager
description: This skill should be used when creating, managing, or configuring Claude Code plugin marketplaces. Use when the user wants to set up a marketplace, add plugins to a marketplace, configure team distribution, manage marketplace versions, or understand marketplace.json structure and CLI commands. Applicable for local development marketplaces, team marketplaces, and public marketplace distribution.
---

# Marketplace Manager

## Overview

This skill provides comprehensive guidance for creating and managing Claude Code plugin marketplaces. Marketplaces are JSON-based catalogs that enable centralized discovery, version management, and distribution of plugins across teams and organizations.

## When to Use This Skill

Use this skill when:
- Creating a new plugin marketplace (local, team, or public)
- Adding or removing plugins from a marketplace
- Configuring marketplace.json structure and fields
- Setting up team-wide plugin distribution
- Managing marketplace versions and updates
- Troubleshooting marketplace installation or plugin issues
- Implementing marketplace governance for teams
- Migrating from individual plugins to marketplace distribution

## Marketplace Management Workflow

Follow this workflow for creating and managing effective marketplaces.

### Step 1: Choose Marketplace Type

Determine the appropriate marketplace type based on your distribution needs.

**Local Development Marketplace:**
- **Purpose**: Testing plugins during development
- **Location**: Project directory
- **Access**: Single developer
- **Workflow**: Rapid iteration
- **Example**: `./project/.claude-plugin/marketplace.json`

**Team Marketplace:**
- **Purpose**: Standardize tools across team
- **Location**: GitHub/GitLab repository
- **Access**: Team members
- **Workflow**: Reviewed updates
- **Example**: `company/claude-plugins` repository

**Public Marketplace:**
- **Purpose**: Community distribution
- **Location**: Public GitHub repository
- **Access**: Anyone
- **Workflow**: Open contribution
- **Example**: `community/claude-plugins-collection`

**Decision Factors:**
- Audience size: Personal → Team → Public
- Update frequency: High → Medium → Low
- Quality requirements: Flexible → Standard → Strict
- Security review: None → Team → Community

**Reference**: See `references/team-collaboration.md` for detailed comparison of team marketplace strategies including centralized, distributed, and multi-marketplace approaches.

**Output**: Clear decision on marketplace type and hosting approach.

### Step 2: Create Marketplace Structure

Set up the repository and directory structure.

**For GitHub/GitLab Marketplace (Recommended):**

```bash
# Create repository
mkdir my-marketplace
cd my-marketplace
git init

# Create directory structure
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
    "description": "Description of marketplace purpose",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": []
}
EOF

# Create README
cat > README.md << 'EOF'
# My Marketplace

Brief description of marketplace.

## Installation

\`\`\`bash
/plugin marketplace add username/my-marketplace
\`\`\`

## Available Plugins

List of plugins with descriptions.
EOF

# Commit
git add .
git commit -m "Initialize marketplace structure"
```

**For Local Development:**

```bash
# In your project directory
mkdir -p .claude-plugin

# Copy template
cp assets/marketplace-templates/local-dev-marketplace.json .claude-plugin/marketplace.json

# Edit with your details
# Update name, owner, and plugin entries
```

**Templates Available:**
- `assets/marketplace-templates/local-dev-marketplace.json` - Local development
- `assets/marketplace-templates/team-marketplace.json` - Team distribution
- `assets/marketplace-templates/github-marketplace.json` - GitHub-based marketplace

**Critical Structure Rules:**
- marketplace.json must be at `.claude-plugin/marketplace.json`
- All paths relative to repository root
- Valid JSON syntax required
- Required fields: name, owner, plugins

**Output**: Complete marketplace repository structure ready for plugins.

### Step 3: Configure marketplace.json

Create the marketplace manifest with appropriate metadata.

**Required Fields:**
```json
{
  "name": "marketplace-identifier",
  "owner": {
    "name": "Maintainer Name",
    "email": "contact@example.com"
  },
  "plugins": []
}
```

**Recommended Metadata:**
```json
{
  "metadata": {
    "description": "Clear description of marketplace purpose",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  }
}
```

**Field Explanations:**
- **name**: Kebab-case identifier (e.g., `team-tools`, `my-marketplace`)
- **owner**: Contact information for marketplace maintainer
- **metadata.description**: Brief overview shown to users
- **metadata.version**: Marketplace version (semantic versioning)
- **metadata.pluginRoot**: Base path for relative plugin sources

**Validation:**
```bash
# Check JSON syntax
cat .claude-plugin/marketplace.json | jq .

# Verify required fields
jq -r '.name, .owner.name, .plugins' .claude-plugin/marketplace.json
```

**Reference**: See `references/marketplace-json-schema.md` for:
- Complete schema with all fields
- Field descriptions and examples
- Plugin entry configuration
- Source type formats (relative, GitHub, Git URL)
- Validation requirements
- Multiple real-world examples

**Output**: Valid marketplace.json with proper metadata configuration.

### Step 4: Add Plugins to Marketplace

Configure plugin entries in the marketplace.

**Adding Local Plugin:**

1. **Create plugin in marketplace:**
```bash
# If using pluginRoot
cd plugins
mkdir my-plugin
cd my-plugin

# Create plugin structure
mkdir -p .claude-plugin commands skills
# ... create plugin components
```

2. **Add to marketplace.json:**
```json
{
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./my-plugin",
      "description": "Plugin description for marketplace listing",
      "version": "1.0.0",
      "category": "development-tools",
      "keywords": ["keyword1", "keyword2"]
    }
  ]
}
```

**Adding GitHub Plugin:**

```json
{
  "plugins": [
    {
      "name": "external-plugin",
      "source": {
        "source": "github",
        "repo": "username/repository",
        "subdir": "plugin-directory",
        "ref": "v1.0.0"
      },
      "description": "Plugin from external repository"
    }
  ]
}
```

**Adding Git URL Plugin:**

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

**Plugin Entry Best Practices:**
- Match `name` to plugin's plugin.json name
- Provide clear, concise descriptions
- Use semantic versioning
- Include relevant keywords
- Categorize appropriately
- Pin versions with `ref` for stability

**Validation:**
```bash
# Test plugin installation
/plugin marketplace add ./path/to/marketplace  # or github-url
/plugin install plugin-name@marketplace-name

# Verify functionality
# Test plugin commands/skills
```

**Reference**: See `references/marketplace-workflows.md` for:
- Detailed workflows for adding/removing plugins
- Managing multiple plugins
- Monorepo vs separate repository strategies
- Version pinning strategies
- Testing procedures

**Output**: Marketplace with functional plugin entries ready for distribution.

### Step 5: Test Marketplace Locally

Validate marketplace works correctly before publishing.

**Add Marketplace:**

**Local:**
```bash
/plugin marketplace add ./path/to/marketplace
```

**GitHub (after pushing):**
```bash
/plugin marketplace add username/repository
```

**Git URL:**
```bash
/plugin marketplace add https://gitlab.com/org/marketplace.git
```

**Verify Installation:**
```bash
# List marketplaces
/plugin marketplace list

# Should show your marketplace

# Browse plugins
/plugin

# Should show plugins from your marketplace
```

**Test Plugin Installation:**
```bash
# Install plugin from marketplace
/plugin install plugin-name@marketplace-name

# Test plugin functionality
/command-name  # If plugin has commands
# Or use skill naturally

# Uninstall and test again
/plugin uninstall plugin-name
/plugin install plugin-name@marketplace-name
```

**Iteration Loop:**
```bash
# Make changes to marketplace.json
# Update marketplace
/plugin marketplace update marketplace-name

# Test changes
/plugin install updated-plugin@marketplace-name
```

**Validation Checklist:**
- [ ] Marketplace installs without errors
- [ ] All plugins visible in `/plugin` browser
- [ ] Plugins install successfully
- [ ] Plugin functionality works as expected
- [ ] No conflicts between plugins
- [ ] Descriptions are clear and accurate
- [ ] Versions are correct

**Output**: Thoroughly tested marketplace ready for team or public use.

### Step 6: Publish and Distribute

Make marketplace available to users.

**For GitHub Marketplace:**

1. **Push to GitHub:**
```bash
git add .
git commit -m "Initial marketplace release"
git push origin main
```

2. **Create Release (Optional):**
```bash
git tag -a v1.0.0 -m "Version 1.0.0"
git push origin v1.0.0
```

3. **Document Installation:**

Update README.md:
```markdown
## Installation

Add marketplace:
\`\`\`bash
/plugin marketplace add username/repository-name
\`\`\`

Install plugins:
\`\`\`bash
/plugin install plugin-name@marketplace-name
\`\`\`

## Available Plugins

### plugin-name
Description of plugin

**Installation:**
\`\`\`bash
/plugin install plugin-name@marketplace-name
\`\`\`

**Features:**
- Feature 1
- Feature 2
```

**For Team Distribution:**

**Option 1: Auto-Install (Recommended)**

Add to project `.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "team-tools": {
      "source": {
        "source": "github",
        "repo": "company/claude-plugins"
      }
    }
  }
}
```

When team members trust repository, marketplace auto-installs.

**Option 2: Manual Installation**

Document in team wiki/README:
```markdown
## Setup Claude Plugins

1. Add marketplace:
   \`\`\`bash
   /plugin marketplace add company/claude-plugins
   \`\`\`

2. Install essential plugins:
   \`\`\`bash
   /plugin install code-standards@team-tools
   /plugin install deployment@team-tools
   \`\`\`
```

**Announcement Template:**
```markdown
## 🚀 New Plugin Marketplace Available

We've created a centralized marketplace for team tools.

**Setup:**
1. Add marketplace: `/plugin marketplace add company/claude-plugins`
2. Browse plugins: `/plugin`
3. Install as needed

**Available Plugins:**
- code-standards: Enforce coding standards
- deployment: Deployment workflows
- testing: Testing utilities

**Documentation:** See repository README

**Questions:** #engineering-tools channel
```

**Reference**: See `references/team-collaboration.md` for:
- Team marketplace strategies
- Governance models
- Onboarding workflows
- Communication templates
- Security and compliance considerations

**Output**: Published marketplace accessible to target audience.

### Step 7: Maintain and Update

Ongoing marketplace management and updates.

**Adding New Plugin:**

1. **Add plugin to marketplace:**
```bash
# Edit marketplace.json - add to plugins array
# Validate JSON
cat .claude-plugin/marketplace.json | jq .

# Commit and push
git add .claude-plugin/marketplace.json
git commit -m "Add new-plugin to marketplace"
git push
```

2. **Bump marketplace version:**
```json
{
  "metadata": {
    "version": "1.1.0"
  }
}
```

3. **Announce to users:**
```markdown
## New Plugin Available: new-plugin

Description of plugin.

**Installation:**
\`\`\`bash
/plugin marketplace update marketplace-name
/plugin install new-plugin@marketplace-name
\`\`\`
```

**Updating Plugin Version:**

```json
{
  "plugins": [
    {
      "name": "my-plugin",
      "source": {
        "ref": "v2.0.0"
      },
      "version": "2.0.0"
    }
  ]
}
```

**Removing Plugin:**

```bash
# Remove from marketplace.json
jq 'del(.plugins[] | select(.name == "old-plugin"))' \
  .claude-plugin/marketplace.json > tmp.json
mv tmp.json .claude-plugin/marketplace.json

# Commit
git add .claude-plugin/marketplace.json
git commit -m "Remove deprecated plugin"
git push
```

**Version Management:**
- **MAJOR**: Breaking changes, removed plugins
- **MINOR**: New plugins added
- **PATCH**: Bug fixes, documentation updates

**Regular Maintenance:**
- Review plugin updates monthly
- Test new versions before updating refs
- Monitor for security vulnerabilities
- Update documentation
- Respond to user issues

**Reference**: See `references/marketplace-workflows.md` section on "Maintenance Workflows" for:
- Plugin deprecation process
- Breaking change handling
- Testing strategies
- Troubleshooting common issues

**Output**: Well-maintained marketplace with current, stable plugins.

## CLI Command Reference

### Marketplace Management

**Add marketplace:**
```bash
/plugin marketplace add owner/repo                  # GitHub
/plugin marketplace add https://url.git             # Git URL
/plugin marketplace add ./local-path                # Local directory
```

**List marketplaces:**
```bash
/plugin marketplace list
```

**Update marketplace:**
```bash
/plugin marketplace update marketplace-name
```

**Remove marketplace:**
```bash
/plugin marketplace remove marketplace-name
```

### Plugin Operations

**Browse plugins:**
```bash
/plugin                                            # Interactive browser
```

**Install plugin:**
```bash
/plugin install plugin-name@marketplace-name
```

**Update plugin:**
```bash
/plugin marketplace update marketplace-name        # Update marketplace
/plugin install plugin-name@marketplace-name      # Reinstall plugin
```

**Uninstall plugin:**
```bash
/plugin uninstall plugin-name
```

## Marketplace Patterns

### Pattern 1: Local Development Marketplace

**Use Case**: Testing plugins during development

**Structure:**
```
project/
├── .claude-plugin/
│   └── marketplace.json
└── test-plugin/
    └── ...
```

**marketplace.json:**
```json
{
  "name": "local-dev",
  "owner": {"name": "Developer"},
  "plugins": [
    {"name": "test-plugin", "source": "./test-plugin"}
  ]
}
```

**Workflow:**
```bash
# Add marketplace
/plugin marketplace add ./project

# Test plugin
/plugin install test-plugin@local-dev

# Make changes
# Update and reinstall
/plugin marketplace update local-dev
/plugin uninstall test-plugin
/plugin install test-plugin@local-dev
```

### Pattern 2: Team Monorepo

**Use Case**: All team plugins in one repository

**Structure:**
```
company-plugins/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   ├── plugin-a/
│   ├── plugin-b/
│   └── plugin-c/
└── README.md
```

**marketplace.json:**
```json
{
  "name": "company-tools",
  "owner": {"name": "Engineering"},
  "metadata": {"pluginRoot": "./plugins"},
  "plugins": [
    {"name": "plugin-a", "source": "./plugin-a"},
    {"name": "plugin-b", "source": "./plugin-b"},
    {"name": "plugin-c", "source": "./plugin-c"}
  ]
}
```

**Benefits:**
- Single repository to maintain
- Easy cross-plugin changes
- Unified CI/CD
- Simple version management

### Pattern 3: Multi-Source Marketplace

**Use Case**: Curating plugins from multiple sources

**Structure:**
```
marketplace-repo/
├── .claude-plugin/
│   └── marketplace.json
├── internal-plugins/
│   └── plugin-a/
└── README.md
```

**marketplace.json:**
```json
{
  "name": "curated-tools",
  "owner": {"name": "Team"},
  "plugins": [
    {
      "name": "internal-plugin",
      "source": "./internal-plugins/plugin-a"
    },
    {
      "name": "community-plugin",
      "source": {
        "source": "github",
        "repo": "community/plugin"
      }
    },
    {
      "name": "gitlab-plugin",
      "source": {
        "source": "url",
        "url": "https://gitlab.com/org/plugin.git"
      }
    }
  ]
}
```

**Benefits:**
- Mix internal and external plugins
- Curate best community plugins
- Flexible plugin sources

### Pattern 4: Multi-Marketplace Strategy

**Use Case**: Different tool sets for different teams

**Marketplaces:**
- `frontend-tools`: Frontend-specific plugins
- `backend-tools`: Backend-specific plugins
- `devops-tools`: Infrastructure and deployment

**Configuration in .claude/settings.json:**
```json
{
  "extraKnownMarketplaces": {
    "frontend-tools": {
      "source": {"source": "github", "repo": "company/frontend-plugins"}
    },
    "backend-tools": {
      "source": {"source": "github", "repo": "company/backend-plugins"}
    }
  }
}
```

**Benefits:**
- Focused tool sets per team
- Team autonomy
- Reduced complexity
- Clear ownership

## Quick Reference

### marketplace.json Required Fields

```json
{
  "name": "marketplace-name",
  "owner": {
    "name": "Maintainer Name"
  },
  "plugins": []
}
```

### Plugin Entry Formats

**Local:**
```json
{"name": "plugin", "source": "./path/to/plugin"}
```

**GitHub:**
```json
{
  "name": "plugin",
  "source": {
    "source": "github",
    "repo": "owner/repo",
    "subdir": "plugin-dir",
    "ref": "v1.0.0"
  }
}
```

**Git URL:**
```json
{
  "name": "plugin",
  "source": {
    "source": "url",
    "url": "https://git.example.com/repo.git",
    "subdir": "plugin-dir"
  }
}
```

## Troubleshooting

### Marketplace Won't Add

**Check:**
- Repository exists and accessible
- marketplace.json at `.claude-plugin/marketplace.json`
- Valid JSON syntax
- Required fields present

**Solution:**
```bash
# Verify repository
curl https://github.com/user/repo

# Check marketplace.json
curl https://raw.githubusercontent.com/user/repo/main/.claude-plugin/marketplace.json | jq .
```

### Plugin Won't Install

**Check:**
- Plugin exists in marketplace.json
- Source path/URL correct
- Plugin has valid plugin.json (if strict: true)
- No name conflicts

**Solution:**
```bash
# List plugins
/plugin marketplace update marketplace-name
/plugin

# Verify plugin entry
cat .claude-plugin/marketplace.json | jq '.plugins[] | select(.name=="plugin-name")'
```

### Updates Not Appearing

**Solution:**
```bash
# Force update
/plugin marketplace update marketplace-name

# Reinstall
/plugin uninstall plugin-name
/plugin install plugin-name@marketplace-name
```

## Resources

**Comprehensive References:**
- `references/marketplace-json-schema.md` - Complete schema with all fields and examples
- `references/marketplace-workflows.md` - Detailed workflows for creating, managing, and maintaining marketplaces
- `references/team-collaboration.md` - Team strategies, governance, onboarding, and scaling

**Templates:**
- `assets/marketplace-templates/local-dev-marketplace.json` - Local development template
- `assets/marketplace-templates/team-marketplace.json` - Team distribution template
- `assets/marketplace-templates/github-marketplace.json` - GitHub-based template

## Summary

Create and manage effective Claude Code plugin marketplaces by:
1. **Choosing**: Determine marketplace type (local, team, public)
2. **Creating**: Set up repository structure with marketplace.json
3. **Configuring**: Define metadata and plugin entries
4. **Adding Plugins**: Configure local, GitHub, or Git URL sources
5. **Testing**: Validate locally before publishing
6. **Publishing**: Distribute via GitHub/GitLab with documentation
7. **Maintaining**: Update plugins, bump versions, respond to issues

Leverage bundled references for detailed schema information, workflow guidance, and team collaboration strategies throughout the marketplace lifecycle.
