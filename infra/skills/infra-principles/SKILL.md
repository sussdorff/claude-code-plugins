---
name: infra-principles
model: haiku
description: >-
  Infrastructure engineering principles for server work, deployments, and multi-agent collaboration.
  Use when working on servers, deploying services, writing deployment scripts, or coordinating
  parallel agent edits. Triggers on infrastructure, deploy, server, IaC, multi-agent, parallel edits.
requires_standards: [english-only]
---

# Infrastructure Principles

## When to Use

- Working on remote servers (deployment, configuration, debugging)
- Writing deployment scripts or automation
- Coordinating multi-agent edits in the same repository
- Deciding whether to write a wrapper script vs use native tooling
- Planning self-updating bot/service deployments

## Core Principles

### Software before Scripts

Investigate software's native mechanisms first (config files, DB, admin UI) before writing wrapper scripts. Only create automation when native mechanisms are insufficient.

### Infrastructure as Code

Fix problems IN THE SCRIPT, not manually on the server. Manual fixes are acceptable only to verify hypotheses — then port the fix back to the script/config.

### Verify Before Deleting

Always verify the destination has the expected files/data before deleting sources after migration. Never assume a migration succeeded without checking.

## Multi-Agent Git Safety

When multiple agents work in parallel on the same repository:

- **Specific staging only**: Always `git add <specific-files>`, never `git add -A` or `git add .`
- **Dirty worktrees are normal**: `git status` may show changes from other agents — ignore them
- **Untracked files from others**: May appear — don't investigate or clean up
- **Merge strategy**: `git pull --no-rebase` for branches with existing merge commits — `--rebase` causes confusing conflicts
- **Before editing in worktree**: `git fetch && git log --oneline origin/main -- <file>` to check if another worktree recently changed the file
- **Design files** (`design/*.pen`): Team-owned assets — commit only after user confirmation

## Deployment Patterns

### Self-Updating Services

For simple bot/service deployments: write a short shell script, SSH-triggerable. Do not use GitHub Actions for straightforward self-updates.

```bash
# Pattern: deploy.sh on the server
#!/bin/bash
cd /opt/myservice
git pull
# language-specific restart (systemctl, pm2, etc.)
sudo systemctl restart myservice
```

Trigger from local: `ssh myserver '/opt/myservice/deploy.sh'`

### Testing Remote Services

- **Telegram bots**: Test via `playwright-cli` on `web.telegram.org` (local Mac, as real user). Never install test clients on production servers.
- **Web services**: Always verify the endpoint responds before investigating infrastructure (`curl` before reading configs).
