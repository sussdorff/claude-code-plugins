# Common Command Patterns

Proven workflow patterns for slash commands. Each pattern includes use case, when to use, template, customization points, and variations.

## Table of Contents

1. [Morning Routine Pattern](#morning-routine-pattern)
2. [Pre-Commit Validation Pattern](#pre-commit-validation-pattern)
3. [PR Preparation Pattern](#pr-preparation-pattern)
4. [Quick Fix Workflow Pattern](#quick-fix-workflow-pattern)
5. [Feature Development Pattern](#feature-development-pattern)
6. [Release Preparation Pattern](#release-preparation-pattern)
7. [Incident Response Pattern](#incident-response-pattern)
8. [Code Quality Check Pattern](#code-quality-check-pattern)
9. [Dependency Update Pattern](#dependency-update-pattern)
10. [Documentation Sync Pattern](#documentation-sync-pattern)

---

## Morning Routine Pattern

### Use Case
Start workday with project context, status checks, and priorities.

### When to Use
- Daily at work start
- After long breaks
- Context switching between projects
- Weekly planning

### Pattern Template

```markdown
---
description: Daily project setup and priorities
allowed-tools: Bash(git:*), Bash(gh:*), Read
---

Morning routine:

1. Environment check:
   - Current branch and status
   - Sync with remote: git pull
   - Check for conflicts

2. Health verification:
   - Quick build check (if fast)
   - Dependency security alerts
   - CI/CD status

3. Work items review:
   - Assigned PRs: gh pr list --assignee @me
   - Review requests: gh search prs --review-requested=@me
   - Assigned issues: gh issue list --assignee @me
   - Blocked items

4. Recent activity:
   - Team updates since yesterday
   - High priority issues
   - Production incidents

5. Today's priorities:
   - Based on above, suggest focus areas
   - Urgent items
   - Blocking items
   - Planned work

Summary: Actionable priorities for today
```

### Customization Points

**Time Range:**
```markdown
# Last 24 hours
--updated-since=24h

# Since last Friday (for Monday)
--updated-since=72h

# Last work day
--updated-since=$(date -d 'last weekday' +%Y-%m-%d)
```

**Team-Specific Checks:**
```markdown
3. Team context:
   - Standup notes in docs/standups/
   - Team calendar for today
   - On-call rotation status
```

**Project-Specific Health:**
```markdown
2. Health checks:
   - Check Kubernetes deployments
   - Verify database migrations
   - Check monitoring dashboards
   - Review error rates
```

### Variations

**Minimal Morning Routine:**
```markdown
---
description: Quick morning check
model: claude-3-5-haiku-20241022
---

Quick check:
1. git pull
2. My PRs: gh pr list --author @me
3. My issues: gh issue list --assignee @me
4. Summary of what needs attention
```

**Comprehensive Morning Routine:**
```markdown
---
description: Comprehensive daily startup
---

Extended morning routine:
1. Environment setup (git, dependencies)
2. Health checks (tests, builds, services)
3. Work items (PRs, issues, reviews)
4. Team sync (standups, updates, blockers)
5. Planning (priorities, estimates, dependencies)
6. Tools check (gh auth, aws credentials, vpn)
7. Documentation review (recent changes to docs)
8. Personal notes (what was I working on?)

Detailed summary with action items
```

**Weekly Planning Routine:**
```markdown
---
description: Weekly planning and review
---

Weekly planning:
1. Last week review:
   - PRs merged: gh pr list --state merged --author @me --created last-week
   - Issues closed: gh issue list --state closed --assignee @me --created last-week
   - Accomplishments summary

2. This week planning:
   - Open PRs to finish
   - Assigned issues
   - Upcoming deadlines
   - Team dependencies

3. Sprint planning:
   - Review sprint goals
   - Capacity planning
   - Risk assessment
```

---

## Pre-Commit Validation Pattern

### Use Case
Validate all changes before committing to ensure quality and standards.

### When to Use
- Before every commit
- As git pre-commit hook
- Before creating PRs
- Team quality gates

### Pattern Template

```markdown
---
description: Validate changes before committing
allowed-tools: Bash(git:*), Bash(npm:*), Read, Grep
model: claude-3-5-haiku-20241022
---

Pre-commit validation:

1. Show changes:
   - Staged files: git diff --cached --name-only
   - Changes summary: git diff --cached --stat

2. Automated checks:
   - Type check: npm run type:check
   - Linter: npm run lint
   - Format check: npm run format:check
   - Tests: npm test -- --findRelatedTests

3. Code quality:
   - No console.log in staged files
   - No debugger statements
   - No TODO without issue numbers
   - No commented code blocks

4. Security checks:
   - No hardcoded secrets
   - No .env files staged
   - No sensitive data in logs
   - No API keys in code

5. Results:
   ✅ All checks passed - safe to commit
   ❌ Issues found - must fix:
      - List blocking issues
      - List warnings
```

### Customization Points

**Project-Specific Checks:**
```markdown
3. Project standards:
   - Check Dockerfile best practices
   - Verify API versioning
   - Check database migration files
   - Validate GraphQL schema
```

**Performance Checks:**
```markdown
4. Performance validation:
   - Check bundle size impact
   - Verify no large files added
   - Check for performance anti-patterns
   - Validate query efficiency
```

**Documentation Checks:**
```markdown
5. Documentation:
   - Public APIs have JSDoc
   - README updated if needed
   - CHANGELOG updated for features/fixes
   - Migration guide for breaking changes
```

### Variations

**Fast Pre-Commit (< 30 seconds):**
```markdown
---
description: Quick pre-commit validation
model: claude-3-5-haiku-20241022
---

Fast validation:
1. Show staged changes
2. Lint only staged files
3. Type check only if TypeScript changed
4. No console.log or debugger
5. Quick summary: ✅/❌
```

**Comprehensive Pre-Commit:**
```markdown
---
description: Thorough pre-commit validation
---

Thorough validation:
1. All automated checks
2. Full test suite
3. Code quality analysis
4. Security scan
5. Documentation check
6. Performance impact
7. Breaking changes detection
8. Detailed report with recommendations
```

**Language-Specific Checks:**
```markdown
# For Python
2. Python checks:
   - Black formatting
   - Flake8 linting
   - MyPy type checking
   - Pytest for changed files

# For Go
2. Go checks:
   - gofmt
   - golint
   - go vet
   - go test -race
```

---

## PR Preparation Pattern

### Use Case
Prepare comprehensive pull request with all necessary information.

### When to Use
- Ready to create PR
- Ensuring PR quality
- Team PR standards
- Complete documentation

### Pattern Template

```markdown
---
description: Prepare comprehensive pull request
argument-hint: [base-branch]
allowed-tools: Bash(gh:*), Bash(git:*), Read, Grep, Glob
---

Prepare PR to $ARGUMENTS:

1. Pre-flight:
   - Current branch: git branch --show-current
   - Commits: git log $ARGUMENTS..HEAD --oneline
   - Changes: git diff $ARGUMENTS...HEAD --stat

2. Quality checks:
   - Run tests
   - Run linter
   - Check coverage
   - Verify no debug code

3. Analyze changes:
   - List modified files
   - Summarize changes per file
   - Identify breaking changes
   - Note new dependencies

4. Generate PR description:

   ## Summary
   [What changed and why]

   ## Changes
   - [Key change 1]
   - [Key change 2]

   ## Testing
   - [How to test]
   - [Tests added]

   ## Screenshots
   [If UI changes]

   ## Checklist
   - [ ] Tests added/updated
   - [ ] Docs updated
   - [ ] No breaking changes

5. Create PR:
   - Push: git push -u origin branch
   - Create: gh pr create
   - Add labels
   - Request reviewers

6. Post-creation:
   - Monitor CI
   - Link to project board
   - Summary with PR URL
```

### Customization Points

**PR Templates:**
```markdown
4. Use project PR template:
   - Read .github/pull_request_template.md
   - Fill in all sections
   - Add project-specific sections
```

**Visual Changes:**
```markdown
4. For UI changes:
   - Take before/after screenshots
   - Record demo video
   - Test responsive design
   - Check accessibility
```

**Release Notes:**
```markdown
4. Update release notes:
   - Add to CHANGELOG.md
   - Categorize: feature/fix/breaking
   - Include migration guide if needed
```

### Variations

**Quick PR (Internal):**
```markdown
---
description: Quick PR for small changes
---

Quick PR:
1. Show changes: git diff origin/main...HEAD --stat
2. Run tests
3. Create PR with basic description
4. Auto-add reviewers from CODEOWNERS
```

**Formal PR (External/Release):**
```markdown
---
description: Formal PR with full documentation
---

Formal PR:
1. Comprehensive quality checks
2. Full documentation update
3. Changelog entry
4. Breaking changes analysis
5. Migration guide if needed
6. Security considerations
7. Performance impact analysis
8. Detailed test plan
```

---

## Quick Fix Workflow Pattern

### Use Case
Rapidly fix small bugs or issues with minimal overhead.

### When to Use
- Small, isolated bugs
- Quick improvements
- Hotfixes
- Typos and minor issues

### Pattern Template

```markdown
---
description: Quick fix for small issues
argument-hint: [description]
allowed-tools: Bash(git:*), Edit, Read, Grep
model: claude-3-5-haiku-20241022
---

Quick fix: $ARGUMENTS

1. Identify issue:
   - Search for problem: grep -r "$ARGUMENTS"
   - Locate affected files
   - Understand context

2. Implement fix:
   - Make minimal change
   - Follow existing patterns
   - No refactoring (stay focused)

3. Quick test:
   - Verify fix works
   - No new errors introduced
   - Basic smoke test

4. Commit:
   - git add [files]
   - Commit: "fix: $ARGUMENTS"
   - Push to current branch

Done: Fix applied and pushed
```

### Customization Points

**With Test:**
```markdown
2. Implement fix:
   - Add failing test first
   - Implement fix
   - Verify test passes
```

**With Review:**
```markdown
4. Create PR:
   - Push to new branch: fix/[description]
   - Create PR for team review
   - Link related issue
```

**Hotfix Process:**
```markdown
1. Hotfix setup:
   - Create from production branch
   - Name: hotfix/[issue]

5. Hotfix deployment:
   - Deploy to production
   - Notify team
   - Monitor for issues
```

### Variations

**Typo Fix:**
```markdown
---
description: Fix typos in code or docs
argument-hint: [file-pattern]
---

Fix typos in $ARGUMENTS:
1. Search files matching pattern
2. Fix spelling errors
3. Commit: "fix: correct typos in $ARGUMENTS"
```

**Config Update:**
```markdown
---
description: Update configuration
argument-hint: [config-name] [new-value]
---

Update config $1 to $2:
1. Locate config file
2. Update value safely
3. Validate config format
4. Commit: "config: update $1 to $2"
```

---

## Feature Development Pattern

### Use Case
Structured workflow for developing new features from start to finish.

### When to Use
- New feature implementation
- Following TDD approach
- Team feature development
- Complex features requiring planning

### Pattern Template

```markdown
---
description: Develop new feature following standards
argument-hint: [feature-name]
allowed-tools: Bash(git:*), Edit, Read, Write, Grep, Glob
---

Develop feature: $ARGUMENTS

1. Planning:
   - Review feature requirements
   - Identify affected components
   - List files to create/modify
   - Plan test strategy

2. Branch setup:
   - Create branch: feature/$ARGUMENTS
   - Ensure clean state
   - Pull latest main

3. Design phase:
   - Sketch component structure
   - Plan data flow
   - Identify dependencies
   - Consider edge cases

4. Test-first development:
   - Write failing tests for feature
   - Define interfaces/types
   - Document expected behavior

5. Implementation:
   - Implement core functionality
   - Follow coding standards
   - Add inline documentation
   - Handle errors gracefully

6. Testing:
   - Run tests: watch them pass
   - Add integration tests
   - Manual testing
   - Edge case verification

7. Documentation:
   - Update README if needed
   - Add usage examples
   - Document API if public
   - Add to CHANGELOG

8. Review:
   - Self-review changes
   - Run full test suite
   - Check test coverage
   - Review for improvements

9. Commit and PR:
   - Commit: "feat: add $ARGUMENTS"
   - Push and create PR
   - Link to requirements
   - Request review

Summary: Feature complete and ready for review
```

### Customization Points

**Agile Integration:**
```markdown
1. Ticket integration:
   - Fetch ticket: jira view PROJ-123
   - Extract acceptance criteria
   - Update ticket status: In Progress
```

**Design Review:**
```markdown
3. Design review:
   - Document design decisions
   - Get architecture review
   - Consider alternatives
   - Plan for scale
```

**Performance Planning:**
```markdown
4. Performance considerations:
   - Identify performance requirements
   - Plan for optimization
   - Add performance tests
   - Monitor resource usage
```

### Variations

**Spike/Exploration:**
```markdown
---
description: Explore technical approach for feature
---

Technical spike: $ARGUMENTS
1. Research approaches
2. Prototype solutions
3. Compare trade-offs
4. Document findings
5. Recommend approach
6. Discard spike branch
```

**Feature Flag Pattern:**
```markdown
---
description: Develop feature behind feature flag
---

Feature with flag: $ARGUMENTS
1. Add feature flag to config
2. Implement feature conditionally
3. Add flag documentation
4. Test with flag on/off
5. Plan rollout strategy
```

---

## Release Preparation Pattern

### Use Case
Prepare software release with all necessary checks and documentation.

### When to Use
- Version releases
- Production deployments
- Library publishing
- Release cadence (weekly, monthly)

### Pattern Template

```markdown
---
description: Prepare release with version bump
argument-hint: [version: major|minor|patch]
allowed-tools: Bash(git:*), Bash(npm:*), Edit, Read, Grep
---

Prepare release: $ARGUMENTS

1. Pre-release verification:
   - On main/master branch
   - All tests passing
   - No uncommitted changes
   - Up to date with remote

2. Version bump:
   - Update package.json version ($ARGUMENTS)
   - Update version in other files
   - Follow semver guidelines

3. Changelog:
   - Generate from commits
   - Categorize: Features, Fixes, Breaking
   - Add migration guide if needed
   - Review for clarity

4. Quality checks:
   - Run full test suite
   - Run linter
   - Check types
   - Build production bundle
   - Verify bundle size

5. Documentation:
   - Update README for new features
   - Update API documentation
   - Add upgrade guide
   - Review examples

6. Git tagging:
   - Commit: "chore: release v$VERSION"
   - Tag: git tag -a v$VERSION
   - Add release notes to tag

7. Pre-publish checks:
   - Test installation in fresh project
   - Verify exports work
   - Check for bundled dev dependencies
   - Security audit

8. Release:
   - Push: git push && git push --tags
   - Publish: npm publish (if package)
   - Create GitHub release: gh release create
   - Deploy if applicable

9. Post-release:
   - Announce to team
   - Update documentation site
   - Monitor for issues
   - Prepare hotfix plan

Summary: Version $VERSION released
```

### Customization Points

**Automated Testing:**
```markdown
4. Comprehensive testing:
   - Unit tests
   - Integration tests
   - E2E tests
   - Performance benchmarks
   - Security scan
   - Compatibility tests
```

**Multi-Environment:**
```markdown
8. Staged rollout:
   - Deploy to staging
   - Smoke tests in staging
   - Deploy to production
   - Monitor metrics
   - Rollback plan ready
```

**Notification:**
```markdown
9. Notifications:
   - Post to Slack/Discord
   - Email stakeholders
   - Update status page
   - Tweet announcement
```

### Variations

**Hotfix Release:**
```markdown
---
description: Emergency hotfix release
---

Hotfix release:
1. Create from production tag
2. Apply minimal fix
3. Test thoroughly
4. Patch version bump
5. Fast-track deployment
6. Monitor closely
```

**Beta Release:**
```markdown
---
description: Beta/pre-release
---

Beta release:
1. Version: X.Y.Z-beta.N
2. Tag as pre-release
3. Publish with beta tag
4. Limited announcement
5. Gather feedback
```

---

## Incident Response Pattern

### Use Case
Systematic approach to handling production incidents and outages.

### When to Use
- Production issues
- Service degradation
- Security incidents
- Customer-impacting problems

### Pattern Template

```markdown
---
description: Respond to production incident
argument-hint: [incident-description]
allowed-tools: Bash(git:*), Bash(gh:*), Read, Grep
model: claude-3-7-sonnet-20250219
---

Incident response: $ARGUMENTS

1. Triage:
   - Severity: critical/high/medium/low
   - Impact: users affected, features down
   - Started: when did it begin?
   - Current status

2. Immediate actions:
   - Alert team if critical
   - Update status page
   - Create incident ticket
   - Start incident log

3. Investigation:
   - Check recent deployments
   - Review error logs
   - Check system metrics
   - Identify error patterns
   - Review recent changes

4. Gather context:
   - Related PRs merged recently
   - Recent configuration changes
   - Infrastructure changes
   - Third-party service status

5. Hypothesis:
   - Likely cause based on evidence
   - Alternative explanations
   - How to verify hypothesis

6. Mitigation:
   - Immediate fix or rollback?
   - Workaround available?
   - Implement mitigation
   - Verify issue resolved

7. Monitoring:
   - Confirm metrics improved
   - Check error rates
   - Verify functionality restored
   - Monitor for recurrence

8. Communication:
   - Update team on resolution
   - Update status page
   - Notify affected users
   - Update incident ticket

9. Post-incident:
   - Document timeline
   - Schedule post-mortem
   - Identify preventive measures
   - Create follow-up tasks

Incident status: [resolved/mitigated/ongoing]
```

### Customization Points

**On-Call Integration:**
```markdown
1. On-call response:
   - Page on-call engineer
   - Check runbook: docs/runbooks/$INCIDENT
   - Follow escalation procedure
```

**Customer Communication:**
```markdown
8. Customer communication:
   - Draft customer notice
   - Get approval from lead
   - Send via support channel
   - Offer compensation if SLA breach
```

**Automated Remediation:**
```markdown
6. Auto-remediation attempts:
   - Restart affected services
   - Clear caches
   - Scale up resources
   - Failover to backup
```

### Variations

**Security Incident:**
```markdown
---
description: Security incident response
---

Security incident:
1. Isolate affected systems
2. Preserve evidence
3. Assess breach scope
4. Notify security team
5. Follow security protocol
6. Implement fixes
7. Audit for similar issues
8. Post-incident security review
```

**Performance Degradation:**
```markdown
---
description: Performance issue investigation
---

Performance issue:
1. Identify slow operations
2. Check resource utilization
3. Review recent changes
4. Profile application
5. Optimize bottlenecks
6. Deploy optimization
7. Monitor improvements
```

---

## Code Quality Check Pattern

### Use Case
Comprehensive code quality analysis beyond basic linting.

### When to Use
- Before major releases
- Regular code audits
- Refactoring planning
- Technical debt assessment

### Pattern Template

```markdown
---
description: Comprehensive code quality analysis
argument-hint: [@path or "all"]
allowed-tools: Read, Grep, Glob, Bash(npm:*)
---

Code quality check: $ARGUMENTS

1. Scope definition:
   - If @path: focus on specified path
   - If "all": analyze entire codebase
   - Identify file types and count

2. Static analysis:
   - Run linter with all rules
   - Type checker in strict mode
   - Complexity analysis
   - Unused code detection

3. Code patterns:
   - Duplicated code
   - Long functions (> 50 lines)
   - Complex functions (cyclomatic complexity)
   - Large files (> 300 lines)

4. Best practices:
   - Error handling consistency
   - Logging patterns
   - Naming conventions
   - Code organization

5. Testing:
   - Test coverage by file
   - Untested critical paths
   - Test quality (assertions, mocking)
   - Missing edge case tests

6. Documentation:
   - Functions without docs
   - Complex code without comments
   - Outdated documentation
   - Missing README sections

7. Dependencies:
   - Unused dependencies
   - Outdated packages
   - Security vulnerabilities
   - License compatibility

8. Performance:
   - Inefficient algorithms
   - Memory leaks potential
   - Expensive operations
   - Missing optimizations

9. Security:
   - Input validation gaps
   - Authentication issues
   - Hardcoded secrets search
   - Insecure patterns

10. Report:
    - Overall score
    - Critical issues
    - High priority improvements
    - Technical debt estimation
    - Refactoring recommendations

Summary: Code quality score and action items
```

### Customization Points

**Automated Tools:**
```markdown
2. Run quality tools:
   - ESLint/TSLint
   - SonarQube
   - CodeClimate
   - Complexity report
```

**Framework-Specific:**
```markdown
4. React best practices:
   - Component size
   - Hook usage
   - Prop drilling depth
   - Re-render optimization
```

**Custom Rules:**
```markdown
5. Project conventions:
   - Check custom patterns
   - Verify architecture rules
   - Validate file structure
   - Check naming conventions
```

### Variations

**Quick Quality Check:**
```markdown
---
description: Fast code quality scan
model: claude-3-5-haiku-20241022
---

Quick quality check:
1. Run linter
2. Check test coverage
3. Find TODOs and FIXMEs
4. Quick summary
```

**Deep Quality Audit:**
```markdown
---
description: Thorough code quality audit
model: claude-opus-4-20250514
---

Deep audit:
1. All standard checks
2. Architecture analysis
3. Design pattern review
4. Scalability assessment
5. Maintainability analysis
6. Team feedback integration
7. Detailed improvement roadmap
```

---

## Dependency Update Pattern

### Use Case
Safely update project dependencies with proper testing.

### When to Use
- Regular maintenance (weekly/monthly)
- Security updates
- Major version upgrades
- Dependency modernization

### Pattern Template

```markdown
---
description: Update dependencies safely
argument-hint: [package-name or "all" or "security"]
allowed-tools: Bash(npm:*), Read, Grep
---

Update dependencies: $ARGUMENTS

1. Current state:
   - List outdated: npm outdated
   - Security issues: npm audit
   - Current versions in package.json

2. Categorize updates:
   - If "security": security fixes only
   - If "all": categorize major/minor/patch
   - If package name: focus on specific package

3. Research changes:
   - For each update, check:
     - Changelog/release notes
     - Breaking changes
     - Migration guides
     - Known issues

4. Update strategy:
   - Patch: batch together (low risk)
   - Minor: group by category
   - Major: one at a time (high risk)
   - Security: prioritize, may need major update

5. Apply updates:
   - Update package.json
   - Run: npm install (or npm update)
   - Update lock file
   - Check for peer dependency warnings

6. Code changes:
   - Apply breaking change migrations
   - Update deprecated API usage
   - Fix type errors
   - Update tests

7. Testing:
   - Run type check
   - Run full test suite
   - Run linter
   - Manual testing of critical paths
   - Check build succeeds

8. Verification:
   - No deprecation warnings
   - No security vulnerabilities
   - All tests pass
   - Application works correctly

9. Documentation:
   - Update README if needed
   - Document breaking changes
   - Add to CHANGELOG
   - Note migration steps

10. Commit:
    - Message: "chore: update dependencies"
    - List updated packages
    - Note if security fixes included

Summary:
- Updated: [list packages]
- Security fixes: yes/no
- Breaking changes: yes/no
- Tests: passing
```

### Customization Points

**Automated Updates:**
```markdown
1. Check for automated PRs:
   - Review Dependabot PRs
   - Review Renovate PRs
   - Batch compatible updates
```

**Monorepo Updates:**
```markdown
5. Monorepo coordination:
   - Update all workspaces
   - Align shared dependencies
   - Update root dependencies
   - Test all packages
```

**Version Pinning:**
```markdown
5. Version strategy:
   - Pin exact versions for stability
   - Use ranges for flexibility
   - Lock critical dependencies
```

### Variations

**Security-Only Update:**
```markdown
---
description: Apply security updates only
---

Security updates:
1. Run: npm audit
2. Apply: npm audit fix
3. Manual updates for high severity
4. Test critical paths
5. Deploy urgently if needed
```

**Major Version Upgrade:**
```markdown
---
description: Upgrade major version
argument-hint: [package-name]
---

Major upgrade: $1
1. Read migration guide
2. Update in isolation
3. Apply all breaking changes
4. Comprehensive testing
5. Phased rollout if possible
```

---

## Documentation Sync Pattern

### Use Case
Keep documentation synchronized with code changes.

### When to Use
- After feature implementation
- Before releases
- Regular doc maintenance
- API changes

### Pattern Template

```markdown
---
description: Sync documentation with code
argument-hint: [@files or "all"]
allowed-tools: Read, Edit, Grep, Glob
---

Documentation sync for: $ARGUMENTS

1. Identify scope:
   - If @files: docs for specific files
   - If "all": full documentation review
   - Find related documentation

2. Code analysis:
   - Read source code
   - Identify public APIs
   - Extract function signatures
   - Note parameters and return types

3. Documentation comparison:
   - Compare code with docs
   - Find outdated information
   - Find missing documentation
   - Find deprecated features

4. Update documentation:
   - Sync API documentation
   - Update examples with new syntax
   - Add new features
   - Mark deprecated features
   - Fix inaccuracies

5. Examples validation:
   - Test code examples
   - Update for API changes
   - Add missing examples
   - Remove outdated examples

6. README updates:
   - Installation instructions
   - Quick start guide
   - Feature list
   - Configuration options

7. Inline documentation:
   - JSDoc/TSDoc comments
   - Parameter descriptions
   - Return type documentation
   - Usage examples in code

8. Additional docs:
   - Update CHANGELOG
   - Update migration guides
   - Update troubleshooting
   - Update FAQ

9. Cross-references:
   - Fix broken links
   - Update references
   - Add new cross-refs
   - Remove outdated links

10. Verification:
    - All examples work
    - Links are valid
    - Formatting correct
    - Spelling/grammar check

Summary: Documentation updated and verified
```

### Customization Points

**API Documentation:**
```markdown
3. API doc generation:
   - Generate from TypeScript types
   - Use JSDoc to generate docs
   - Update OpenAPI spec
   - Generate client SDKs
```

**Versioned Docs:**
```markdown
4. Version management:
   - Update docs for current version
   - Archive old version docs
   - Add version switcher
   - Note version differences
```

**Interactive Docs:**
```markdown
5. Interactive elements:
   - Add code playgrounds
   - Include live demos
   - Add interactive tutorials
   - Update Storybook stories
```

### Variations

**Quick Doc Update:**
```markdown
---
description: Quick documentation fix
argument-hint: [topic]
---

Quick doc update: $ARGUMENTS
1. Find relevant docs
2. Make specific update
3. Verify examples still work
4. Commit: "docs: update $ARGUMENTS"
```

**Comprehensive Doc Review:**
```markdown
---
description: Full documentation audit
---

Full doc review:
1. Review all documentation
2. Test all examples
3. Update for latest changes
4. Improve clarity
5. Add missing sections
6. Reorganize if needed
7. Professional edit pass
```

---

## Pattern Composition

### Combining Patterns

Patterns can be combined for complex workflows:

```markdown
---
description: Complete feature workflow
---

Full feature cycle:
1. Use Feature Development Pattern for implementation
2. Use Code Quality Check Pattern for review
3. Use Pre-Commit Validation Pattern before committing
4. Use PR Preparation Pattern for PR creation
5. Use Documentation Sync Pattern for docs
```

### Pattern Selection Guide

| Frequency | Pattern | Model |
|-----------|---------|-------|
| Daily | Morning Routine | Haiku |
| Per commit | Pre-Commit Validation | Haiku |
| Per PR | PR Preparation | Sonnet |
| Per feature | Feature Development | Sonnet |
| Per release | Release Preparation | Sonnet |
| As needed | Incident Response | Sonnet/Opus |
| Weekly | Code Quality Check | Sonnet |
| Monthly | Dependency Update | Sonnet |
| As needed | Documentation Sync | Haiku/Sonnet |

---

## Customizing Patterns for Your Team

1. **Start with base pattern**
2. **Add project-specific steps**
3. **Adjust tool permissions**
4. **Configure for your stack**
5. **Test with team**
6. **Gather feedback**
7. **Iterate and improve**

Remember: These patterns are starting points. Adapt them to your team's workflow, tech stack, and requirements.
