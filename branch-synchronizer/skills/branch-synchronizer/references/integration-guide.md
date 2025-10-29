# Branch Synchronizer - Integration Guide

Comprehensive guide for integrating branch-synchronizer with other tools, workflows, and automation systems.

## Table of Contents

- [Claude Code Integration](#claude-code-integration)
- [Skill Integration](#skill-integration)
- [CI/CD Integration](#cicd-integration)
- [Git Hooks Integration](#git-hooks-integration)
- [IDE Integration](#ide-integration)
- [Automation Workflows](#automation-workflows)

## Claude Code Integration

The branch-synchronizer skill is designed for seamless integration with Claude Code's agent workflows.

### Invocation Patterns

Claude Code invokes the skill through the allowed_tools mechanism defined in SKILL.md:

```yaml
allowed_tools: Bash(./.claude/skills/branch-synchronizer/scripts/sync-branch.zsh *), Bash(jq:*)
```

### Common Invocation Scenarios

#### User-Initiated Sync

**User request:**
```
"Sync my branch with main"
```

**Claude Code action:**
```zsh
./.claude/skills/branch-synchronizer/scripts/sync-branch.zsh
```

**Expected output:**
```
🔄 Branch Synchronizer
  Repository: /path/to/repo
  Branch: feature/PROJ-123/fix
  Base: main

  → Fetching from origin...
  → Rebasing onto origin/main...
  ✅ Branch synchronized successfully

📌 Next steps:
  1. Review the changes
  2. Test your code
  3. Push to remote: git push origin feature/PROJ-123/fix
```

#### Pattern-Based Sync

**User request:**
```
"Update branch PROJ-456"
```

**Claude Code action:**
```zsh
./.claude/skills/branch-synchronizer/scripts/sync-branch.zsh --pattern PROJ-456
```

**Expected output:**
```
🔍 Finding branch for pattern: PROJ-456
✅ Found branch: feature/PROJ-456/update

🔄 Branch Synchronizer
  Repository: /path/to/repo
  Branch: feature/PROJ-456/update
  Base: main

  → Fetching from origin...
  → Rebasing onto origin/main...
  ✅ Branch synchronized successfully
```

#### Worktree Sync

**User request:**
```
"Sync the worktree for CH2-789"
```

**Claude Code action:**
```zsh
./.claude/skills/branch-synchronizer/scripts/sync-branch.zsh \
  --path /repo/.worktrees/CH2-789
```

### Conflict Handling in Claude Code

When conflicts occur, Claude Code receives exit code 1 and error output:

**Agent Mode Response:**
```
⚠️  Rebase encountered conflicts - auto-aborting
ℹ️  Worktree left at original state

Manual resolution needed:
  cd /path/to/worktree
  git rebase origin/main
  # Resolve conflicts
  git rebase --continue
```

**Claude Code should:**
1. Inform user that conflicts require manual resolution
2. Provide the conflict resolution commands
3. Offer to guide through conflict resolution if user requests
4. Not attempt to automatically resolve conflicts

### Status Checking

Claude Code can check sync status before operations:

```zsh
# Check if sync needed
STATUS=$(./.claude/skills/branch-synchronizer/scripts/sync-branch.zsh --status)
NEEDS_SYNC=$(echo "$STATUS" | jq -r '.needs_sync')

if [ "$NEEDS_SYNC" = "true" ]; then
  # Proactively suggest sync
  echo "Your branch is behind main. Would you like to sync before testing?"
fi
```

### Proactive Sync Suggestions

Claude Code should proactively suggest syncing when:

1. **Before running tests**
   ```
   User: "Run the tests"
   Claude: "I notice your branch is 15 commits behind main. Should I sync first?"
   ```

2. **Before creating PR**
   ```
   User: "Create a pull request"
   Claude: "Let me sync your branch with main first to ensure tests pass..."
   ```

3. **When resuming work**
   ```
   User: "Continue working on PROJ-123"
   Claude: "This branch was last updated 3 days ago. Let me sync with main first..."
   ```

## Skill Integration

Integration patterns with other skills in the solutio-claude-skills marketplace.

### With git-worktree-tools Skill

The git-worktree-tools skill manages worktree lifecycle, while branch-synchronizer keeps worktrees current.

#### Workflow Integration

**When creating worktree:**
```zsh
# git-worktree-tools creates the worktree
./git-worktree-tools/scripts/create-worktree.zsh --ticket PROJ-123

# branch-synchronizer syncs it immediately
./branch-synchronizer/scripts/sync-branch.zsh --pattern PROJ-123
```

**When validating worktree:**
```zsh
# git-worktree-tools validates structure
./git-worktree-tools/scripts/validate-worktree.zsh PROJ-123

# branch-synchronizer checks sync status
./branch-synchronizer/scripts/sync-branch.zsh --pattern PROJ-123 --status
```

#### Combined Script Example

```zsh
#!/usr/bin/env zsh
# Combined worktree setup with sync

TICKET=$1

# Create worktree
if ./git-worktree-tools/scripts/create-worktree.zsh --ticket "$TICKET"; then
  echo "Worktree created, syncing with main..."

  # Sync the new worktree
  if ./branch-synchronizer/scripts/sync-branch.zsh --pattern "$TICKET"; then
    echo "✅ Worktree ready for work"
  else
    echo "⚠️  Sync failed - may need manual conflict resolution"
  fi
fi
```

### With jira-context-fetcher Skill

The jira-context-fetcher downloads ticket data, and branch-synchronizer ensures the working branch is current.

#### Workflow Integration

```zsh
# Fetch ticket context
./jira-context-fetcher/scripts/fetch-ticket.zsh --ticket PROJ-123

# Ensure branch is up-to-date before starting work
./branch-synchronizer/scripts/sync-branch.zsh --pattern PROJ-123

# Now ready to work with current context and synced branch
```

### With git-operations Skill (Future)

The git-operations skill handles safe git operations like commits, pushes, and force-pushes.

#### Workflow Integration

```zsh
# Sync branch
./branch-synchronizer/scripts/sync-branch.zsh

# Make changes and commit
# ... code changes ...

# Safe force-push using git-operations
./git-operations/scripts/safe-force-push.zsh --branch feature/PROJ-123/fix
```

## CI/CD Integration

Integrate branch-synchronizer into continuous integration and deployment pipelines.

### GitLab CI Integration

#### Pre-Merge Branch Validation

Ensure branches are synced before merge:

```yaml
# .gitlab-ci.yml

stages:
  - validate
  - test
  - merge

check-branch-sync:
  stage: validate
  script:
    - git clone https://github.com/your-org/solutio-claude-skills.git skills
    - cd skills/branch-synchronizer
    - ./scripts/sync-branch.zsh --status > /tmp/sync-status.json
    - |
      COMMITS_BEHIND=$(jq -r '.commits_behind' /tmp/sync-status.json)
      if [ "$COMMITS_BEHIND" -gt 0 ]; then
        echo "❌ Branch is $COMMITS_BEHIND commits behind main"
        echo "Please sync your branch: git rebase origin/main"
        exit 1
      fi
    - echo "✅ Branch is up-to-date with main"
  only:
    - merge_requests

run-tests:
  stage: test
  needs: [check-branch-sync]
  script:
    - npm test
  only:
    - merge_requests
```

#### Automatic Sync Bot

Create a bot that auto-syncs branches:

```yaml
# .gitlab-ci.yml

auto-sync-branches:
  stage: sync
  only:
    - schedules
  script:
    - git clone https://github.com/your-org/solutio-claude-skills.git skills
    - |
      # Get all active feature branches
      git branch -r | grep 'feature/' | while read branch; do
        branch_name=$(echo $branch | sed 's/origin\///')
        echo "Syncing $branch_name..."

        # Try to sync
        if ! skills/branch-synchronizer/scripts/sync-branch.zsh \
          --branch "$branch_name" \
          --base-branch main; then
          echo "⚠️  $branch_name has conflicts - notifying developer"
          # Send notification (Slack, email, etc.)
        fi
      done
```

### GitHub Actions Integration

#### Sync Check on PR

```yaml
# .github/workflows/pr-sync-check.yml

name: Check Branch Sync

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  check-sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Clone branch-synchronizer
        run: |
          git clone https://github.com/your-org/solutio-claude-skills.git skills

      - name: Check sync status
        id: sync-check
        run: |
          cd skills/branch-synchronizer
          ./scripts/sync-branch.zsh --status > sync-status.json

          COMMITS_BEHIND=$(jq -r '.commits_behind' sync-status.json)
          NEEDS_SYNC=$(jq -r '.needs_sync' sync-status.json)

          echo "commits_behind=$COMMITS_BEHIND" >> $GITHUB_OUTPUT
          echo "needs_sync=$NEEDS_SYNC" >> $GITHUB_OUTPUT

      - name: Comment on PR
        if: steps.sync-check.outputs.needs_sync == 'true'
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '⚠️ This branch is ${{ steps.sync-check.outputs.commits_behind }} commits behind main. Please sync your branch:\n\n```bash\ngit fetch origin\ngit rebase origin/main\n```'
            })
```

### Jenkins Integration

```groovy
// Jenkinsfile

pipeline {
    agent any

    stages {
        stage('Check Branch Sync') {
            steps {
                script {
                    sh '''
                        git clone https://github.com/your-org/solutio-claude-skills.git skills
                        cd skills/branch-synchronizer
                        ./scripts/sync-branch.zsh --status > sync-status.json
                    '''

                    def syncStatus = readJSON file: 'skills/branch-synchronizer/sync-status.json'

                    if (syncStatus.needs_sync) {
                        echo "⚠️ Branch is ${syncStatus.commits_behind} commits behind main"

                        // Option 1: Fail build
                        error("Branch must be synced with main before merge")

                        // Option 2: Auto-sync (if no conflicts expected)
                        // sh 'skills/branch-synchronizer/scripts/sync-branch.zsh'
                    }
                }
            }
        }

        stage('Test') {
            steps {
                sh 'npm test'
            }
        }
    }
}
```

## Git Hooks Integration

Integrate branch-synchronizer into local git workflows using hooks.

### Pre-Push Hook

Ensure branch is synced before pushing:

```zsh
#!/usr/bin/env zsh
# .git/hooks/pre-push

BRANCH=$(git branch --show-current)

# Skip for main branch
if [ "$BRANCH" = "main" ]; then
    exit 0
fi

echo "Checking if branch is synced with main..."

# Check sync status
STATUS=$(~/.claude/skills/branch-synchronizer/scripts/sync-branch.zsh --status)
COMMITS_BEHIND=$(echo "$STATUS" | jq -r '.commits_behind')

if [ "$COMMITS_BEHIND" -gt 0 ]; then
    echo ""
    echo "⚠️  Your branch is $COMMITS_BEHIND commits behind main"
    echo ""
    echo "Would you like to sync now? (y/n)"
    read -r response

    if [ "$response" = "y" ]; then
        if ~/.claude/skills/branch-synchronizer/scripts/sync-branch.zsh; then
            echo "✅ Branch synced successfully"
        else
            echo "❌ Sync failed - resolve conflicts before pushing"
            exit 1
        fi
    else
        echo "⚠️  Pushing without sync - PR may have conflicts"
    fi
fi

exit 0
```

### Pre-Commit Hook

Warn if branch is significantly behind:

```zsh
#!/usr/bin/env zsh
# .git/hooks/pre-commit

BRANCH=$(git branch --show-current)

# Skip for main branch
if [ "$BRANCH" = "main" ]; then
    exit 0
fi

# Check sync status (non-blocking)
STATUS=$(~/.claude/skills/branch-synchronizer/scripts/sync-branch.zsh --status 2>/dev/null)
COMMITS_BEHIND=$(echo "$STATUS" | jq -r '.commits_behind' 2>/dev/null)

if [ "$COMMITS_BEHIND" -gt 10 ]; then
    echo ""
    echo "⚠️  WARNING: Your branch is $COMMITS_BEHIND commits behind main"
    echo "   Consider syncing soon to avoid conflicts"
    echo "   Run: git rebase origin/main"
    echo ""
    # Don't block commit, just warn
fi

exit 0
```

### Post-Checkout Hook

Auto-sync when switching branches:

```zsh
#!/usr/bin/env zsh
# .git/hooks/post-checkout

PREV_COMMIT=$1
NEW_COMMIT=$2
BRANCH_CHECKOUT=$3

# Only run on branch checkout (not file checkout)
if [ "$BRANCH_CHECKOUT" = "1" ]; then
    BRANCH=$(git branch --show-current)

    # Skip for main branch
    if [ "$BRANCH" = "main" ]; then
        exit 0
    fi

    echo "Checking sync status for $BRANCH..."

    STATUS=$(~/.claude/skills/branch-synchronizer/scripts/sync-branch.zsh --status)
    COMMITS_BEHIND=$(echo "$STATUS" | jq -r '.commits_behind')

    if [ "$COMMITS_BEHIND" -gt 0 ]; then
        echo ""
        echo "ℹ️  This branch is $COMMITS_BEHIND commits behind main"
        echo "   Sync with: ~/.claude/skills/branch-synchronizer/scripts/sync-branch.zsh"
        echo ""
    fi
fi

exit 0
```

## IDE Integration

Integrate branch-synchronizer into your IDE workflow.

### VS Code Tasks

Add sync task to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Sync Branch with Main",
      "type": "shell",
      "command": "${userHome}/.claude/skills/branch-synchronizer/scripts/sync-branch.zsh",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Check Sync Status",
      "type": "shell",
      "command": "${userHome}/.claude/skills/branch-synchronizer/scripts/sync-branch.zsh --status | jq",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    }
  ]
}
```

Usage: `Cmd+Shift+P` → "Tasks: Run Task" → "Sync Branch with Main"

### VS Code Keybinding

Add to `.vscode/keybindings.json`:

```json
[
  {
    "key": "cmd+k cmd+s",
    "command": "workbench.action.tasks.runTask",
    "args": "Sync Branch with Main"
  }
]
```

### JetBrains IDEs (IntelliJ, PyCharm, etc.)

Add External Tool:

1. **Settings** → **Tools** → **External Tools** → **Add**
2. **Name**: Sync Branch with Main
3. **Program**: `$USER_HOME$/.claude/skills/branch-synchronizer/scripts/sync-branch.zsh`
4. **Working Directory**: `$ProjectFileDir$`
5. **Add to**: Tools Menu

## Automation Workflows

Advanced automation patterns using branch-synchronizer.

### Daily Branch Maintenance Script

Sync all active worktrees daily:

```zsh
#!/usr/bin/env zsh
# daily-branch-sync.zsh

WORKTREES_DIR="/repo/.worktrees"
SYNC_SCRIPT="$HOME/.claude/skills/branch-synchronizer/scripts/sync-branch.zsh"

echo "📅 Daily Branch Maintenance - $(date)"
echo ""

SUCCESS_COUNT=0
CONFLICT_COUNT=0
SKIPPED_COUNT=0

for worktree in "$WORKTREES_DIR"/*; do
    if [ ! -d "$worktree" ]; then
        continue
    fi

    WORKTREE_NAME=$(basename "$worktree")
    echo "Processing $WORKTREE_NAME..."

    # Check if branch already merged
    cd "$worktree"
    BRANCH=$(git branch --show-current)

    if git log origin/main --oneline | grep -q "$BRANCH"; then
        echo "  ℹ️  Already merged - skipping"
        ((SKIPPED_COUNT++))
        continue
    fi

    # Attempt sync
    if "$SYNC_SCRIPT" --path "$worktree"; then
        echo "  ✅ Synced successfully"
        ((SUCCESS_COUNT++))
    else
        echo "  ❌ Conflicts detected"
        ((CONFLICT_COUNT++))

        # Log conflict for notification
        echo "$WORKTREE_NAME" >> /tmp/branch-conflicts.log
    fi

    echo ""
done

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary:"
echo "  ✅ Synced: $SUCCESS_COUNT"
echo "  ❌ Conflicts: $CONFLICT_COUNT"
echo "  ⏭️  Skipped: $SKIPPED_COUNT"

# Send notification if conflicts
if [ $CONFLICT_COUNT -gt 0 ]; then
    # Send Slack notification, email, etc.
    echo "Conflicts detected in:"
    cat /tmp/branch-conflicts.log
fi
```

### Pre-Release Branch Sync

Ensure all release branches are current:

```zsh
#!/usr/bin/env zsh
# pre-release-sync.zsh

RELEASE_BRANCH=$1
SYNC_SCRIPT="$HOME/.claude/skills/branch-synchronizer/scripts/sync-branch.zsh"

if [ -z "$RELEASE_BRANCH" ]; then
    echo "Usage: pre-release-sync.zsh <release-branch>"
    exit 1
fi

echo "🚀 Pre-Release Branch Sync"
echo "Release branch: $RELEASE_BRANCH"
echo ""

# Find all branches that should be in release
git branch -r | grep -E 'feature/|bugfix/' | while read remote_branch; do
    branch=$(echo "$remote_branch" | sed 's/origin\///')

    echo "Syncing $branch with $RELEASE_BRANCH..."

    if "$SYNC_SCRIPT" --branch "$branch" --base-branch "$RELEASE_BRANCH"; then
        echo "  ✅ Ready for release"
    else
        echo "  ❌ Needs attention"
    fi
    echo ""
done
```

## See Also

- [SKILL.md](../SKILL.md) - Main skill documentation
- [usage-guide.md](./usage-guide.md) - Usage examples and workflows
- [api-reference.md](./api-reference.md) - Complete API documentation
- [troubleshooting.md](./troubleshooting.md) - Common issues and solutions
