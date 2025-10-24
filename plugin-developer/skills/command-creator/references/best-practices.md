# Command Best Practices

Comprehensive guide for writing effective, maintainable, and efficient slash commands.

## Table of Contents

1. [Writing Effective Commands](#writing-effective-commands)
2. [Parameter Design](#parameter-design)
3. [Tool Permissions](#tool-permissions)
4. [Model Selection](#model-selection)
5. [Command Structure](#command-structure)
6. [Error Handling](#error-handling)
7. [Documentation](#documentation)
8. [Maintenance](#maintenance)
9. [Performance Optimization](#performance-optimization)
10. [Team Collaboration](#team-collaboration)

---

## Writing Effective Commands

### Keep Commands Focused

**Do:**
```markdown
---
description: Run all pre-commit checks
---

Run checks in order:
1. Type check
2. Lint
3. Run tests
4. Report results
```

**Don't:**
```markdown
---
description: Do everything before committing and also sync with team and check issues
---

Run checks, sync with remote, check all team PRs, review issues, send notifications...
```

**Why:** Focused commands are easier to understand, test, and maintain. They compose better.

---

### Use Clear, Imperative Instructions

**Do:**
```markdown
1. Fetch PR details: gh pr view $1
2. Review changed files for security issues
3. Check test coverage is above 80%
4. Post review comment with findings
```

**Don't:**
```markdown
Maybe look at the PR and see if there are any issues with security or testing or whatever else seems important.
```

**Why:** Clear, numbered steps are easier for Claude to follow and produce consistent results.

---

### Provide Context and Success Criteria

**Do:**
```markdown
Review PR #$1 for security issues:

Priority checks:
- Input validation (SQL injection, XSS)
- Authentication/authorization
- Sensitive data exposure

Success criteria:
- All security concerns identified
- Severity rating for each issue
- Specific remediation steps provided
```

**Don't:**
```markdown
Review PR #$1 for security.
```

**Why:** Context helps Claude understand priorities. Success criteria ensure consistent quality.

---

### Include Examples in Description

**Do:**
```markdown
---
description: Review PR with priority (high|medium|low). Example: /review-pr 123 high
argument-hint: [PR-number] [priority]
---
```

**Don't:**
```markdown
---
description: Review PR
---
```

**Why:** Examples show users how to invoke commands correctly.

---

### Handle Edge Cases

**Do:**
```markdown
1. Fetch issue #$ARGUMENTS
2. If issue not found:
   - Check if user has access
   - Verify issue number is correct
   - Suggest using: gh issue list
3. If issue is closed:
   - Note status in output
   - Ask if should reopen
```

**Don't:**
```markdown
1. Fetch issue #$ARGUMENTS
2. Do the thing
```

**Why:** Robust commands handle failures gracefully and provide helpful feedback.

---

## Parameter Design

### Choose the Right Parameter Type

**Single Flexible Parameter ($ARGUMENTS):**
```markdown
# Good for: Natural language input, flexible arguments
/fix-issue $ARGUMENTS
# Can be: "123" or "authentication bug" or "issue #456"
```

**Multiple Positional Parameters ($1, $2, $3):**
```markdown
# Good for: Multiple distinct required inputs
/review-pr $1 $2
# $1 = PR number (required)
# $2 = priority (required)
```

**File References (@file):**
```markdown
# Good for: File-specific operations
/optimize @src/utils/helper.ts @src/lib/api.ts
```

**Hybrid Approach:**
```markdown
# Good for: Mix of required and optional
/deploy $1 $ARGUMENTS
# $1 = environment (required)
# $ARGUMENTS = additional flags (optional)
```

---

### Set Clear Argument Hints

**Do:**
```markdown
---
argument-hint: [PR-number] [priority: high|medium|low]
---
```

**Don't:**
```markdown
---
argument-hint: [stuff]
---
```

**Why:** Clear hints guide users and prevent errors.

---

### Provide Defaults for Optional Parameters

**Do:**
```markdown
Review PR #$1 with priority: ${2:-medium}

Priority levels:
- high: Full security and performance review
- medium: Standard code review (default)
- low: Quick scan for major issues
```

**Why:** Defaults make commands flexible and user-friendly.

---

### Validate Parameters

**Do:**
```markdown
1. Validate inputs:
   - Check $1 is a number
   - Check $2 is one of: high, medium, low
   - If invalid, show usage: /review-pr [PR-number] [priority]
   - Exit with clear error message
2. Proceed with validated inputs...
```

**Don't:**
```markdown
1. Use $1 and $2 directly
```

**Why:** Early validation prevents confusing errors later.

---

### Document Parameter Usage

**Do:**
```markdown
---
description: Deploy application to environment
argument-hint: [environment] [options]
---

Deploy to $1 with options: $ARGUMENTS

Environments:
- dev: Development environment
- staging: Staging environment
- production: Production (requires approval)

Options:
- --skip-tests: Skip pre-deployment tests (not recommended)
- --force: Force deployment even with warnings
- --dry-run: Show what would be deployed
```

**Don't:**
```markdown
---
description: Deploy
argument-hint: [env] [opts]
---
```

**Why:** Documentation prevents misuse and reduces support burden.

---

## Tool Permissions

### Principle of Least Privilege

**Do:**
```markdown
---
allowed-tools: Bash(git:*), Read, Grep
---
```

**Don't:**
```markdown
---
# No allowed-tools specified (allows everything)
---
```

**Why:** Restricting tools improves security and prevents unintended operations.

---

### Tool Permission Patterns

**Git Operations:**
```yaml
allowed-tools: Bash(git:*)
# Allows: git status, git commit, git push, etc.
```

**Read-Only Operations:**
```yaml
allowed-tools: Read, Grep, Glob, Bash(git status:*), Bash(git diff:*)
# Allows reading but prevents modifications
```

**Testing Commands:**
```yaml
allowed-tools: Bash(npm test:*), Bash(npm run test:*), Read, Grep
# Allows running tests but not installing packages
```

**File Operations:**
```yaml
allowed-tools: Read, Edit, Write, Glob, Grep
# Allows file operations but no bash commands
```

**Full Access (Use Sparingly):**
```yaml
# Omit allowed-tools field entirely
# Or: allowed-tools: all
```

---

### Specific Tool Restrictions

**Do:**
```markdown
---
# Only allow specific npm scripts
allowed-tools: Bash(npm run lint:*), Bash(npm run test:*)
---
```

**Don't:**
```markdown
---
# Too broad
allowed-tools: Bash(npm:*)
# Allows: npm install, npm uninstall, npm publish, etc.
---
```

**Why:** Specific restrictions prevent accidental dangerous operations.

---

### Progressive Permission Granting

**Start Restrictive:**
```markdown
# Version 1
---
allowed-tools: Read, Grep
---
```

**Add as Needed:**
```markdown
# Version 2 - added Edit after testing
---
allowed-tools: Read, Edit, Grep
---
```

**Why:** Start with minimal permissions and expand based on actual needs.

---

## Model Selection

### Haiku: Fast and Efficient

**Best for:**
- Simple, well-defined tasks
- Repetitive workflows
- Tasks with clear steps
- When speed matters

**Examples:**
```markdown
---
model: claude-3-5-haiku-20241022
---

# Good Haiku tasks:
- /lint-fix: Run linter and apply fixes
- /format-code: Format code with prettier
- /run-tests: Execute test suite
- /git-status: Show current git status
```

**Characteristics:**
- Faster execution
- Lower cost
- Best for < 5 steps
- Clear success/failure criteria

---

### Sonnet: Balanced Default

**Best for:**
- Standard workflows
- Moderate complexity
- Most commands
- Good balance of capability and speed

**Examples:**
```markdown
---
model: claude-3-7-sonnet-20250219
---

# Good Sonnet tasks:
- /review-pr: Code review
- /fix-issue: Fix bugs following workflow
- /refactor-component: Refactor code
- /analyze-logs: Analyze logs for patterns
```

**Characteristics:**
- Good reasoning ability
- Balanced speed/capability
- Handles 5-15 steps well
- Default choice for most commands

---

### Opus: Maximum Capability

**Best for:**
- Complex problem-solving
- Novel situations
- Architectural decisions
- Deep analysis

**Examples:**
```markdown
---
model: claude-opus-4-20250514
---

# Good Opus tasks:
- /design-system: Design system architecture
- /security-audit: Comprehensive security review
- /investigate-outage: Complex debugging
- /optimize-architecture: Performance optimization
```

**Characteristics:**
- Most capable reasoning
- Slower execution
- Higher cost
- Best for complex, novel problems

---

### Model Selection Decision Tree

```
Is the task well-defined with clear steps?
├─ Yes: Can it be done in < 5 simple steps?
│  ├─ Yes: Use Haiku
│  └─ No: Use Sonnet
└─ No: Does it require complex reasoning or novel problem-solving?
   ├─ Yes: Use Opus
   └─ No: Use Sonnet
```

---

### Don't Over-Engineer Model Selection

**Do:**
```markdown
# Use default (Sonnet) unless clear reason to change
---
description: Standard code review
---
```

**Don't:**
```markdown
# Over-thinking it
---
description: Standard code review
model: claude-opus-4-20250514
---
```

**Why:** Sonnet handles most tasks well. Only specify model when there's a clear benefit.

---

## Command Structure

### Use Numbered Steps

**Do:**
```markdown
1. Fetch PR details
2. Review changed files
3. Check test coverage
4. Provide feedback
```

**Don't:**
```markdown
First fetch the PR, then review it, after that check tests, and finally give feedback.
```

**Why:** Numbered steps are clearer and easier to follow.

---

### Group Related Actions

**Do:**
```markdown
1. Pre-flight checks:
   - Verify current branch
   - Check for uncommitted changes
   - Pull latest changes

2. Run validation:
   - Type check
   - Lint
   - Tests
```

**Don't:**
```markdown
1. Verify current branch
2. Check for uncommitted changes
3. Pull latest changes
4. Type check
5. Lint
6. Tests
```

**Why:** Grouping related actions improves readability and understanding.

---

### Include Decision Points

**Do:**
```markdown
3. Check test coverage:
   - If coverage < 80%:
     - List uncovered files
     - Suggest adding tests
     - Wait for user confirmation to proceed
   - If coverage >= 80%:
     - Note coverage is good
     - Proceed to next step
```

**Why:** Explicit decision points handle different scenarios clearly.

---

### Provide Progress Updates

**Do:**
```markdown
5. Run test suite (this may take 2-3 minutes):
   - Start tests
   - Show progress
   - Report results

6. Summary:
   - ✅ Tests passed: 245/245
   - ✅ Coverage: 87%
   - ✅ Lint: No issues
   - Ready for commit
```

**Why:** Progress updates set expectations and provide feedback.

---

## Error Handling

### Anticipate Common Failures

**Do:**
```markdown
1. Fetch PR #$1:
   - Run: gh pr view $1
   - If error "could not resolve":
     - Check if PR number is valid
     - Verify gh is authenticated: gh auth status
     - Suggest: gh auth login
   - If error "not found":
     - PR may not exist
     - Suggest: gh pr list to see available PRs
```

**Why:** Anticipated errors provide better user experience.

---

### Provide Actionable Error Messages

**Do:**
```markdown
❌ Error: Tests failed

Failed tests:
- src/utils/helper.test.ts: 3 tests failed
- src/components/Button.test.tsx: 1 test failed

Next steps:
1. Review failed tests: npm test -- --verbose
2. Fix issues in code
3. Re-run: /pre-commit
```

**Don't:**
```markdown
Tests failed. Fix them.
```

**Why:** Actionable errors help users resolve issues quickly.

---

### Graceful Degradation

**Do:**
```markdown
2. Check test coverage:
   - Try: npm run test:coverage
   - If coverage script not found:
     - Note: No coverage script configured
     - Continue without coverage check
     - Suggest: Add coverage script to package.json
```

**Why:** Commands should work even when optional features are missing.

---

## Documentation

### Write Clear Descriptions

**Do:**
```markdown
---
description: Review PR for security issues, test coverage, and code quality
argument-hint: [PR-number]
---
```

**Don't:**
```markdown
---
description: PR review
---
```

**Why:** Clear descriptions help users find and understand commands.

---

### Document Assumptions

**Do:**
```markdown
---
description: Deploy to environment (requires gh CLI authenticated)
---

Prerequisites:
- gh CLI installed and authenticated
- Access to target environment
- Current branch is main or release/*
```

**Why:** Documenting assumptions prevents confusion and errors.

---

### Include Usage Examples

**Do:**
```markdown
Examples:
  /deploy dev              # Deploy to dev environment
  /deploy staging --force  # Force deploy to staging
  /deploy production       # Deploy to production (requires approval)
```

**Why:** Examples show proper usage and available options.

---

## Maintenance

### Regular Review

**Review commands quarterly:**
- Are they still being used?
- Do steps need updating?
- Are tool permissions still appropriate?
- Can they be simplified?
- Should they be combined or split?

---

### Version Control Commands

**Do:**
```markdown
# Commit project commands to git
git add .claude/commands/
git commit -m "chore: update review-pr command for new workflow"
```

**Why:** Version control tracks changes and enables team collaboration.

---

### Keep Commands DRY

**Don't repeat common steps:**

**Bad:**
```markdown
# In multiple commands:
1. Check if gh is authenticated
2. Verify gh CLI installed
3. Check git status
```

**Good:**
```markdown
# Create /check-setup command
# Reference in other commands:
1. Run setup check (see /check-setup)
2. Proceed with main workflow...
```

---

### Deprecation Strategy

**When removing commands:**
```markdown
---
description: [DEPRECATED] Use /new-command instead
---

⚠️  This command is deprecated and will be removed in v2.0

Please use /new-command instead:
  /new-command has improved features and performance

Migration guide: docs/migration/old-to-new.md
```

**Why:** Graceful deprecation helps users transition smoothly.

---

## Performance Optimization

### Minimize Unnecessary Operations

**Do:**
```markdown
1. Check if tests are needed:
   - If only docs changed: skip tests
   - If code changed: run relevant tests only
```

**Don't:**
```markdown
1. Always run all tests
```

**Why:** Smart skipping reduces wait time.

---

### Use Appropriate Commands

**Do:**
```markdown
# Fast status check
Bash(git status --short)

# Quick file list
Glob(**/*.ts)
```

**Don't:**
```markdown
# Slow and verbose
Bash(git status --verbose --long-format)

# Inefficient
Bash(find . -name "*.ts")
```

**Why:** Efficient commands improve user experience.

---

### Cache When Possible

**Do:**
```markdown
1. Check if build artifacts exist:
   - If dist/ exists and newer than src/: skip rebuild
   - If missing or outdated: rebuild
```

**Why:** Avoiding redundant work saves time.

---

## Team Collaboration

### Establish Team Conventions

**Document in CLAUDE.md:**
```markdown
## Slash Commands

Project commands available:
- /review-pr [number]: Standard PR review
- /fix-issue [number]: Fix issue workflow
- /pre-commit: Pre-commit validation

Team conventions:
- Always run /pre-commit before committing
- Use /review-pr for all PR reviews
- Run /morning-routine at start of day
```

---

### Share Commands Effectively

**Project commands:**
```
.claude/commands/       # Commit to git
├── review-pr.md       # Team command
├── fix-issue.md       # Team command
└── README.md          # Document all commands
```

**Personal commands:**
```
~/.claude/commands/     # Personal, not committed
├── daily-notes.md     # Personal workflow
└── time-tracking.md   # Personal tool
```

---

### Gather Feedback

**Regular retrospectives:**
- Which commands are most useful?
- What commands are confusing?
- What new commands are needed?
- What commands should be deprecated?

**Iterate based on feedback:**
- Improve clarity
- Add requested features
- Remove unused commands
- Combine similar commands

---

## Summary

**Key Principles:**

1. **Focus**: One clear purpose per command
2. **Clarity**: Numbered steps, clear instructions
3. **Security**: Minimal tool permissions
4. **Performance**: Right model for the task
5. **Robustness**: Handle errors gracefully
6. **Documentation**: Clear descriptions and examples
7. **Maintenance**: Regular review and updates
8. **Collaboration**: Share effectively with team

**Remember:**
- Start simple, iterate based on usage
- Test commands thoroughly
- Document assumptions and requirements
- Gather feedback and improve continuously
- Use appropriate model for complexity
- Grant minimal necessary permissions
- Handle edge cases and errors
- Keep commands focused and composable

Following these best practices will lead to reliable, maintainable, and effective commands that enhance your team's productivity.
