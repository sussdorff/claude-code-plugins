# Command Templates Library

Comprehensive collection of command templates for common workflows. Each template includes use case, when to use, template code, and customization options.

## Table of Contents

1. [Simple Git Workflow](#simple-git-workflow)
2. [Multi-Step Testing](#multi-step-testing)
3. [Code Review](#code-review)
4. [Issue Triage](#issue-triage)
5. [Fix Issue Workflow](#fix-issue-workflow)
6. [PR Review with Priority](#pr-review-with-priority)
7. [Log Analysis](#log-analysis)
8. [Pre-Commit Validation](#pre-commit-validation)
9. [PR Preparation](#pr-preparation)
10. [Morning Routine](#morning-routine)
11. [Component Creation](#component-creation)
12. [Database Migration](#database-migration)
13. [Dependency Update](#dependency-update)
14. [Security Audit](#security-audit)
15. [Performance Analysis](#performance-analysis)

---

## Simple Git Workflow

### Use Case
Quick git status check and commit workflow for daily development.

### When to Use
- Multiple times daily during active development
- Need quick overview of changes
- Simple commit without complex branching

### Template

```markdown
---
description: Show git status and help create commit
allowed-tools: Bash(git:*)
model: claude-3-5-haiku-20241022
---

Quick git workflow:

1. Show current branch: git branch --show-current
2. Show status: git status
3. Show staged changes: git diff --cached
4. Show unstaged changes: git diff
5. If changes exist, ask if user wants to commit
6. If yes, suggest commit message based on changes
7. Show summary of what was done
```

### Customization Options
- Add push step after commit
- Include pre-commit hooks
- Add branch creation if on main
- Include remote sync check
- Add stash operations

---

## Multi-Step Testing

### Use Case
Run complete test suite with coverage and reporting.

### When to Use
- Before committing changes
- Before creating PRs
- After significant refactoring
- CI/CD validation locally

### Template

```markdown
---
description: Run complete test suite with coverage
allowed-tools: Bash(npm:*), Bash(pnpm:*), Read, Glob
model: claude-3-5-haiku-20241022
---

Run comprehensive test suite:

1. Check package.json for test scripts
2. Run unit tests: npm test
3. Run integration tests if available: npm run test:integration
4. Check test coverage: npm run test:coverage
5. List any files below coverage threshold
6. Run linter: npm run lint
7. Run type check if TypeScript: npm run type:check
8. Summary report:
   - ✅ Tests passed: X/Y
   - ✅ Coverage: X%
   - ✅ Lint: pass/fail
   - ✅ Types: pass/fail

Exit with clear pass/fail status.
```

### Customization Options
- Add e2e tests
- Include performance benchmarks
- Add visual regression tests
- Configure coverage thresholds
- Add specific test patterns
- Include watch mode option

---

## Code Review

### Use Case
Systematic code review of files or entire PRs.

### When to Use
- Reviewing teammate's code
- Self-review before submitting PR
- Architecture review
- Security review

### Template

```markdown
---
description: Perform systematic code review
argument-hint: [@files or PR-number]
allowed-tools: Bash(gh:*), Bash(git:*), Read, Grep, Glob
---

Code review for $ARGUMENTS:

1. Identify scope:
   - If number: fetch PR with gh pr view $ARGUMENTS
   - If @files: review specified files
   - If nothing: review git diff --cached

2. Review checklist:
   - **Correctness**: Logic errors, edge cases
   - **Tests**: Coverage, test quality
   - **Security**: Vulnerabilities, input validation
   - **Performance**: Inefficiencies, memory leaks
   - **Maintainability**: Code clarity, documentation
   - **Style**: Consistency with codebase

3. For each issue found:
   - Severity: critical/major/minor
   - Location: file:line
   - Description: what's wrong
   - Suggestion: how to fix

4. Summary:
   - Overall assessment
   - Must-fix issues
   - Nice-to-have improvements
   - Positive observations

5. Recommendation: approve/request changes/comment
```

### Customization Options
- Focus on specific aspects (security, performance)
- Add automated checks integration
- Include architectural review
- Add compliance checks
- Custom review checklists per project

---

## Issue Triage

### Use Case
Analyze, categorize, and prioritize GitHub/GitLab issues.

### When to Use
- New issues need classification
- Backlog grooming
- Bug report analysis
- Feature request evaluation

### Template

```markdown
---
description: Analyze and categorize issue
argument-hint: [issue-number]
allowed-tools: Bash(gh:*), Bash(glab:*), Read, Grep, Glob
---

Triage issue #$ARGUMENTS:

1. Fetch issue details:
   - GitHub: gh issue view $ARGUMENTS
   - GitLab: glab issue view $ARGUMENTS

2. Analyze issue:
   - Is description clear and complete?
   - Can issue be reproduced?
   - Is it duplicate of existing issue?
   - What components are affected?

3. Search codebase for related code:
   - Grep for mentioned files/functions
   - Find similar issues in history
   - Locate relevant test files

4. Categorization:
   - Type: bug/feature/docs/question/enhancement
   - Priority: critical/high/medium/low
   - Effort: small/medium/large
   - Area: frontend/backend/infrastructure/etc

5. Recommendations:
   - Suggested labels
   - Milestone assignment
   - Related issues to link
   - Questions to ask reporter (if unclear)
   - Potential assignees

6. Draft response if needed:
   - Thank reporter
   - Ask clarifying questions
   - Set expectations
   - Provide workarounds if available
```

### Customization Options
- Custom labels per project
- Integration with project management tools
- Automated duplicate detection
- Priority scoring system
- SLA tracking

---

## Fix Issue Workflow

### Use Case
Systematic workflow for fixing bugs or implementing features from issues.

### When to Use
- Starting work on assigned issue
- Following structured development process
- Ensuring all steps completed
- Team standardization

### Template

```markdown
---
description: Fix issue following project standards
argument-hint: [issue-number]
allowed-tools: Bash(gh:*), Bash(git:*), Read, Edit, Write, Glob, Grep
---

Fix issue #$ARGUMENTS:

1. Fetch issue details: gh issue view $ARGUMENTS

2. Extract key information:
   - Issue title and description
   - Expected vs actual behavior
   - Steps to reproduce (if bug)
   - Acceptance criteria (if feature)

3. Create branch:
   - Format: fix/$ARGUMENTS/short-description
   - git checkout -b fix/$ARGUMENTS/description

4. Understand current code:
   - Read relevant files mentioned in issue
   - Search for related functions/components
   - Review existing tests

5. Implement fix/feature:
   - Follow coding standards in CLAUDE.md
   - Add/update tests first (TDD if appropriate)
   - Implement changes
   - Add/update documentation

6. Validation:
   - Run affected tests
   - Run full test suite
   - Manual testing if needed
   - Check for unintended side effects

7. Commit changes:
   - Message: "fix: resolve issue #$ARGUMENTS - brief description"
   - Include "Closes #$ARGUMENTS" in body

8. Create PR:
   - Push branch: git push -u origin branch-name
   - Create PR: gh pr create
   - Link to issue
   - Add relevant labels

9. Summary:
   - Changes made
   - Tests added/updated
   - PR URL
   - Next steps (wait for review)
```

### Customization Options
- Add pre-commit hooks
- Include deployment steps
- Add screenshots for UI changes
- Integration with project management
- Custom commit message format
- Add changelog update

---

## PR Review with Priority

### Use Case
Review pull requests with different depth levels based on priority.

### When to Use
- Reviewing team PRs
- Different review depth needed
- Time-constrained reviews
- Risk-based review approach

### Template

```markdown
---
description: Review PR with specified priority level
argument-hint: [PR-number] [priority: high|medium|low]
allowed-tools: Bash(gh:*), Bash(git:*), Read, Grep, Glob
---

Review PR #$1 with priority: $2

1. Fetch PR details: gh pr view $1
2. Fetch PR diff: gh pr diff $1
3. Identify changed files and scope

4. Review based on priority level:

**High Priority (security, production hotfix, breaking changes):**
- Full security review (input validation, auth, sensitive data)
- Architecture impact analysis
- Performance implications
- Breaking changes assessment
- Comprehensive test coverage check
- Documentation completeness
- Deployment considerations

**Medium Priority (standard features, bug fixes):**
- Logic correctness
- Test coverage for changes
- Code style consistency
- Basic security check
- Error handling
- Documentation for public APIs

**Low Priority (docs, minor fixes, refactoring):**
- Basic correctness
- No obvious issues
- Follows style guide
- Tests present if needed

5. Provide feedback:
   - Issues found by severity
   - Suggestions for improvement
   - Positive observations

6. Decision:
   - Approve (if no blocking issues)
   - Request changes (if critical issues)
   - Comment (if only suggestions)

7. Post review: gh pr review $1 --[approve|request-changes|comment]
```

### Customization Options
- Custom priority definitions
- Automated checks integration
- Risk scoring system
- Reviewer assignment logic
- Review time tracking
- Template responses

---

## Log Analysis

### Use Case
Analyze application logs for errors, patterns, and insights.

### When to Use
- Debugging production issues
- Performance investigation
- Error pattern analysis
- System health check

### Template

```markdown
---
description: Analyze logs for errors and patterns
argument-hint: [@log-file or service-name]
allowed-tools: Read, Grep, Bash(tail:*), Bash(grep:*)
---

Analyze logs: $ARGUMENTS

1. Identify log source:
   - If @file: read specified file
   - If service: fetch recent logs
   - If nothing: ask user for log location

2. Basic statistics:
   - Total lines
   - Date range covered
   - Log volume over time

3. Error analysis:
   - Count errors by severity (ERROR, WARN, INFO)
   - Identify unique error messages
   - Find most frequent errors
   - Extract stack traces for critical errors

4. Pattern detection:
   - Repeated error sequences
   - Time-based patterns (hourly spikes)
   - User/session patterns if applicable
   - Performance metrics (response times)

5. Anomaly detection:
   - Sudden error rate increases
   - Unusual patterns
   - Missing expected log entries
   - Gaps in logging

6. Context gathering:
   - Events before/after errors
   - Related log entries
   - User actions leading to errors
   - System state during issues

7. Summary report:
   - Top 5 issues by frequency
   - Critical errors requiring immediate attention
   - Trends and patterns
   - Recommended actions
   - Areas needing investigation

8. Actionable recommendations:
   - Immediate fixes needed
   - Monitoring to add
   - Code improvements
   - Infrastructure changes
```

### Customization Options
- Structured log parsing (JSON, etc)
- Integration with log aggregation tools
- Custom error patterns
- Alerting thresholds
- Time range filtering
- Service-specific analysis

---

## Pre-Commit Validation

### Use Case
Validate all changes before committing to ensure quality.

### When to Use
- Before every commit
- As git pre-commit hook
- Team quality gates
- CI/CD alignment

### Template

```markdown
---
description: Validate changes before committing
allowed-tools: Bash(git:*), Bash(npm:*), Bash(pnpm:*), Read, Grep
model: claude-3-5-haiku-20241022
---

Pre-commit validation:

1. Show what will be committed:
   - git diff --cached --stat
   - git diff --cached

2. Automated checks:
   - Run type check: npm run type:check
   - Run linter: npm run lint --fix
   - Run tests for changed files
   - Check formatting: npm run format:check

3. Manual checks:
   - Search for console.log in staged files
   - Search for debugger statements
   - Check for TODO/FIXME without issue numbers
   - Verify no sensitive data (keys, passwords)
   - Check for commented code blocks

4. File-specific checks:
   - Package.json: validate format, check for conflicts
   - Lock files: ensure in sync with package.json
   - Config files: validate syntax
   - Documentation: check for broken links

5. Commit message validation:
   - If commit message exists, check format
   - Suggest message based on changes if needed
   - Validate conventional commit format if used

6. Summary:
   ✅ All checks passed - safe to commit
   ❌ Issues found - fix before committing:
      - List all blocking issues
      - List warnings (non-blocking)

7. If issues found, offer to fix auto-fixable items
```

### Customization Options
- Custom lint rules
- Project-specific checks
- Skip options for emergencies
- Integration with Husky/lint-staged
- Custom commit message format
- File size limits
- Dependency security checks

---

## PR Preparation

### Use Case
Prepare comprehensive PR with all necessary information.

### When to Use
- Ready to create PR
- Ensuring PR quality
- Team PR standards
- Complete documentation

### Template

```markdown
---
description: Prepare comprehensive pull request
argument-hint: [base-branch]
allowed-tools: Bash(gh:*), Bash(git:*), Read, Grep, Glob
---

Prepare PR for merge into $ARGUMENTS:

1. Pre-flight checks:
   - Current branch: git branch --show-current
   - Commits ahead: git log $ARGUMENTS..HEAD --oneline
   - Changes summary: git diff $ARGUMENTS...HEAD --stat

2. Code quality:
   - Run full test suite
   - Run linter
   - Check test coverage
   - Verify no console.logs or debugger

3. Review changes:
   - List all modified files
   - For each file, summarize changes
   - Identify breaking changes
   - Note new dependencies

4. Generate PR description:

   **Summary:**
   - What was changed and why
   - Related issues (Closes #X)

   **Changes:**
   - Bulleted list of key changes

   **Testing:**
   - How to test these changes
   - New tests added

   **Screenshots/Videos:**
   - For UI changes (placeholder if applicable)

   **Checklist:**
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] No breaking changes (or documented)
   - [ ] Changelog updated (if applicable)

5. Push and create PR:
   - Push branch: git push -u origin branch-name
   - Create PR: gh pr create with generated description
   - Add labels based on changes
   - Request reviewers
   - Link to project board if applicable

6. Post-creation:
   - Monitor CI/CD status
   - Address review comments
   - Keep PR updated with main

Summary: PR #X created and ready for review
```

### Customization Options
- Custom PR templates
- Automated screenshot capture
- Integration with project management
- Reviewer assignment rules
- Label automation
- Changelog generation
- Release notes integration

---

## Morning Routine

### Use Case
Daily project setup and status check.

### When to Use
- Start of work day
- Context switching between projects
- Weekly project check-in
- Personal productivity

### Template

```markdown
---
description: Daily project setup and status check
allowed-tools: Bash(git:*), Bash(gh:*), Read
---

Morning routine:

1. Git status:
   - Current branch
   - Pull latest: git pull origin main
   - Any conflicts to resolve?
   - Uncommitted changes?

2. Project health:
   - Run quick test: npm run test:quick (if available)
   - Check build status: npm run build (if fast)
   - Review dependencies for security alerts

3. PRs and reviews:
   - PRs assigned to you: gh pr list --assignee @me
   - PRs waiting for your review: gh search prs --review-requested=@me
   - Status of your open PRs: gh pr list --author @me

4. Issues:
   - Assigned issues: gh issue list --assignee @me
   - Recent activity: gh issue list --updated-since=24h
   - High priority issues: gh issue list --label priority:high

5. Notifications:
   - Recent mentions: gh api notifications
   - Team activity since yesterday

6. Today's focus:
   - Based on above, suggest priorities
   - Blocking issues
   - Urgent reviews
   - In-progress work to continue

Summary: What needs attention today?
```

### Customization Options
- Include calendar integration
- Add time tracking
- Custom priority rules
- Team-specific checks
- Project-specific health checks
- Integration with task management
- Slack/Discord notifications

---

## Component Creation

### Use Case
Create new component with all boilerplate, tests, and documentation.

### When to Use
- Adding new UI components
- Following component standards
- Ensuring complete setup
- Team consistency

### Template

```markdown
---
description: Create new component with tests and docs
argument-hint: [ComponentName]
allowed-tools: Write, Edit, Read, Glob, Grep
---

Create component: $ARGUMENTS

1. Validate input:
   - Check ComponentName is PascalCase
   - Check component doesn't already exist
   - Identify component location from project structure

2. Determine component type:
   - Ask: Is this a page, layout, or reusable component?
   - Ask: Does it need state management?
   - Ask: Any specific props required?

3. Create component file:
   - Location: src/components/$ARGUMENTS/$ARGUMENTS.tsx
   - Template based on project standards (read existing components)
   - Include TypeScript interfaces for props
   - Add JSDoc comments
   - Include default export

4. Create test file:
   - Location: src/components/$ARGUMENTS/$ARGUMENTS.test.tsx
   - Basic render test
   - Props validation tests
   - User interaction tests if applicable
   - Mock any dependencies

5. Create story file (if Storybook used):
   - Location: src/components/$ARGUMENTS/$ARGUMENTS.stories.tsx
   - Default story
   - Variant stories for different props

6. Create styles (if needed):
   - CSS module or styled-components
   - Follow project styling approach
   - Include responsive styles

7. Create index file:
   - Location: src/components/$ARGUMENTS/index.ts
   - Export component and types

8. Update parent index:
   - Add to src/components/index.ts

9. Documentation:
   - Add README.md in component folder
   - Usage examples
   - Props documentation
   - Known issues/limitations

10. Verification:
    - Run tests: npm test $ARGUMENTS
    - Run type check
    - Verify imports work
    - Check Storybook if applicable

Summary:
- Files created
- Next steps (implement functionality)
- How to import and use
```

### Customization Options
- Framework-specific templates (React, Vue, Svelte)
- Custom file structure
- Accessibility templates
- Performance optimization patterns
- Integration with design system
- Automated screenshot generation

---

## Database Migration

### Use Case
Create and apply database migrations safely.

### When to Use
- Schema changes needed
- Adding new tables/columns
- Data transformations
- Database refactoring

### Template

```markdown
---
description: Create and apply database migration
argument-hint: [migration-description]
allowed-tools: Bash(npm:*), Bash(npx:*), Write, Read, Grep
---

Create migration: $ARGUMENTS

1. Understand change:
   - What schema changes are needed?
   - Is this additive or destructive?
   - Data migration needed?
   - Rollback strategy?

2. Check current schema:
   - Read latest migration files
   - Check current schema file
   - Identify affected tables

3. Generate migration:
   - Run migration generator: npx prisma migrate dev --name $ARGUMENTS
   - Or: npm run migrate:create -- $ARGUMENTS
   - Review generated SQL/migration file

4. Review migration:
   - Check SQL syntax
   - Verify indexes added appropriately
   - Check for data loss risks
   - Validate constraints
   - Review default values

5. Add data migration if needed:
   - Separate migration for data changes
   - Ensure idempotent
   - Handle edge cases

6. Write rollback migration:
   - Create down migration
   - Test rollback locally

7. Test migration:
   - Apply to local DB
   - Verify schema changes
   - Test application functionality
   - Check performance impact
   - Test rollback

8. Documentation:
   - Add migration notes
   - Document breaking changes
   - Update schema documentation
   - Add to changelog

9. Safety checks:
   - No dropping columns without deprecation
   - No data loss
   - Indexes for foreign keys
   - Performance considerations

Summary:
- Migration created: filename
- Changes: list schema changes
- Rollback: available/tested
- Breaking changes: yes/no
- Ready for: dev/staging/production
```

### Customization Options
- ORM-specific commands (Prisma, TypeORM, Sequelize)
- Custom migration validation
- Integration with schema management
- Deployment pipeline integration
- Multi-database support
- Data seeding

---

## Dependency Update

### Use Case
Safely update project dependencies with testing.

### When to Use
- Regular dependency maintenance
- Security vulnerability fixes
- Major version upgrades
- Keeping dependencies current

### Template

```markdown
---
description: Update dependencies safely with testing
argument-hint: [package-name or "all"]
allowed-tools: Bash(npm:*), Bash(pnpm:*), Read, Grep
---

Update dependencies: $ARGUMENTS

1. Check current state:
   - List outdated: npm outdated
   - Check for security issues: npm audit
   - Review package.json

2. Identify updates:
   - If specific package: focus on $ARGUMENTS
   - If "all": categorize by type (major/minor/patch)
   - Check breaking changes in changelogs

3. For each update:
   - Research breaking changes
   - Review migration guides
   - Check compatibility with other deps
   - Assess risk level

4. Update strategy:
   - Patch updates: safe to batch
   - Minor updates: group by category
   - Major updates: one at a time

5. Apply updates:
   - Update package.json
   - Run: npm install (or pnpm install)
   - Update lock file

6. Test thoroughly:
   - Run type check
   - Run full test suite
   - Run linter
   - Manual testing of affected features
   - Check build succeeds

7. Check for deprecation warnings:
   - Review console output
   - Check for breaking changes
   - Update code if needed

8. Update related files:
   - Update CI/CD configs if needed
   - Update documentation
   - Update lock file properly

9. Commit:
   - Message: "chore: update dependencies"
   - List updated packages in body
   - Note any breaking changes

10. Documentation:
    - Add to changelog
    - Note migration steps if needed
    - Update deployment notes

Summary:
- Packages updated: list
- Breaking changes: yes/no
- Tests: passing/failing
- Security fixes: yes/no
- Ready to merge: yes/no
```

### Customization Options
- Automated dependency updates
- Security-only updates
- Version pinning strategy
- Integration with Renovate/Dependabot
- Custom test suites per dependency
- Rollback procedures

---

## Security Audit

### Use Case
Comprehensive security review of codebase.

### When to Use
- Before major releases
- Security incident response
- Compliance requirements
- Regular security reviews

### Template

```markdown
---
description: Comprehensive security audit of codebase
allowed-tools: Bash(npm:*), Read, Grep, Glob
model: claude-opus-4-20250514
---

Security audit:

1. Dependency security:
   - Run: npm audit
   - Check for known vulnerabilities
   - Review outdated packages
   - Check for abandoned packages

2. Authentication & authorization:
   - Review auth implementation
   - Check session management
   - Verify access control
   - Test authentication bypass scenarios

3. Input validation:
   - Search for user input handling
   - Check for SQL injection risks
   - Check for XSS vulnerabilities
   - Verify input sanitization

4. Data protection:
   - Search for sensitive data handling
   - Check encryption usage
   - Verify secure storage
   - Check for data leaks in logs

5. API security:
   - Review API endpoints
   - Check rate limiting
   - Verify CORS configuration
   - Test for API abuse

6. Secret management:
   - Search for hardcoded secrets
   - Check .env files not committed
   - Verify environment variables
   - Review secret rotation

7. Code vulnerabilities:
   - Check for eval() usage
   - Review dynamic code execution
   - Check for path traversal
   - Review file upload handling

8. Dependencies analysis:
   - Review third-party code
   - Check for supply chain risks
   - Verify integrity checks
   - Review license compliance

9. Infrastructure:
   - Review Dockerfile security
   - Check for exposed ports
   - Review cloud configs
   - Check for least privilege

10. Security headers:
    - Check HTTP security headers
    - Verify CSP policies
    - Check for secure cookies

Report:
- Critical issues: list with severity
- High priority: needs immediate fix
- Medium priority: fix in next sprint
- Low priority: nice to have
- Recommendations: general security improvements
```

### Customization Options
- Custom security rules
- Compliance frameworks (OWASP, NIST)
- Integration with security scanners
- Automated vulnerability scanning
- Penetration testing checklist
- Security policy enforcement

---

## Performance Analysis

### Use Case
Analyze application performance and identify bottlenecks.

### When to Use
- Performance degradation
- Before optimization work
- Regular performance monitoring
- Production performance issues

### Template

```markdown
---
description: Analyze application performance
argument-hint: [@component or "full"]
allowed-tools: Bash(npm:*), Read, Grep, Glob
model: claude-3-7-sonnet-20250219
---

Performance analysis: $ARGUMENTS

1. Identify scope:
   - If @component: focus on specific component
   - If "full": analyze entire application
   - If nothing: ask user for focus area

2. Bundle size analysis:
   - Run build: npm run build
   - Analyze bundle: npx webpack-bundle-analyzer
   - Identify large dependencies
   - Check for code splitting opportunities

3. Runtime performance:
   - Search for performance anti-patterns:
     - Unnecessary re-renders
     - Missing memoization
     - Inefficient loops
     - Heavy computations in render
     - Memory leaks

4. Network performance:
   - Review API calls
   - Check for N+1 queries
   - Identify large payloads
   - Review caching strategy

5. Database performance (if applicable):
   - Review slow queries
   - Check for missing indexes
   - Identify inefficient queries
   - Review connection pooling

6. Asset optimization:
   - Check image sizes
   - Review font loading
   - Check CSS size
   - Review static asset caching

7. Code-level optimization:
   - Search for: Array methods in loops
   - Check for: Expensive operations
   - Review: State management efficiency
   - Identify: Redundant calculations

8. Profiling recommendations:
   - Areas needing React Profiler
   - Backend endpoints to profile
   - Database queries to analyze
   - Memory usage to monitor

9. Quick wins:
   - Easy optimizations to implement now
   - Configuration changes
   - Dependency updates
   - Simple code refactors

10. Long-term improvements:
    - Architectural changes needed
    - Major refactoring opportunities
    - Infrastructure improvements
    - Monitoring to implement

Report:
- Current performance metrics
- Top bottlenecks
- Quick wins (< 1 hour)
- Medium effort (1-3 days)
- Large projects (> 1 week)
- Recommended priorities
```

### Customization Options
- Framework-specific analysis (React, Vue, Angular)
- Custom performance budgets
- Integration with monitoring tools
- Automated performance testing
- Lighthouse integration
- Custom performance metrics

---

## Usage Tips

### Combining Templates

Templates can be combined for complex workflows:

```markdown
---
description: Complete feature workflow
argument-hint: [feature-name]
---

Implement feature: $ARGUMENTS

1. Use /fix-issue workflow for implementation
2. Use /pre-commit for validation
3. Use /review-pr for self-review
4. Use /pr-preparation for PR creation
```

### Customizing for Your Project

1. Copy template to your `.claude/commands/`
2. Adjust steps for your workflow
3. Update tool permissions for your stack
4. Add project-specific checks
5. Test and iterate

### Template Maintenance

- Review templates quarterly
- Update based on team feedback
- Remove unused steps
- Add new patterns discovered
- Keep documentation current

---

## Contributing Templates

Have a useful template? Consider:
- Generalizing for wider use
- Adding clear documentation
- Testing with different scenarios
- Sharing with team
- Contributing to community
