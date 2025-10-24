# Advanced Command Features

Advanced capabilities for creating sophisticated slash commands. Includes syntax, examples, use cases, and best practices for each feature.

## Table of Contents

1. [Bash Command Execution](#bash-command-execution)
2. [File References](#file-references)
3. [Conditional Logic](#conditional-logic)
4. [Context from Claude](#context-from-claude)
5. [Parameter Defaults and Validation](#parameter-defaults-and-validation)
6. [Sub-steps and Grouping](#sub-steps-and-grouping)
7. [Multi-command Workflows](#multi-command-workflows)
8. [Environment Detection](#environment-detection)
9. [Dynamic Tool Selection](#dynamic-tool-selection)
10. [State Management](#state-management)

---

## Bash Command Execution

### Overview
Commands can instruct Claude to execute bash commands, capture output, and use results in subsequent steps.

### Basic Syntax

```markdown
1. Execute command:
   - Run: git status
   - Capture output
   - Use in next steps
```

### Explicit vs Implicit Execution

**Explicit (Recommended):**
```markdown
1. Check git status:
   - Execute: git status --short
   - Parse output for staged files
   - Count modified files

2. Based on status from step 1:
   - If no changes: exit with message
   - If changes: proceed to commit
```

**Implicit:**
```markdown
1. Check git status and if there are changes, commit them
```

**Best Practice:** Use explicit instructions for complex operations.

---

### Capturing and Using Output

**Example:**
```markdown
1. Get current branch:
   - Run: git branch --show-current
   - Store branch name
   - Use in subsequent steps

2. Create PR to main from {branch-name}:
   - Run: gh pr create --base main --head {branch-from-step-1}
```

---

### Error Handling in Bash Commands

```markdown
1. Run tests:
   - Execute: npm test
   - Capture exit code
   - Capture output (stdout and stderr)

2. Handle test results:
   - If exit code is 0 (success):
     - Show success message
     - Proceed to next step
   - If exit code is non-zero (failure):
     - Show failed tests from output
     - Stop workflow
     - Provide remediation steps
```

---

### Complex Bash Pipelines

**Simple pipeline:**
```markdown
1. Find large files:
   - Run: find . -type f -size +1M | sort -h
   - List files over 1MB, sorted by size
```

**With processing:**
```markdown
1. Analyze log errors:
   - Run: tail -1000 app.log | grep ERROR | cut -d' ' -f3 | sort | uniq -c | sort -rn
   - Extract: unique error types with counts
   - Display: top 10 most frequent errors
```

---

### Tool Permission for Bash

**Specific commands:**
```yaml
---
allowed-tools: Bash(git:*), Bash(npm test:*)
---
```

**Pattern matching:**
```yaml
# Matches: npm run anything
allowed-tools: Bash(npm run:*)

# Matches: all git commands
allowed-tools: Bash(git:*)

# Matches: specific git commands
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*)
```

---

### Use Cases

**CI/CD Validation:**
```markdown
1. Pre-flight checks:
   - Check Docker: docker --version
   - Check kubectl: kubectl version --client
   - Verify AWS credentials: aws sts get-caller-identity

2. Only if all checks pass:
   - Proceed with deployment
```

**Code Analysis:**
```markdown
1. Complexity analysis:
   - Run: npx complexity-report src/
   - Parse output
   - Identify high complexity functions

2. Report findings:
   - List functions over complexity threshold
   - Suggest refactoring targets
```

**Performance Testing:**
```markdown
1. Benchmark operation:
   - Run: time npm run build
   - Capture execution time
   - Compare to baseline (< 30s)

2. Performance report:
   - Current: X seconds
   - Baseline: Y seconds
   - Status: pass/fail
```

---

## File References

### Overview
Commands can accept file paths as arguments using `@file` syntax.

### Basic Syntax

**In command definition:**
```markdown
---
description: Optimize specified files
---

Optimize files: $ARGUMENTS

1. For each file in $ARGUMENTS:
   - Read file content
   - Analyze for optimization opportunities
   - Apply optimizations
   - Save changes
```

**Invocation:**
```bash
/optimize @src/utils/helper.ts
/optimize @src/utils/helper.ts @src/lib/api.ts
```

---

### Single File Operations

```markdown
---
description: Refactor component
---

Refactor component: $ARGUMENTS

1. Read file: $ARGUMENTS
2. Identify refactoring opportunities:
   - Long functions
   - Duplicated code
   - Complex logic
3. Refactor following best practices
4. Update file
5. Run tests to verify
```

**Usage:**
```bash
/refactor @src/components/LargeComponent.tsx
```

---

### Multiple File Operations

```markdown
---
description: Add type annotations to files
---

Add types to: $ARGUMENTS

1. For each file in $ARGUMENTS:
   - Read file
   - Identify untyped variables
   - Add appropriate type annotations
   - Maintain code style
   - Save changes

2. Verify all files:
   - Run: npm run type:check
   - Report any type errors
```

**Usage:**
```bash
/add-types @src/utils/helper.ts @src/lib/api.ts @src/services/auth.ts
```

---

### File Pattern Matching

**Using glob patterns with Glob tool:**
```markdown
---
description: Optimize all components
allowed-tools: Read, Edit, Glob, Grep
---

Optimize all components:

1. Find component files:
   - Use Glob: **/*Component.tsx
   - Get list of all component files

2. For each component:
   - Read file
   - Apply optimization patterns
   - Save if improved

3. Summary: files optimized
```

**Usage:**
```bash
/optimize-components
```

---

### File Reference Best Practices

**Validate file exists:**
```markdown
1. Verify files:
   - Check each file in $ARGUMENTS exists
   - If any missing:
     - List missing files
     - Ask user to verify paths
     - Exit
   - If all exist: proceed
```

**Backup strategy:**
```markdown
1. Backup before modifying:
   - For each file, note current state
   - If changes fail:
     - Restore from backup
     - Report error
```

**Show changes:**
```markdown
3. Show modifications:
   - For each modified file:
     - Show diff of changes
     - Explain what was changed and why
```

---

### Use Cases

**Batch Processing:**
```markdown
---
description: Add copyright header to files
---

Add copyright to: $ARGUMENTS

1. For each file:
   - Read file
   - Check if header already exists
   - If not: add copyright header at top
   - Save file
2. Summary: files updated
```

**Cross-file Refactoring:**
```markdown
---
description: Rename function across files
argument-hint: [old-name] [new-name] @files
---

Rename $1 to $2 in specified files

1. For each file in remaining arguments:
   - Search for function $1
   - Replace with $2
   - Update imports/exports
   - Save changes

2. Run tests to verify
```

**Consistency Checks:**
```markdown
---
description: Check files follow style guide
---

Check style in: $ARGUMENTS

1. For each file:
   - Read file
   - Check against style rules
   - Note violations

2. Report:
   - Files with violations
   - Specific issues found
   - Auto-fixable vs manual
```

---

## Conditional Logic

### Overview
Commands can include decision points and branching logic.

### If-Then-Else Patterns

**Basic conditional:**
```markdown
1. Check test coverage:
   - Run: npm run test:coverage
   - Extract coverage percentage

2. Decision based on coverage:
   - If coverage >= 80%:
     - ✅ Coverage meets requirements
     - Proceed to commit
   - If coverage < 80%:
     - ❌ Coverage too low
     - List uncovered files
     - Stop workflow
     - Suggest: add tests before committing
```

---

### Multiple Conditions

```markdown
1. Analyze change type:
   - Check staged files: git diff --cached --name-only

2. Determine validation needed:
   - If only .md files changed:
     - Skip tests (documentation only)
     - Run spell check
   - If .ts/.tsx files changed:
     - Run type check
     - Run tests
     - Run linter
   - If package.json changed:
     - Verify lock file updated
     - Run dependency audit
     - Run full test suite
   - If Dockerfile changed:
     - Validate Dockerfile
     - Check for best practices
     - Suggest security scan
```

---

### Validation and Early Exit

```markdown
1. Validate prerequisites:
   - Check gh CLI installed: gh --version
   - Check authenticated: gh auth status

2. Early exit if issues:
   - If gh not installed:
     - Error: gh CLI required
     - Install: https://cli.github.com
     - Exit workflow
   - If not authenticated:
     - Error: Not authenticated with GitHub
     - Run: gh auth login
     - Exit workflow
   - If all OK:
     - Proceed to main workflow
```

---

### Complex Decision Trees

```markdown
1. Analyze PR context:
   - Get PR: gh pr view $1
   - Extract: size (files changed), labels, author

2. Multi-level decision:
   - If PR has label "hotfix":
     - Priority: critical
     - Review depth: security and correctness only
     - Timeline: immediate
   - Else if PR has label "breaking":
     - Priority: high
     - Review depth: full (security, architecture, docs)
     - Check: migration guide present
   - Else if files changed > 50:
     - Priority: medium
     - Suggest: break into smaller PRs
     - Review depth: high-level architecture first
   - Else:
     - Priority: normal
     - Review depth: standard
     - Timeline: regular

3. Execute review based on priority and depth from step 2
```

---

### Use Cases

**Environment-specific actions:**
```markdown
1. Detect environment:
   - Check: git branch --show-current

2. Environment-specific steps:
   - If branch is "main":
     - Require: all tests pass
     - Require: code review approved
     - Deploy to: production
   - If branch is "develop":
     - Require: tests pass
     - Deploy to: staging
   - If branch is feature/*:
     - Run: tests only
     - No deployment
```

**User confirmation:**
```markdown
1. Show planned changes:
   - List: files to be modified
   - Preview: what will change

2. Wait for confirmation:
   - Ask user: "Proceed with these changes? (yes/no)"
   - If yes: apply changes
   - If no: exit without changes
```

---

## Context from Claude

### Overview
Commands can leverage Claude's knowledge and reasoning throughout execution.

### Asking Claude for Analysis

```markdown
1. Analyze code complexity:
   - Read: src/components/LargeComponent.tsx
   - Identify:
     - Functions over 50 lines
     - Nested conditionals > 3 levels
     - Repeated patterns
   - Suggest: specific refactoring approaches

2. Based on analysis in step 1:
   - Prioritize refactoring by impact
   - Plan refactoring steps
   - Consider: backward compatibility
```

---

### Pattern Recognition

```markdown
1. Identify design patterns:
   - Read codebase structure
   - Recognize patterns in use:
     - Singleton
     - Factory
     - Observer
     - etc.

2. Consistency check:
   - For new feature in $ARGUMENTS
   - Recommend: which pattern to follow
   - Explain: why based on existing patterns
```

---

### Code Generation

```markdown
1. Understand requirements:
   - Feature description: $ARGUMENTS
   - Review: similar existing code
   - Identify: patterns and conventions

2. Generate implementation:
   - Following project style from existing code
   - Matching patterns used in codebase
   - Include: tests following test patterns
   - Add: documentation in project style
```

---

### Explanation and Documentation

```markdown
1. Analyze complex code:
   - Read: $ARGUMENTS (complex file)
   - Understand: what code does

2. Generate documentation:
   - High-level overview
   - Explain complex algorithms
   - Document side effects
   - Add inline comments for tricky parts
   - Generate README section
```

---

### Use Cases

**Intelligent code review:**
```markdown
1. Comprehensive review:
   - Read PR changes
   - Understand intent from PR description
   - Analyze changes in context of codebase

2. Provide feedback:
   - Not just syntax issues
   - Architecture concerns
   - Better approaches
   - Edge cases to consider
   - Security implications
```

**Smart refactoring:**
```markdown
1. Analyze refactoring target:
   - Read code to refactor
   - Understand purpose and usage
   - Find all usages in codebase

2. Plan refactoring:
   - Identify safe changes
   - Plan migration path
   - Consider impact on callers

3. Execute refactoring:
   - Refactor code
   - Update all usages
   - Maintain functionality
   - Add tests if missing
```

---

## Parameter Defaults and Validation

### Overview
Commands can provide default values and validate parameters before execution.

### Default Values

**Bash-style defaults:**
```markdown
---
description: Review PR with optional priority
argument-hint: [PR-number] [priority]
---

Review PR #$1 with priority: ${2:-medium}

Priority levels:
- high: Full security and architecture review
- medium: Standard code review (default)
- low: Quick scan for obvious issues
```

**Usage:**
```bash
/review-pr 123        # Uses default: medium
/review-pr 123 high   # Uses specified: high
```

---

### Multiple Defaults

```markdown
---
description: Deploy with optional environment and region
argument-hint: [environment] [region] [flags]
---

Deploy to ${1:-staging} in region ${2:-us-east-1} with flags: ${3}

Defaults:
- Environment: staging
- Region: us-east-1
- Flags: none
```

---

### Parameter Validation

**Type validation:**
```markdown
1. Validate inputs:
   - Check $1 is a number (PR number)
     - Try: gh pr view $1
     - If error: not a valid PR number
   - Check $2 is one of: high, medium, low
     - If not: show usage and exit

2. Only proceed if validation passes
```

**Format validation:**
```markdown
1. Validate branch name:
   - Check $ARGUMENTS matches pattern: (feature|fix|chore)/[a-z-]+
   - If invalid:
     - Error: Invalid branch name
     - Expected: type/description
     - Examples: feature/new-login, fix/auth-bug
     - Exit

2. Create valid branch name from step 1
```

**Range validation:**
```markdown
1. Validate coverage threshold:
   - Check $1 is a number between 0 and 100
   - If not:
     - Error: Coverage must be 0-100
     - Exit

2. Use threshold: $1
```

---

### Required vs Optional Parameters

```markdown
---
description: Create feature with optional description
argument-hint: [feature-name] [description]
---

Create feature: $1

1. Validate required parameter:
   - If $1 is empty:
     - Error: Feature name required
     - Usage: /create-feature [name] [description]
     - Exit
   - Otherwise: proceed

2. Use optional description:
   - If $2 provided:
     - Description: $2
   - If $2 not provided:
     - Description: "New feature: $1"

3. Create feature with name $1 and description from step 2
```

---

### Use Cases

**Flexible deployment:**
```markdown
---
argument-hint: [environment] [skip-tests] [dry-run]
---

Deploy to ${1:-staging}

Options:
- Skip tests: ${2:-false}
- Dry run: ${3:-false}

1. Validate environment:
   - Must be: dev, staging, or production
   - If invalid: show options and exit

2. Execute deployment with options
```

**Smart defaults from context:**
```markdown
1. Determine defaults from context:
   - Current branch: git branch --show-current
   - If on feature/*: default environment = dev
   - If on develop: default environment = staging
   - If on main: default environment = production

2. Use environment: ${1:-[default-from-step-1]}
```

---

## Sub-steps and Grouping

### Overview
Organize complex commands with hierarchical steps and logical grouping.

### Hierarchical Steps

```markdown
1. Pre-flight checks:
   a. Verify git is clean
   b. Check all tests pass
   c. Verify no uncommitted changes

2. Build phase:
   a. Clean build directory
   b. Run production build
   c. Verify build artifacts

3. Deployment:
   a. Upload to S3
   b. Invalidate CloudFront cache
   c. Verify deployment succeeded

4. Post-deployment:
   a. Run smoke tests
   b. Check monitoring dashboards
   c. Notify team
```

---

### Logical Grouping

```markdown
1. ** Validation Phase **

   Environment checks:
   - Docker installed and running
   - kubectl configured correctly
   - AWS credentials valid

   Code quality:
   - All tests passing
   - Lint errors fixed
   - Type checking passes

2. ** Build Phase **

   Compilation:
   - Build TypeScript
   - Bundle with webpack
   - Optimize assets

   Verification:
   - Check bundle size < 1MB
   - Verify no source maps in production
   - Test build locally

3. ** Deploy Phase **

   Upload:
   - Push to registry
   - Update manifests
   - Apply to cluster

   Verification:
   - Pods running
   - Health checks pass
   - Services accessible
```

---

### Progress Indicators

```markdown
1. Phase 1/4: Validation
   ✓ Git status checked
   ✓ Tests passed
   ✓ Lint passed
   [Progress: 25%]

2. Phase 2/4: Build
   ✓ TypeScript compiled
   ✓ Assets bundled
   ⏳ Optimizing...
   [Progress: 50%]

3. Phase 3/4: Test
   ✓ Unit tests
   ✓ Integration tests
   ⏳ E2E tests running...
   [Progress: 75%]

4. Phase 4/4: Deploy
   ⏳ Uploading to S3...
```

---

### Use Cases

**Complex workflows:**
```markdown
1. ** Data Migration **

   Backup:
   - Export current data
   - Verify backup integrity
   - Store backup location

   Migration:
   - Run migration scripts
   - Transform data
   - Validate transformed data

   Import:
   - Import to new system
   - Verify import succeeded
   - Run data integrity checks

   Verification:
   - Compare old vs new
   - Run application tests
   - Check performance

2. ** Rollback Plan ** (if anything fails)
   - Restore from backup
   - Verify restoration
   - Notify team
```

**Multi-service deployment:**
```markdown
1. ** Backend Services **

   API Service:
   - Build API
   - Deploy to ECS
   - Run health check

   Worker Service:
   - Build worker
   - Deploy to ECS
   - Verify queue processing

2. ** Frontend **

   Build:
   - Build React app
   - Optimize assets
   - Generate sitemap

   Deploy:
   - Upload to S3
   - Invalidate CDN
   - Verify loading

3. ** Verification **
   - E2E smoke tests
   - Monitor error rates
   - Check all integrations
```

---

## Multi-command Workflows

### Overview
Commands can reference or chain with other commands for complex workflows.

### Sequential Command References

```markdown
---
description: Complete feature workflow
argument-hint: [feature-name]
---

Full feature cycle for: $ARGUMENTS

1. Development phase:
   - Create branch: feature/$ARGUMENTS
   - Implement feature (manual work by user)
   - When ready, proceed to step 2

2. Pre-commit validation:
   - Run validation: /pre-commit
   - If fails: fix issues and retry
   - If passes: proceed to step 3

3. PR preparation:
   - Prepare PR: /prepare-pr main
   - Review PR description
   - Submit for team review

4. Post-merge:
   - Pull latest: git pull origin main
   - Delete feature branch
   - Update local: git fetch --prune

Summary: Feature workflow complete
```

---

### Conditional Command Execution

```markdown
1. Analyze changes:
   - Check: git diff --cached --name-only
   - Categorize: frontend, backend, or both

2. Run appropriate validations:
   - If frontend changed:
     - Run: /validate-frontend
   - If backend changed:
     - Run: /validate-backend
   - If both changed:
     - Run: /validate-frontend
     - Then: /validate-backend
     - Finally: /validate-integration

3. Summary of all validations
```

---

### Command Composition

**Building blocks approach:**

```markdown
# /check-git - Simple building block
---
description: Check git status and branch
---
1. Show: git status
2. Show: current branch
3. Check: uncommitted changes

# /check-tests - Simple building block
---
description: Run test suite
---
1. Run: npm test
2. Report: pass/fail

# /pre-commit - Composed command
---
description: Pre-commit validation (uses building blocks)
---
1. Git checks: /check-git
2. Test suite: /check-tests
3. Lint: npm run lint
4. Summary: ready to commit or issues found
```

---

### Use Cases

**Morning workflow:**
```markdown
---
description: Complete morning routine
---

Morning startup:

1. Project sync: /sync-project
   - Pull latest changes
   - Update dependencies
   - Verify builds

2. Work planning: /plan-day
   - Review assigned items
   - Check blockers
   - Set priorities

3. Ready to start:
   - Summary of priorities
   - Next action items
```

**Release workflow:**
```markdown
---
description: Complete release process
argument-hint: [version]
---

Release version: $1

1. Pre-release validation: /validate-release
   - All tests pass
   - Documentation current
   - Changelog ready

2. Version bump: /bump-version $1
   - Update package.json
   - Update files
   - Create git tag

3. Build and publish: /publish-release
   - Build artifacts
   - Run final checks
   - Publish to registry

4. Post-release: /post-release $1
   - Create GitHub release
   - Notify team
   - Update documentation site
```

---

## Environment Detection

### Overview
Commands can detect and adapt to different environments.

### Detecting Current Environment

```markdown
1. Detect environment from context:

   From git branch:
   - If on "main": production environment
   - If on "develop": staging environment
   - If on feature/*: development environment

   From environment variables:
   - Check: $NODE_ENV
   - Check: $ENVIRONMENT

   From files:
   - Check: .env file contents
   - Check: config files

2. Use detected environment for subsequent steps
```

---

### Adapting to Environment

```markdown
1. Detect environment (see above)

2. Environment-specific behavior:

   Production:
   - Require: code review approval
   - Require: all tests green
   - Enable: detailed logging
   - Use: production credentials

   Staging:
   - Require: tests pass
   - Enable: debug mode
   - Use: staging credentials

   Development:
   - Skip: some checks for speed
   - Enable: all debugging
   - Use: local credentials

3. Execute with environment-specific settings
```

---

### Cross-platform Compatibility

```markdown
1. Detect operating system:
   - Run: uname -s
   - Detect: macOS, Linux, or Windows (WSL)

2. Use platform-specific commands:

   macOS:
   - Open: open file.txt
   - Copy: pbcopy

   Linux:
   - Open: xdg-open file.txt
   - Copy: xclip

   Windows (WSL):
   - Open: cmd.exe /c start file.txt
   - Copy: clip.exe

3. Execute with correct commands for platform
```

---

### Tool Availability

```markdown
1. Check tool availability:
   - Docker: docker --version
   - kubectl: kubectl version --client
   - gh CLI: gh --version
   - npm: npm --version

2. Adapt workflow based on available tools:
   - If Docker available:
     - Use containerized tests
   - If Docker not available:
     - Use local test environment
     - Warn: some tests may behave differently

3. Execute with available tools
```

---

### Use Cases

**Smart deployment:**
```markdown
1. Detect deploy target:
   - From arguments: ${1}
   - Or from branch
   - Or from environment variable
   - Or ask user

2. Environment-specific deployment:
   - Production: requires approval, full tests, monitoring
   - Staging: requires tests, basic monitoring
   - Dev: minimal checks, fast deployment
```

**CI/CD detection:**
```markdown
1. Detect CI environment:
   - Check: $CI environment variable
   - Check: $GITHUB_ACTIONS
   - Check: $JENKINS_URL
   - Check: $GITLAB_CI

2. If in CI:
   - Use non-interactive mode
   - Use CI-specific credentials
   - Enable detailed logging
   - Post results to CI system

3. If local:
   - Interactive mode OK
   - Use local credentials
   - Shorter output
```

---

## Dynamic Tool Selection

### Overview
Commands can intelligently choose which tools to use based on context.

### Conditional Tool Usage

```markdown
1. Determine search tool:
   - Check if: ripgrep (rg) installed
   - If yes: use rg (faster)
   - If no: use standard grep

2. Search using selected tool:
   - With rg: rg "pattern" --type js
   - With grep: grep -r "pattern" --include="*.js"

3. Process results (same regardless of tool)
```

---

### Fallback Strategies

```markdown
1. Try preferred method:
   - Check: gh CLI available
   - If yes:
     - Use: gh pr list --author @me
   - If no:
     - Fallback: curl GitHub API
     - Or: open GitHub in browser
     - Or: notify user to install gh

2. Process results from whichever method worked
```

---

### Tool Selection Logic

```markdown
1. Select test runner:

   Check package.json scripts:
   - If has "test:unit": use npm run test:unit
   - Else if has "test": use npm test
   - Else if jest installed: use npx jest
   - Else if mocha installed: use npx mocha
   - Else: notify no test runner found

2. Run tests with selected runner

3. Parse output (adapt to runner format)
```

---

## State Management

### Overview
Commands can maintain context and state across steps.

### Carrying State Between Steps

```markdown
1. Initial state collection:
   - Current branch: git branch --show-current
   - Store as: $CURRENT_BRANCH
   - Modified files: git diff --name-only
   - Store as: $MODIFIED_FILES
   - Test coverage: npm run test:coverage
   - Store as: $COVERAGE

2. Use state from step 1:
   - Create PR from $CURRENT_BRANCH
   - Include $MODIFIED_FILES in description
   - Note coverage is $COVERAGE

3. Update state based on actions:
   - PR created: store PR number
   - Use PR number in step 4

4. Final actions using all state:
   - Add labels to PR #[number-from-step-3]
   - Post comment with coverage $COVERAGE
   - List files changed: $MODIFIED_FILES
```

---

### Accumulating Results

```markdown
1. Initialize results tracking:
   - Total files: 0
   - Files fixed: 0
   - Files with errors: 0
   - Error list: empty

2. Process each file:
   - For each TypeScript file:
     - Increment: total files
     - Try to add types
     - If successful: increment files fixed
     - If error: increment files with errors, add to error list

3. Final report using accumulated results:
   - Processed: [total files] files
   - Successfully fixed: [files fixed]
   - Had errors: [files with errors]
   - Errors encountered: [error list]
   - Success rate: [files fixed / total files]%
```

---

### Complex State Management

```markdown
1. ** Collect comprehensive state **

   Git state:
   - Branch name
   - Commit count ahead of main
   - Modified files
   - Staged files

   Code state:
   - Test coverage
   - Lint errors
   - Type errors
   - Build status

   Project state:
   - Dependencies up to date
   - Security vulnerabilities
   - Documentation status

2. ** Analyze state **
   - Determine: ready for PR or issues to fix
   - Calculate: risk score based on state
   - Identify: blocking issues

3. ** Take action based on analysis **
   - If ready (low risk, no blocking issues):
     - Create PR
     - Add appropriate labels based on state
   - If issues (high risk or blockers):
     - List issues
     - Suggest fixes
     - Offer to fix automatically where possible

4. ** Report final state **
   - What was done
   - Current status
   - Next steps
```

---

## Combining Advanced Features

### Example: Sophisticated PR Review Command

```markdown
---
description: Comprehensive PR review with intelligent adaptation
argument-hint: [PR-number] [priority]
model: claude-3-7-sonnet-20250219
allowed-tools: Bash(gh:*), Bash(git:*), Read, Grep, Glob
---

Review PR #$1 with priority ${2:-medium}

1. ** Context Collection **
   - Fetch PR: gh pr view $1
   - Extract: title, description, labels, files changed
   - Store: PR metadata for use in later steps
   - Detect: PR type (feature/fix/docs) from labels

2. ** Environment Detection **
   - Check: base branch (main, develop, release/*)
   - Detect: project type from files
   - Identify: testing framework in use
   - Store: context for adapted review

3. ** Dynamic Review Depth **
   Based on priority ($2) and PR type (from step 1):

   High priority OR breaking changes:
   - Security audit
   - Architecture review
   - Performance analysis
   - Full test coverage
   - Documentation completeness

   Medium priority (default):
   - Code correctness
   - Basic security check
   - Test presence
   - Style compliance

   Low priority:
   - Quick scan
   - Obvious issues only

4. ** Intelligent File Analysis **
   For each changed file:
   - Read file: (use Read tool)
   - Detect language: from extension
   - Apply language-specific checks:
     - TypeScript: type usage, null checks
     - React: hooks rules, performance
     - CSS: methodology, browser support
   - Accumulate findings

5. ** Conditional Checks **
   Based on files changed (from step 1):

   If package.json changed:
   - Verify lock file updated
   - Check for security vulnerabilities
   - Validate version bumps

   If migrations added:
   - Check reversibility
   - Verify test data
   - Check for breaking changes

   If config files changed:
   - Validate syntax
   - Check for secrets
   - Verify defaults

6. ** Context-Aware Feedback **
   Using Claude's knowledge:
   - Suggest better approaches
   - Identify potential bugs
   - Note edge cases
   - Recommend improvements
   - Explain reasoning

7. ** Multi-level Report **
   Grouped by severity:

   🚨 Blocking (must fix):
   - [List from analysis]

   ⚠️  Important (should fix):
   - [List from analysis]

   💡 Suggestions (nice to have):
   - [List from analysis]

   ✅ Positive observations:
   - [List good practices]

8. ** Action Decision **
   Based on findings:
   - No blocking issues: approve
   - Blocking issues: request changes
   - Only suggestions: comment

   Post review: gh pr review $1 --[decision]

Summary:
- Review depth: [priority from $2]
- Files reviewed: [count]
- Issues found: [breakdown by severity]
- Decision: [approve/request-changes/comment]
```

---

## Best Practices for Advanced Features

1. **Start Simple:** Add advanced features incrementally
2. **Document Complexity:** Explain complex logic in comments
3. **Test Thoroughly:** Test edge cases and error conditions
4. **Graceful Degradation:** Handle missing tools/features
5. **Clear State:** Make state transitions explicit
6. **Error Handling:** Check success at each step
7. **User Feedback:** Provide progress updates
8. **Maintain Focus:** Don't over-complicate
9. **Reusability:** Design for reuse across projects
10. **Performance:** Consider efficiency of complex operations

---

## Summary

Advanced features enable sophisticated commands that:
- Adapt to context and environment
- Make intelligent decisions
- Handle complex workflows
- Provide better user experience
- Leverage Claude's full capabilities

Use these features judiciously to create powerful, flexible commands while maintaining clarity and maintainability.
