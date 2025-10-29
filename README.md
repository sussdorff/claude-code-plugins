# Claude Code Plugins

Professional Claude Code plugins for shell scripting, git workflows, and development automation.

## Installation

Add this marketplace to Claude Code:

```bash
/plugin marketplace add sussdorff/claude-code-plugins
```

Then browse and install individual plugins via the `/plugin` menu in Claude Code.

## Available Plugins

### Shell Scripting Best Practices

#### bash-best-practices (v1.2.0)

Cross-platform Bash scripting guide with comprehensive best practices.

**Features:**
- ShellCheck integration for linting
- Tree-sitter-based function discovery
- 20 comprehensive reference guides covering strict mode, arrays, error handling, and more
- Common patterns and code review checklists
- Works on macOS, Linux, and WSL

See [bash-best-practices/SKILL.md](./bash-best-practices/SKILL.md)

---

#### zsh-best-practices (v1.4.0)

macOS ZSH scripting best practices with automated function discovery.

**Features:**
- ZSH-specific patterns (typeset, 1-based arrays, word splitting)
- Automated function discovery with tree-sitter
- 10 comprehensive reference guides
- macOS-specific considerations (BSD vs GNU tools)
- Code review checklists

See [zsh-best-practices/SKILL.md](./zsh-best-practices/SKILL.md)

---

#### powershell-pragmatic (v1.0.0)

Production-ready PowerShell coding patterns.

**Features:**
- Pragmatic best practices over dogmatic rules
- PSScriptAnalyzer integration
- Error handling and logging strategies
- German output support for user-facing text (ASCII-only)
- Reusability and modularity patterns

See [powershell-pragmatic/SKILL.md](./powershell-pragmatic/SKILL.md)

---

### Git Workflow Tools

#### git-operations (v1.0.0)

Safe git operations with comprehensive safety checks.

**Features:**
- Git Safety Protocol enforcement (authorship verification, push status checks)
- Styleable commit messages (6 built-in styles: conventional, pirate, snarky, emoji, minimal, corporate)
- Branch protection (blocks force-push to main/master)
- Smart amend logic for pre-commit hooks
- Configuration via CLAUDE.md

See [git-operations/SKILL.md](./git-operations/SKILL.md)

---

#### git-worktree-tools (v1.0.0)

Git worktree lifecycle management with project-aware configuration syncing.

**Features:**
- Create, validate, and remove worktrees
- Automatic branch handling and ticket extraction
- Configuration synchronization (.claude/, CLAUDE.local.md, .env)
- Black box operation (run from outside worktree)
- JSON output for programmatic integration

See [git-worktree-tools/skill.md](./git-worktree-tools/skill.md)

---

#### branch-synchronizer (v1.0.0)

Intelligent branch synchronization with conflict-aware rebasing.

**Features:**
- Fetch latest from remote and rebase onto main
- Auto-stash uncommitted changes before rebase
- Conflict detection with context-aware handling (agent vs interactive mode)
- Branch discovery by ticket pattern (PROJ-*, TICKET-*, etc.)
- Never auto-pushes (safety-first approach)

See [branch-synchronizer/SKILL.md](./branch-synchronizer/SKILL.md)

---

### Development Tools

#### youtube-music-updater (v1.0.0)

Update YouTube Music desktop application from GitHub releases.

**Features:**
- Version checking and comparison
- App restart and quarantine attribute removal (macOS)
- Handles pear-devs GitHub releases
- macOS focused

See [youtube-music-updater/SKILL.md](./youtube-music-updater/SKILL.md)

---

#### reference-file-compactor (v1.0.0)

Optimize and compact skill reference files using validation-driven workflow.

**Features:**
- Single file or whole skill compaction
- Validation-driven workflow
- Context-aware compression
- Maintains reference integrity

See [reference-file-compactor/SKILL.md](./reference-file-compactor/SKILL.md)

---

### Productivity Tools

#### timing-matcher (v1.0.0)

Process large Timing app JSON exports to match unassigned activities to projects using pattern recognition, git commit correlation, and intelligent aggregation.

**Features:**
- Handles 70k+ entries efficiently with incremental processing
- Pattern extraction from training data (ticket prefixes, activity patterns)
- Git commit correlation (±15 min window with commit SHA linking)
- Intelligent activity aggregation with confidence scoring
- Timing MCP server integration for bulk time entry creation
- Duplicate detection and rate limit handling

See [timing-matcher/SKILL.md](./timing-matcher/SKILL.md)

---

## Coming Soon

These plugins are under development and available in feature branches:

- **shellspec-tester** (branch: `feature/shellspec-tester`) - BDD-style testing for shell scripts
- **reference-file-compactor** (branch: `feature/reference-compactor`) - Optimize skill reference files

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - see [LICENSE](./LICENSE) file for details.

Copyright (c) 2025 Malte Sussdorff

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for version history and detailed changes.
