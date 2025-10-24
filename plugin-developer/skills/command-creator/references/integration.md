# Integration with Claude Code Features

How slash commands integrate with other Claude Code features including CLAUDE.md, hooks, skills, memory, and MCP servers.

## Table of Contents

1. [Commands vs Other Features](#commands-vs-other-features)
2. [Integration with CLAUDE.md](#integration-with-claudemd)
3. [Integration with Hooks](#integration-with-hooks)
4. [Integration with Skills](#integration-with-skills)
5. [Integration with Memory](#integration-with-memory)
6. [Integration with MCP Servers](#integration-with-mcp-servers)
7. [Integration Patterns](#integration-patterns)
8. [Best Practices](#best-practices)

---

## Commands vs Other Features

### Comparison Table

| Feature | Trigger | Scope | Context | Use Case |
|---------|---------|-------|---------|----------|
| **Commands** | Manual: `/command` | Task execution | Ephemeral | Repeatable workflows |
| **CLAUDE.md** | Automatic: always loaded | Project context | Persistent | Conventions, standards |
| **Skills** | Automatic: Claude decides | Procedural knowledge | On-demand | Specialized capabilities |
| **Hooks** | Automatic: on events | Event response | Per-event | Validation, automation |
| **Memory** | Automatic: past context | Historical data | Cross-session | Preferences, patterns |
| **MCP** | Tool calls | External data | Request-based | External integrations |

---

### When to Use Each

**Commands:**
- User explicitly wants to run a workflow
- Parameterized, reusable task
- Multiple steps with clear sequence
- Example: `/review-pr 123`, `/fix-issue 456`

**CLAUDE.md:**
- Project-wide conventions
- Always-relevant context
- Team standards and patterns
- Example: Coding standards, architecture overview

**Skills:**
- Procedural knowledge Claude needs
- Complex multi-step capabilities
- Claude decides when to invoke
- Example: PDF manipulation, spreadsheet analysis

**Hooks:**
- Automatic validation on events
- Pre/post operation checks
- Enforcing standards automatically
- Example: Pre-commit validation, post-PR creation

**Memory:**
- User preferences across sessions
- Historical context
- Learned patterns
- Example: Code style preferences, common tasks

**MCP Servers:**
- External system integration
- Real-time data access
- API interactions
- Example: Database queries, Slack messages

---

## Integration with CLAUDE.md

### Complementary Roles

**CLAUDE.md provides context, Commands provide action:**

```markdown
# CLAUDE.md - Context

## Project Standards
- TypeScript strict mode
- Follow Airbnb style guide
- Write tests for all features
- Use conventional commits

## Architecture
- Frontend: React + Redux
- Backend: Node.js + Express
- Database: PostgreSQL

## Workflows
For standard workflows, use these commands:
- `/pre-commit` - Validate before committing
- `/review-pr [number]` - Review pull requests
- `/fix-issue [number]` - Fix issues systematically
```

**Commands reference and implement standards:**

```markdown
# .claude/commands/pre-commit.md
---
description: Pre-commit validation per CLAUDE.md standards
---

Validate changes per project standards:

1. Run checks from CLAUDE.md requirements:
   - TypeScript strict mode: npm run type:check
   - Airbnb style: npm run lint
   - Tests required: npm test
   - Commit message format: conventional commits

2. Report: ✅ Ready or ❌ Issues to fix
```

---

### Referencing CLAUDE.md from Commands

**Explicit reference:**
```markdown
1. Check project standards:
   - Read: CLAUDE.md conventions section
   - Apply standards to code review
   - Report violations with reference to CLAUDE.md
```

**Implicit alignment:**
```markdown
# Command naturally follows CLAUDE.md patterns
1. Format code:
   - Follow Airbnb style (as specified in CLAUDE.md)
   - Use project's prettier config
   - Match existing code style
```

---

### Documenting Commands in CLAUDE.md

**List available commands:**
```markdown
# CLAUDE.md

## Available Commands

### Development Workflow
- `/pre-commit` - Validate changes before committing
- `/fix-issue [number]` - Fix GitHub issue systematically
- `/review-pr [number]` - Review pull request

### Testing
- `/test-all` - Run complete test suite
- `/test-coverage` - Check test coverage

### Deployment
- `/deploy [env]` - Deploy to environment (dev/staging/prod)

For command details, see `.claude/commands/` directory.
```

---

### Use Cases

**Commands Implementing CLAUDE.md Standards:**
```markdown
# CLAUDE.md defines standard
## Code Review Checklist
- Security: Input validation, auth checks
- Performance: Query efficiency, bundle size
- Tests: Coverage > 80%, edge cases
- Docs: Public APIs documented

# Command implements standard
# /review-pr
---
description: Review PR following project checklist
---

Review PR #$1 per CLAUDE.md standards:

1. Read review checklist from CLAUDE.md
2. Apply each check:
   - Security review
   - Performance check
   - Test coverage verification
   - Documentation completeness
3. Report findings by category
```

**CLAUDE.md Referencing Commands:**
```markdown
# CLAUDE.md
## Git Workflow

Before committing:
1. Run `/pre-commit` to validate changes
2. Fix any issues reported
3. Commit with conventional commit format

Before creating PR:
1. Run `/prepare-pr main` to prepare PR
2. Review generated PR description
3. Submit PR

After PR approved:
1. Merge PR
2. Run `/post-merge` to clean up
```

---

## Integration with Hooks

### Comparison: Hooks vs Commands

| Aspect | Hooks | Commands |
|--------|-------|----------|
| **Trigger** | Automatic (on events) | Manual (user invokes) |
| **Use** | Validation, automation | Workflows, tasks |
| **Timing** | Pre/post operations | Anytime |
| **Control** | System-triggered | User-triggered |

---

### Commands Complementing Hooks

**Hook provides automatic check, Command provides manual run:**

```bash
# .claude/hooks/pre-commit.sh
#!/bin/bash
# Runs automatically before every commit

npm run lint || exit 1
npm test || exit 1
```

```markdown
# .claude/commands/pre-commit.md
---
description: Manually run pre-commit checks
---

Run pre-commit validation:

1. Same checks as pre-commit hook:
   - Lint: npm run lint
   - Tests: npm test

2. This command is useful for:
   - Testing before actual commit
   - Fixing issues before hook runs
   - Running checks outside commit flow
```

---

### Commands Calling Hook-Like Validation

```markdown
# /validate-changes
---
description: Validate changes (similar to pre-commit hook)
---

Validate without committing:

1. Run validations:
   - Type check
   - Lint
   - Tests
   - Security checks

2. Report results:
   - ✅ Would pass pre-commit hook
   - ❌ Would fail pre-commit hook: [reasons]

3. This lets you validate before committing
```

---

### Hooks Triggering Commands

**Hook can invoke command for complex operations:**

```bash
# .claude/hooks/post-pr-create.sh
#!/bin/bash
# After PR created, run comprehensive setup

PR_NUMBER=$1

# Invoke command for complex workflow
claude /setup-pr $PR_NUMBER
```

```markdown
# /setup-pr
---
description: Complete PR setup after creation
---

Setup PR #$1:

1. Add standard labels based on files changed
2. Request reviewers based on CODEOWNERS
3. Add to project board
4. Link related issues
5. Post welcome comment with checklist
```

---

### Use Cases

**Pre-Commit Hook + Command:**
```bash
# Hook: Automatic enforcement
# .claude/hooks/pre-commit.sh
npm run lint --quiet || exit 1

# Command: Manual check with details
# /pre-commit-check
Full validation with detailed output and suggestions
```

**Post-PR Hook + Command:**
```bash
# Hook: Trigger command
# .claude/hooks/post-pr-create.sh
claude /pr-setup $PR_NUMBER

# Command: Do the work
# /pr-setup
Comprehensive PR setup and configuration
```

---

## Integration with Skills

### Comparison: Skills vs Commands

| Aspect | Skills | Commands |
|--------|--------|----------|
| **Invocation** | Claude decides | User invokes |
| **Purpose** | Capabilities for Claude | Workflows for users |
| **Complexity** | Can be very complex | Generally focused |
| **Tools** | Can include scripts | Just prompts |

---

### Commands Leveraging Skills

**Command triggers skill indirectly:**
```markdown
# /analyze-spreadsheet @file.xlsx
---
description: Analyze spreadsheet data
---

Analyze spreadsheet: $ARGUMENTS

1. Read spreadsheet file
   (Claude will use xlsx skill automatically if available)

2. Provide analysis:
   - Summary statistics
   - Data quality issues
   - Visualizations
   - Insights
```

**When user invokes command:**
- User: `/analyze-spreadsheet @data.xlsx`
- Command expands to prompt
- Claude sees xlsx file reference
- Claude invokes xlsx skill to read file
- Claude provides analysis

---

### Skills Supporting Commands

**Skill provides capability, Command provides workflow:**

```markdown
# Skill: document-skills:pdf
Provides: PDF reading, manipulation, form filling

# Command: /fill-form @form.pdf
---
description: Fill PDF form with data
---

Fill form: $ARGUMENTS

1. Read PDF form fields
   (Uses PDF skill)

2. Ask user for field values

3. Fill form with values
   (Uses PDF skill)

4. Save filled form
```

---

### Commands Calling Commands (Using Skills)

```markdown
# /complete-onboarding @docs/*.pdf
---
description: Complete onboarding with documents
---

Process onboarding documents:

1. For each PDF in $ARGUMENTS:
   - Read document (PDF skill)
   - Extract required information
   - Fill forms (PDF skill)
   - Organize by type

2. Create summary report (docx skill)

3. Package everything for submission
```

---

### Use Cases

**Skill Provides Foundation:**
```markdown
# PDF Skill: Provides PDF capabilities
- Read PDFs
- Extract text and tables
- Fill forms
- Merge/split PDFs

# Commands Use Skill:
- /extract-invoice-data @invoice.pdf
- /fill-application @form.pdf
- /merge-reports @*.pdf
- /extract-tables @document.pdf
```

**Command Orchestrates Multiple Skills:**
```markdown
# /process-documents @folder
---
description: Process mixed document types
---

Process documents in: $ARGUMENTS

1. Identify document types:
   - PDFs (use PDF skill)
   - Spreadsheets (use xlsx skill)
   - Word docs (use docx skill)

2. Process each by type:
   - Extract data using appropriate skill
   - Standardize format
   - Validate data

3. Combine into summary report (docx skill)
```

---

## Integration with Memory

### How Memory Affects Commands

**Memory stores:**
- User preferences
- Common patterns
- Past interactions
- Project context

**Commands benefit from memory:**
```markdown
# /deploy
---
description: Deploy application
---

Deploy application:

1. Use memory for defaults:
   - Last deployed environment
   - Common deployment options
   - Previous issues and solutions

2. Adapt based on history:
   - If last 3 deploys to staging: suggest staging
   - If user prefers skip-tests: offer as option
   - If past issues with region: warn

3. Learn from this deployment:
   - Store choices for next time
   - Note any issues
   - Remember successful patterns
```

---

### Commands Updating Memory

```markdown
# /set-preference
---
description: Set preference for future commands
---

Set preference: $ARGUMENTS

1. Parse preference:
   - Type: code style, testing, deployment, etc.
   - Value: user's preference

2. Store in memory:
   - Remember for future sessions
   - Apply to relevant commands

3. Confirm: Preference saved and will be used

Examples:
- /set-preference default-test-framework jest
- /set-preference code-review-depth thorough
- /set-preference deployment-environment staging
```

---

### Memory-Aware Commands

```markdown
# /review-code @files
---
description: Review code files
---

Review code: $ARGUMENTS

1. Load from memory:
   - User's review priorities
   - Past issues found in similar code
   - Project-specific patterns to check

2. Adapt review based on memory:
   - Focus on areas user cares about
   - Check for similar issues to past
   - Apply learned project patterns

3. Update memory:
   - Note new issues to watch for
   - Learn from user feedback
   - Refine review patterns
```

---

### Use Cases

**Personalized Workflows:**
```markdown
# /my-morning-routine
Adapts based on:
- Your typical morning tasks (from memory)
- Projects you work on most (from memory)
- Time of week (from patterns)
- Your preferences (from memory)

Provides:
- Personalized task list
- Relevant project updates
- Adapted to your patterns
```

**Learning from Usage:**
```markdown
# /deploy
Over time learns:
- Your typical deployment patterns
- Environments you use most
- Common options you select
- Issues you've encountered

Provides:
- Smarter defaults
- Proactive warnings
- Personalized suggestions
```

---

## Integration with MCP Servers

### What MCP Provides

**MCP Servers enable:**
- External system integration
- Real-time data access
- API interactions
- Database queries

### Commands Using MCP Servers

**Command leverages MCP for data:**
```markdown
# /check-ticket
---
description: Check Jira ticket status
argument-hint: [ticket-id]
---

Check ticket: $1

1. Fetch from Jira (via MCP):
   - Use Jira MCP server
   - Get ticket details
   - Get comments and history

2. Analyze ticket:
   - Status and progress
   - Blockers
   - Assignee and priority

3. Provide summary and next steps
```

---

### MCP Integration Examples

**Database MCP:**
```markdown
# /query-data
---
description: Query database for information
---

Query: $ARGUMENTS

1. Connect via Database MCP server

2. Run query: $ARGUMENTS

3. Format and display results

4. Provide insights on data
```

**Slack MCP:**
```markdown
# /notify-team
---
description: Send notification to team Slack
---

Send notification: $ARGUMENTS

1. Format message: $ARGUMENTS

2. Send via Slack MCP server

3. Confirm delivery

4. Show sent message
```

**GitHub MCP:**
```markdown
# /pr-stats
---
description: Get PR statistics
---

PR statistics:

1. Fetch via GitHub MCP:
   - Open PRs
   - Review status
   - CI/CD status
   - Time in review

2. Analyze data:
   - Bottlenecks
   - Trends
   - Team velocity

3. Visualize and report
```

---

### Use Cases

**Data-Driven Commands:**
```markdown
# /analyze-performance
Uses:
- Database MCP: Query metrics
- Monitoring MCP: Get current stats
- GitHub MCP: Correlate with deployments

Provides:
- Comprehensive performance analysis
- Correlations with code changes
- Actionable recommendations
```

**Cross-System Workflows:**
```markdown
# /create-ticket-and-branch
---
description: Create Jira ticket and git branch
---

Create ticket and branch: $ARGUMENTS

1. Create Jira ticket (via Jira MCP):
   - Title: $ARGUMENTS
   - Project: from current directory
   - Type: task

2. Create branch (via git):
   - Name: feature/[ticket-id]/[description]

3. Setup tracking:
   - Link branch to ticket
   - Set status to In Progress

4. Summary: Ready to work on [ticket-id]
```

---

## Integration Patterns

### Pattern 1: Layered Integration

```
User invokes command
    ↓
Command uses CLAUDE.md context
    ↓
Command may trigger skill
    ↓
Skill may use MCP server
    ↓
Results returned to user
```

**Example:**
```markdown
# User: /analyze-sales-data @report.xlsx

1. Command: analyze-sales-data
   - Reads CLAUDE.md for business context
   - Knows company's sales KPIs

2. Triggers xlsx skill (Claude decides)
   - Skill reads spreadsheet
   - Extracts data

3. Skill might use Database MCP
   - Get historical data
   - Compare trends

4. Command provides analysis
   - Contextualized with CLAUDE.md
   - Includes recommendations
```

---

### Pattern 2: Hook → Command → Skill

```
Event occurs
    ↓
Hook triggered
    ↓
Hook invokes command
    ↓
Command uses skills
    ↓
Results processed
```

**Example:**
```bash
# PR created (event)
    ↓
# post-pr-create hook runs
    ↓
# Hook invokes: /setup-pr [pr-number]
    ↓
# Command reads PR (may use GitHub skill/MCP)
    ↓
# Command configures PR
```

---

### Pattern 3: Memory-Enhanced Commands

```
User invokes command
    ↓
Load preferences from memory
    ↓
Adapt behavior to user
    ↓
Execute with personalization
    ↓
Update memory with learnings
```

**Example:**
```markdown
# User: /deploy

1. Load from memory:
   - Last 10 deployments
   - User's typical environment
   - Previous issues

2. Adapt defaults:
   - Suggest most-used environment
   - Pre-select common options
   - Warn about past issues

3. Execute deployment

4. Update memory:
   - Store this deployment
   - Note any new patterns
   - Learn from outcomes
```

---

### Pattern 4: CLAUDE.md + Commands + Hooks

```
CLAUDE.md: Defines standards
    ↓
Commands: Implement workflows following standards
    ↓
Hooks: Automatically enforce standards
    ↓
All aligned and consistent
```

**Example:**
```markdown
# CLAUDE.md
Standards:
- Test coverage > 80%
- Conventional commits
- Code review required

# /pre-commit (command)
Validates:
- Test coverage
- Commit message format
- (manual workflow)

# pre-commit hook
Enforces:
- Same validations
- (automatic enforcement)

# Both use same standards from CLAUDE.md
```

---

## Best Practices

### 1. Clear Separation of Concerns

**Do:**
- CLAUDE.md: Context and standards
- Commands: User-triggered workflows
- Skills: Capabilities for Claude
- Hooks: Automatic enforcement
- Memory: Personalization
- MCP: External integration

**Don't:**
- Mix responsibilities
- Duplicate information
- Create circular dependencies

---

### 2. Consistent References

**Document connections:**
```markdown
# CLAUDE.md
For pre-commit checks, use /pre-commit command

# /pre-commit command
Follows standards defined in CLAUDE.md

# pre-commit hook
Enforces same checks as /pre-commit command
```

---

### 3. Avoid Duplication

**Instead of duplicating:**
```markdown
# ❌ CLAUDE.md
Detailed commit message format rules...

# ❌ /pre-commit
Same detailed commit message format rules...

# ❌ pre-commit hook
Same detailed commit message format rules...
```

**Reference common source:**
```markdown
# ✅ CLAUDE.md
## Commit Message Format
[Detailed rules]

# ✅ /pre-commit
Validate commit message per CLAUDE.md format

# ✅ pre-commit hook
#!/bin/bash
# Validates per CLAUDE.md commit format
```

---

### 4. Leverage Each Feature's Strengths

**Use right tool for the job:**

| Need | Use |
|------|-----|
| Always-on context | CLAUDE.md |
| User workflow | Command |
| Complex capability | Skill |
| Automatic enforcement | Hook |
| Personalization | Memory |
| External data | MCP |

---

### 5. Graceful Integration

**Commands should work with or without extras:**
```markdown
# /review-pr
---
description: Review PR (works standalone or with integrations)
---

Review PR #$1:

1. Fetch PR:
   - Try: gh CLI (if available)
   - Try: GitHub MCP (if available)
   - Fallback: ask user to open GitHub

2. Apply standards:
   - From CLAUDE.md if available
   - Use defaults otherwise

3. Use memory:
   - Apply user preferences if available
   - Use standard settings otherwise
```

---

### 6. Document Integrations

**Make connections explicit:**
```markdown
# /deploy
---
description: Deploy application
# Note: Uses deployment-env MCP server if available
# Note: Respects preferences in CLAUDE.md
# Note: Follows post-deploy hook conventions
---

Deploy to ${1:-staging}:
[workflow]
```

---

## Integration Examples

### Complete Integration Example

**Project setup using all features:**

```markdown
# CLAUDE.md - Project Context
## Standards
- TypeScript strict mode
- Test coverage > 80%
- Conventional commits

## Commands Available
- /pre-commit: Pre-commit validation
- /review-pr: PR review
- /deploy: Deployment

## Integrations
- Jira MCP: For ticket management
- Slack MCP: For notifications
```

```markdown
# /pre-commit - Command
---
description: Pre-commit validation per CLAUDE.md
---

Validate per CLAUDE.md standards:
1. TypeScript strict check
2. Test coverage check
3. Commit message format
```

```bash
# .claude/hooks/pre-commit.sh - Hook
#!/bin/bash
# Automatic enforcement
npm run type:check || exit 1
npm run test:coverage || exit 1
```

```markdown
# /deploy - Memory-aware command
---
description: Deploy with preferences
---

Deploy (uses memory for defaults):
1. Load user's typical environment
2. Apply common options
3. Execute deployment
4. Notify via Slack MCP
5. Update Jira via MCP
6. Store learnings in memory
```

**Result:**
- CLAUDE.md provides context
- /pre-commit implements workflow
- Hook enforces automatically
- Memory personalizes experience
- MCP connects external systems
- All work together seamlessly

---

## Summary

**Key Integration Principles:**

1. **Complementary**: Each feature serves distinct purpose
2. **Aligned**: All follow same standards and patterns
3. **Referenced**: Explicit connections documented
4. **Graceful**: Work independently or together
5. **Efficient**: Avoid duplication, leverage strengths

**Best Integration Approach:**
- Define standards in CLAUDE.md
- Implement workflows in commands
- Automate enforcement with hooks
- Enhance with skills for capabilities
- Personalize with memory
- Connect external systems with MCP
- Document all connections

**Remember:**
- Start simple, add integrations as needed
- Keep each feature focused on its purpose
- Document connections clearly
- Test integration points
- Maintain consistency across features
