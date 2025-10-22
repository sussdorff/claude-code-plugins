# Team Collaboration with Marketplaces

## Team Marketplace Strategies

### Centralized Team Marketplace

**Use Case**: Single source of truth for all team tools

**Structure:**
```
company-plugins/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   ├── code-standards/
│   ├── deployment/
│   ├── testing/
│   └── documentation/
├── docs/
│   ├── plugin-guide.md
│   └── contribution-guide.md
└── README.md
```

**Benefits:**
- Single installation for team members
- Consistent tooling across projects
- Centralized maintenance
- Easy discovery

**Setup:**
```json
{
  "name": "company-engineering",
  "owner": {
    "name": "Engineering Team",
    "email": "engineering@company.com"
  },
  "metadata": {
    "description": "Standard engineering tools and workflows",
    "version": "2.1.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [...]
}
```

### Multi-Marketplace Strategy

**Use Case**: Different tools for different teams/purposes

**Organization:**
- `frontend-tools`: Frontend-specific plugins
- `backend-tools`: Backend-specific plugins
- `devops-tools`: Infrastructure and deployment
- `qa-tools`: Testing and quality assurance

**Benefits:**
- Focused tool sets
- Reduced complexity per marketplace
- Team autonomy
- Clearer ownership

**Configuration in .claude/settings.json:**
```json
{
  "extraKnownMarketplaces": {
    "frontend-tools": {
      "source": {
        "source": "github",
        "repo": "company/frontend-plugins"
      }
    },
    "backend-tools": {
      "source": {
        "source": "github",
        "repo": "company/backend-plugins"
      }
    }
  }
}
```

### Project-Specific Marketplaces

**Use Case**: Tools specific to particular projects

**Structure:**
```
project-repo/
├── .claude/
│   └── settings.json
└── .claude-plugin/
    └── marketplace.json
```

**Benefits:**
- Project-specific customizations
- No team-wide impact
- Faster iteration
- Experimental tools

**Auto-install via settings.json:**
```json
{
  "extraKnownMarketplaces": {
    "project-tools": {
      "source": {
        "source": "github",
        "repo": "company/project-specific-plugins"
      }
    }
  }
}
```

## Governance Models

### Centralized Control

**Approach**: Core team maintains marketplace

**Responsibilities:**
- Review all plugin submissions
- Ensure quality standards
- Security review
- Documentation standards
- Version management

**Process:**
```
1. Plugin developer submits PR
2. Core team reviews
   - Code review
   - Security scan
   - Documentation check
   - Testing validation
3. Approved plugins merged
4. Marketplace version bumped
5. Team notified
```

**Example PR Template:**
```markdown
## New Plugin Submission

**Plugin Name**: my-plugin
**Purpose**: Brief description
**Category**: development-tools

**Checklist:**
- [ ] plugin.json complete with version and description
- [ ] README.md included
- [ ] All commands documented
- [ ] Skills have clear descriptions
- [ ] No hardcoded secrets
- [ ] Tested locally
- [ ] No conflicts with existing plugins

**Testing:**
Describe how you tested the plugin.

**Dependencies:**
List any required environment variables or external tools.
```

### Distributed Ownership

**Approach**: Teams maintain their own sections

**Structure:**
```
company-plugins/
├── frontend/          # Frontend team owns
├── backend/           # Backend team owns
├── devops/            # DevOps team owns
└── .claude-plugin/
    └── marketplace.json
```

**Benefits:**
- Team autonomy
- Faster updates
- Domain expertise
- Shared responsibility

**CODEOWNERS file:**
```
# Frontend plugins
/plugins/frontend/ @company/frontend-team

# Backend plugins
/plugins/backend/ @company/backend-team

# DevOps plugins
/plugins/devops/ @company/devops-team

# Marketplace configuration
/.claude-plugin/ @company/platform-team
```

### Open Contribution Model

**Approach**: Anyone can contribute with review

**Process:**
```
1. Fork repository
2. Add/update plugin
3. Submit PR
4. Automated checks run
5. Community review
6. Merge when approved
```

**Automated Checks (.github/workflows/validate.yml):**
```yaml
name: Validate Plugins
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate marketplace.json
        run: jq . .claude-plugin/marketplace.json
      - name: Validate plugin.json files
        run: |
          for plugin in plugins/*/; do
            jq . "$plugin/.claude-plugin/plugin.json"
          done
      - name: Check for secrets
        run: |
          # Run secret scanning
          # Fail if secrets detected
```

## Onboarding New Team Members

### Automatic Setup

**1. Repository Configuration:**

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

**2. Documentation in README:**
```markdown
## Claude Code Setup

1. Trust this repository in Claude Code
2. Marketplace will automatically install
3. Install recommended plugins:
   ```bash
   /plugin install code-standards@company-tools
   /plugin install testing-tools@company-tools
   ```
```

**3. Onboarding Checklist:**
```markdown
## Claude Code Onboarding

- [ ] Install Claude Code
- [ ] Clone repository
- [ ] Trust repository in Claude Code
- [ ] Verify marketplace: `/plugin marketplace list`
- [ ] Install core plugins: `/plugin install code-standards@company-tools`
- [ ] Test functionality: `/check-code-style`
- [ ] Read plugin documentation in README
```

### Manual Setup

**Setup Script (setup-claude.sh):**
```bash
#!/bin/bash
set -euo pipefail

echo "Setting up Claude Code plugins..."

# Add marketplace
echo "Adding company marketplace..."
/plugin marketplace add company/claude-plugins

# Install essential plugins
echo "Installing essential plugins..."
/plugin install code-standards@company-tools
/plugin install deployment@company-tools
/plugin install testing@company-tools

echo "✅ Claude Code setup complete!"
echo ""
echo "Available commands:"
echo "  /check-code-style  - Check code against standards"
echo "  /deploy-staging    - Deploy to staging"
echo "  /run-tests         - Run test suite"
```

## Communication Strategies

### Plugin Updates

**Announcement Template:**
```markdown
## 🚀 New Plugin Available: deployment-helper v1.0

The deployment-helper plugin streamlines our deployment workflow.

**Features:**
- `/deploy-staging` - Deploy to staging environment
- `/deploy-prod` - Deploy to production with checks
- Automated pre-deployment validation

**Installation:**
```bash
/plugin marketplace update company-tools
/plugin install deployment-helper@company-tools
```

**Documentation:** See plugins/deployment-helper/README.md

**Questions?** #engineering-tools channel
```

### Breaking Changes

**Announcement Template:**
```markdown
## ⚠️ Breaking Change: code-standards v2.0

Version 2.0 includes breaking changes to command syntax.

**Changes:**
- Command renamed: `/check-style` → `/check-code-style`
- New required env var: `CODE_STANDARD_VERSION`

**Migration:**
1. Update environment: `export CODE_STANDARD_VERSION=2`
2. Update scripts/workflows to use new command names
3. Update to v2.0: `/plugin install code-standards@company-tools`

**Timeline:**
- Today: v2.0 available
- Next week: v1.x deprecated
- 2 weeks: v1.x removed from marketplace

**Support:** #engineering-tools for help
```

### Regular Updates

**Weekly Plugin Digest:**
```markdown
## Plugin Updates - Week of Dec 18

**New Plugins:**
- `api-tester` - API testing utilities

**Updated Plugins:**
- `deployment` v1.2.0 - Added rollback command
- `testing` v2.1.0 - Better error messages

**Coming Soon:**
- `monitoring` - Integration with monitoring tools
- `docs-generator` - Automated documentation

**Stats:**
- 15 active plugins
- 42 team members using marketplace
- 156 plugin installations this week

Update: `/plugin marketplace update company-tools`
```

## Security and Compliance

### Security Review Process

**Plugin Security Checklist:**
- [ ] No hardcoded secrets or credentials
- [ ] Environment variables for sensitive data
- [ ] Input validation for hooks
- [ ] No arbitrary code execution
- [ ] Dependencies reviewed
- [ ] Audit log for sensitive operations
- [ ] Proper error handling (no info leaks)

**Review Process:**
```
1. Code review by security team
2. Automated security scan
3. Dependency vulnerability check
4. Test with malicious inputs
5. Approve or request changes
6. Merge and tag version
```

### Compliance Requirements

**Internal Tools Only:**
```json
{
  "metadata": {
    "description": "Internal tools - Company Confidential",
    "tags": ["internal", "confidential"]
  }
}
```

**License Compliance:**
```json
{
  "plugins": [
    {
      "name": "my-plugin",
      "license": "MIT",
      "repository": "https://github.com/company/plugin"
    }
  ]
}
```

**Audit Trail:**
- Git history for all changes
- PR reviews documented
- Security approval recorded
- Version tags with release notes

## Scaling Strategies

### Large Team (100+ developers)

**Strategy:**
- Multiple specialized marketplaces
- Automated testing pipeline
- Dedicated marketplace maintainers
- Self-service plugin submission
- Comprehensive documentation

**Organization:**
```
company-plugins/
├── core/              # Essential tools (all teams)
├── frontend/          # Frontend team
├── backend/           # Backend team
├── mobile/            # Mobile team
├── data/              # Data team
└── experimental/      # Beta/testing
```

### Multi-Region Teams

**Considerations:**
- GitHub/GitLab for global access
- Mirror repositories if needed
- Clear timezone documentation
- Async communication for updates

**Regional Mirrors (if needed):**
```json
{
  "metadata": {
    "mirrors": [
      "https://github.com/company/plugins",
      "https://gitlab.internal/company/plugins"
    ]
  }
}
```

### Enterprise Deployment

**Requirements:**
- Internal hosting option
- Security scanning integration
- Compliance tracking
- Access control
- Audit logging

**Self-Hosted GitLab:**
```json
{
  "plugins": [
    {
      "name": "internal-plugin",
      "source": {
        "source": "url",
        "url": "https://gitlab.internal/team/plugins.git",
        "subdir": "plugin-name"
      }
    }
  ]
}
```

## Metrics and Analytics

### Marketplace Health Metrics

**Track:**
- Number of plugins
- Installation counts
- Update frequency
- Issue resolution time
- User satisfaction

**Example Dashboard:**
```markdown
## Marketplace Metrics

**Plugins:**
- Total: 23 plugins
- Active: 20 plugins
- Deprecated: 3 plugins

**Usage:**
- Total installations: 342
- Active users: 87
- Installations this month: 45

**Quality:**
- Average plugin rating: 4.5/5
- Open issues: 7
- Avg resolution time: 3.2 days

**Growth:**
- New plugins this quarter: 6
- Plugin updates: 34
- New contributors: 5
```

### Plugin Performance

**Monitor:**
- Installation success rate
- Error rates
- Performance impact
- User feedback

**Feedback Collection:**
```markdown
## Plugin Feedback

Rate this plugin: ⭐⭐⭐⭐⭐

What works well?

What could be improved?

Issues encountered:
```

## Migration Strategies

### From Individual Plugins to Marketplace

**Phase 1: Create Marketplace**
```bash
# Collect existing plugins
# Create marketplace repository
# Add all plugins to marketplace.json
```

**Phase 2: Test**
```bash
# Test installations
# Verify functionality
# Document breaking changes
```

**Phase 3: Team Migration**
```bash
# Announce migration plan
# Provide migration guide
# Set deprecation timeline
# Support team during migration
```

**Phase 4: Cleanup**
```bash
# Archive old plugin repositories
# Update documentation
# Remove old installation methods
```

### Between Marketplace Versions

**Breaking Change Migration:**
```markdown
## Migration Guide: v1 to v2

**Timeline:**
- Week 1: v2 available (opt-in)
- Week 2-3: Testing period
- Week 4: v2 default
- Week 5: v1 deprecated
- Week 6: v1 removed

**Changes:**
- Marketplace renamed
- Some plugins reorganized
- New installation method

**Migration Steps:**
1. Uninstall from v1: `/plugin marketplace remove old-marketplace`
2. Add v2: `/plugin marketplace add new-marketplace@v2`
3. Reinstall plugins: `/plugin install plugin-name@new-marketplace`
4. Update project settings
```

## Best Practices Summary

### For Marketplace Maintainers

✅ **Do:**
- Version your marketplace
- Document all changes
- Test before publishing
- Communicate updates clearly
- Review security implications
- Maintain consistent quality
- Provide migration guides

❌ **Don't:**
- Push untested changes
- Break plugins without warning
- Ignore security reviews
- Remove plugins without notice
- Neglect documentation
- Allow unreviewed code

### For Plugin Contributors

✅ **Do:**
- Follow contribution guidelines
- Document your plugin thoroughly
- Test locally before submitting
- Version appropriately
- Respond to feedback
- Update when needed

❌ **Don't:**
- Include secrets in code
- Skip testing
- Ignore review comments
- Break backward compatibility without notice
- Abandon maintained plugins

### For Team Members

✅ **Do:**
- Keep marketplaces updated
- Report issues promptly
- Provide feedback
- Follow team standards
- Read plugin documentation

❌ **Don't:**
- Install unreviewed plugins
- Bypass security policies
- Ignore updates
- Modify plugins locally without contributing back
