# Changelog

All notable changes to the Claude Code Plugins collection.

Each skill is versioned independently. Versions are assigned when skills are released.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 2025-10-22

### bash-best-practices v1.2.0

#### Changed
- Simplified skill description for better clarity and conciseness
- Enhanced reference guide links with more descriptive annotations:
  - Added "Edge cases, 4 pitfalls, 3 variations" note for strict mode guide
  - Added "Slicing, associative arrays, 6 reusable patterns, 5 specific pitfalls" note for arrays guide
  - Added "100+ item checklist across 10 categories" note for code review checklist
- Streamlined SKILL.md examples for better readability:
  - Simplified array indexing comparison (removed verbose code blocks)
  - Condensed strict mode explanation
  - Consolidated code review section with clearer focus on comprehensive checklist
- Updated lint-and-index.sh to use Python-based analyzer (`analyze-shell-functions.py`)
- Added uv dependency check to lint-and-index.sh
- Reorganized example files: moved example-extract.json to `references/examples/`

#### Removed
- Removed `assets/example-extract.json` (moved to references/examples/)

## 2025-10-21

### bash-best-practices v1.1.0

#### Added
- Tree-sitter-based function analyzer (`scripts/analyze-shell-functions.py`)
  - Accurate AST parsing using tree-sitter (replaces regex-based approach)
  - Handles heredocs with braces correctly (previously failed with regex parser)
  - Supports both bash (.sh, .bash) and zsh (.zsh) files
  - Auto-installs dependencies via uv (tree-sitter, tree-sitter-bash)
  - PEP 723 inline script dependencies for zero-config usage
  - Tested on real codebases: 708 PowerShell functions, 326 macOS functions, 125 VM functions
  - Output format matches PowerShell extract.json for consistency
  - Fixed purpose extraction bug (skips shebangs, filters inline code comments)
- Comprehensive extract.json reference (`references/20-function-discovery-extract-json.md`)
  - Complete guide on when to use, setup, location best practices
  - All jq query patterns (semantic search, category browsing, parameter inspection)
  - Code commenting best practices for maximum discoverability
  - Agent workflow integration patterns
  - Pre-commit and CI/CD integration examples

#### Changed
- Updated SKILL.md with tree-sitter documentation and rationale for extract.json approach
- Function discovery workflow now recommends tree-sitter analyzer
- Added "When to Use extract.json" section with clear decision criteria
- Added agent workflow guidance (generate at session start or when function not found)
- Emphasized semantic search and precise extraction benefits

#### Removed
- `scripts/analyze-shell-functions.sh` (regex-based analyzer - replaced by tree-sitter version)
- `scripts/analyze-shell-functions-wrapper.sh` (no longer needed)

### zsh-best-practices v1.4.0

#### Added
- Tree-sitter-based function analyzer (`scripts/analyze-shell-functions.py`)
  - Same analyzer as bash-best-practices (handles both bash and zsh)
  - Supports .zsh, .sh, .bash files
  - Tested on real ZSH codebases (326 macOS functions)
- Comprehensive extract.json reference (`references/20-function-discovery-extract-json.md`)
  - Shared with bash-best-practices for consistency
  - Complete guide on setup, jq patterns, commenting best practices

#### Changed
- Updated SKILL.md with function discovery workflow
- Added agent guidance for when to generate extract.json
- Added quick start examples and jq query patterns

## 2025-10-20

### bash-best-practices v1.0.0

Initial release of the bash-best-practices skill providing comprehensive Bash scripting guidance with integrated linting and function discovery.

#### Added
- Complete Bash scripting guide (SKILL.md)
  - Function discovery workflow using metadata extraction
  - Lint-and-index pattern (always couple ShellCheck with metadata regeneration)
  - Quick decision tree pointing to 20 reference documents
  - Cross-platform focus (macOS, Linux, WSL)
  - Recommended script template with strict mode
  - Common pitfalls and solutions
- Function metadata generator (`scripts/analyze-shell-functions.sh`)
  - Extracts function names, locations (file:line), parameters
  - Infers function purpose from comments or naming patterns
  - Categorizes functions (display, core, test, export, install, service, helper)
  - Outputs extract.json for fast semantic search with jq
  - Adapted from ZSH version for Bash compatibility
- Combined workflow script (`scripts/lint-and-index.sh`)
  - Runs ShellCheck for linting
  - Regenerates extract.json for function metadata
  - Ensures metadata stays synchronized with code changes
  - Supports auto-fix mode and severity filtering
- ShellCheck configuration (`.shellcheckrc`)
  - Pragmatic defaults aligned with skill guidelines
  - Disables SC1090/SC1091 for dynamic sourcing
  - Enables additional checks for better quality
- Asset files
  - `shellcheck-suppression-guide.md` - When and how to suppress warnings
  - `tool-integration-guide.md` - Detailed workflow documentation comparing old (grep) vs new (metadata) approach
- 20 comprehensive reference documents covering all aspects of Bash scripting

#### Key Features
- **Metadata-first workflow**: Generate extract.json once, query with jq for instant function discovery
- **Token-efficient**: Read only needed functions using exact line numbers from metadata
- **Always synchronized**: Lint-and-index pattern prevents stale metadata
- **Cross-platform**: Works on macOS, Linux, and WSL
- **Semantic search**: Find functions by purpose, category, or parameters (not just name)

#### Updated
- **zsh-best-practices**: Added scope clarification - when to use ZSH vs Bash

### branch-synchronizer v1.0.0

Initial release of the branch-synchronizer skill providing intelligent branch synchronization with conflict-aware rebasing.

#### Added
- Core synchronization workflow
  - Fetch latest from remote branches and main
  - Auto-stash uncommitted changes before rebase
  - Intelligent rebase onto latest main/develop
  - Conflict detection with context-aware handling
  - Auto-restore stashed changes after successful rebase
- Dual execution modes
  - **Agent Mode**: Auto-abort on conflicts, preserve state, return exit code 1 for agent handling
  - **Interactive Mode**: Guide user through conflict resolution with helpful commands and continuation support
- Branch discovery system
  - Find branches by ticket pattern (PROJ-*, TICKET-*, etc.)
  - Detect if branch already merged to main (prevents unnecessary syncs)
  - Handle multiple matching branches (selects most recent by commit date)
  - Uses ticket patterns from `jira-analyzer.json` (project-local or global)
- Safety features
  - Never auto-push (requires manual review after rebase)
  - Preserve uncommitted changes with auto-stash
  - Validate branch existence before operations
  - Comprehensive error messages with actionable guidance
- Script architecture
  - `sync-branch.zsh` - Main entry point with CLI interface
  - `lib/config-functions.zsh` - Configuration hierarchy (project-local → global)
  - `lib/branch-functions.zsh` - Branch discovery and merge detection
  - `lib/sync-functions.zsh` - Core sync and rebase operations
- Enhanced error messages with context
  - Path validation with current directory and tips
  - Git repository checks with initialization guidance
  - Pattern matching errors with available ticket formats
  - Detached HEAD recovery steps
  - Branch listing with creation commands
  - Fetch/pull failures with diagnostic steps
- ZSH best practices implementation
  - Explicit global variable scoping with `typeset -g`
  - Strict mode throughout (`emulate -LR zsh`, `ERR_EXIT`, `NO_UNSET`, `PIPE_FAIL`)
  - Proper emulation scoping (`emulate -L` in libraries)
  - Safe JSON construction with `jq -n`
  - Cleanup traps for resource management
- Comprehensive documentation
  - SKILL.md with imperative voice, concise structure
  - references/usage-guide.md - 500+ lines of examples, workflows, and patterns
  - references/api-reference.md - Complete script API and JSON output format
  - references/integration-guide.md - CI/CD, git hooks, IDE integration patterns
  - references/troubleshooting.md - Common issues and solutions

**Design Philosophy**:
- Project-agnostic (works with any git repository)
- Context-aware conflict handling (agent vs interactive)
- Safety-first (never auto-push, validate before operations)
- User-friendly error messages with recovery steps

**Status**: Production ready with comprehensive documentation and full ZSH best practices compliance

---

### zsh-best-practices v1.3.0

Enhanced type patterns and syntax validation capabilities.

#### Added
- **`allowed_tools` metadata** for ZSH syntax validation
  - Added `allowed_tools: Bash(zsh -n *)` to YAML frontmatter
  - Enables automatic syntax checking of ZSH scripts
- **Integer boolean pattern** as idiomatic ZSH approach (02-typeset-and-scoping.md)
  - Documented `typeset -i flag=0` pattern with `(( ))` arithmetic tests
  - Explained why integers are more idiomatic than string booleans in ZSH
  - Added comparison examples (`(( found ))` vs `[[ "$found" == "true" ]]`)
  - Convention: 0 = false, 1 (or non-zero) = true
- **Explicit array declaration** best practice (02-typeset-and-scoping.md)
  - Documented pattern: `typeset -a arr` then `arr=()` (separate type from init)
  - Benefits: clarity, documentation, consistency with typed declarations
  - Example with loop population pattern
- **String substring extraction** with 1-based indexing (04-array-indexing.md)
  - Documented ZSH-native `${text[1,5]}` syntax (1-based, consistent with arrays)
  - Compared with Bash-style `${text:0:5}` syntax (0-based, inconsistent)
  - Recommended ZSH-native syntax for consistency with array indexing
  - Real-world examples with date parsing

#### Changed
- Enhanced references/02-typeset-and-scoping.md with integer boolean and explicit array patterns
- Enhanced references/04-array-indexing.md with string substring extraction guidance
- SKILL.md frontmatter now includes allowed_tools metadata

**Status**: Enhanced with idiomatic patterns and syntax validation support

---

### zsh-best-practices v1.2.0

Updated naming conventions to follow industry standards (POSIX, Google Shell Style Guide, Oh My Zsh) instead of custom conventions.

#### Changed
- **Variable naming conventions** updated to industry standards:
  - Regular variables: `lowercase_snake_case` (was `Mixed_Snake_Case`)
  - Constants & exports: `UPPER_SNAKE_CASE` (unchanged)
  - Private variables: `_leading_underscore` (unchanged)
  - Removed non-standard `CamelCase` recommendation for local variables
- **Function naming conventions** updated to industry standards:
  - Public functions: `lowercase_with_underscores` (was `lowerfirst_Snake_Case`)
  - Private functions: `_lowercase_with_underscores` (was `_lowerfirst_Snake_Case`)
- Updated SKILL.md examples to use industry-standard naming
  - Script template now uses `script_dir`, `tmp_dir` instead of `ScriptDir`, `TmpDir`
  - Added rule: "If it's your variable, lowercase it. If you export it or it's a constant, uppercase it."
- Updated references/01-naming-conventions.md with comprehensive industry standard documentation
  - Added POSIX standard references
  - Added Google Shell Style Guide references
  - Removed custom `Mixed_Snake_Case` convention
  - Enhanced examples with real-world patterns

**Context**: Previous conventions were based on custom patterns. New conventions match 99% of shell scripts in the wild (Linux kernel, Oh My Zsh, Google's codebase).

**Impact**: Skills developed using this guide now follow widely-recognized conventions, making them more recognizable to other developers.

---

### git-worktree-tools v1.0.0

Initial release of the git-worktree-tools skill providing git worktree lifecycle management with project-aware configuration syncing.

#### Added
- Core worktree lifecycle scripts
  - `create-worktree.zsh` - Create worktrees with automatic branch handling and config sync
  - `validate-worktree.zsh` - Check worktree state (VALID, INVALID, NOT_FOUND)
  - `remove-worktree.zsh` - Clean up worktrees with uncommitted change detection
  - `sync-configs.zsh` - Sync `.claude/`, `CLAUDE.local.md`, `.env` from main repo
- Library functions for custom integrations
  - `worktree-functions.zsh` - Core worktree operations (status checks, branch detection, listing)
  - `config-sync.zsh` - Configuration synchronization functions
  - `branch-utils.zsh` - Branch name parsing and ticket extraction
- Ticket extraction from branch names
  - Supports multiple ticket patterns: PROJ-*, TICKET-*, and generic PROJECT-123 format
  - Automatic extraction with `extract_ticket_number()` function
  - Branch name validation and generation utilities
- Black box operation design
  - All operations run from outside worktree directories
  - Avoids permission issues and maintains clear separation
  - No cd into worktree directories (safety-first approach)
- Configuration synchronization
  - Uses rsync for `.claude/` directory sync with `--delete-after`
  - Copies `CLAUDE.local.md` and `.env` if present
  - Skips missing files (not treated as errors)
- JSON output for programmatic integration
  - All scripts return structured JSON with status, paths, and metadata
  - Exit codes: 0 for success, 1 for errors
  - Quiet mode for scripting (`--quiet` flag)
- Comprehensive documentation
  - SKILL.md with overview, quick start, common workflow example
  - references/usage-guide.md with 750+ lines of examples and patterns
  - Complete script documentation with help messages
  - Library function reference with signatures

**Design Philosophy**:
- Worktrees created in sibling directory (`project.worktrees/NAME/`)
- Validation-first approach (always check state before operating)
- Project-aware (automatically syncs configurations)
- Branch-aware (extracts ticket numbers from branch names)
- Permission safe (operates from outside to avoid permission issues)

#### Fixed
- ZSH strict mode compatibility issues discovered during testing
  - Reserved variable name `status` (read-only in ZSH) renamed to `worktree_status`
  - Invalid trap signal `RETURN` (bash idiom) replaced with ZSH `always` block
  - All scripts now fully compatible with ZSH strict mode

**Status**: Production ready with comprehensive documentation and testing complete

---

### zsh-best-practices v1.1.0

Enhanced ZSH best practices skill with critical lessons learned from real-world usage.

#### Added
- **Reserved variable names documentation** (Critical Issue #6)
  - Documents ZSH read-only variables that cannot be assigned in strict mode
  - Common reserved names: `status`, `pipestatus`, `ERRNO`, `signals`, etc.
  - Detection patterns for code review
  - Added to critical issues checklist
  - Real-world example: `typeset status=` fails in strict mode
- **`always` block pattern for function-level cleanup**
  - ZSH-specific alternative to `trap` for function scope
  - Works reliably in all ZSH modes including strict mode
  - Pattern comparison table: `trap` vs `always` blocks
  - When to use each pattern (script-level vs function-level)
  - Common Bash idiom mistake: `trap ... RETURN` doesn't work in ZSH
  - Complete examples with temp file cleanup

#### Changed
- Updated SKILL.md common pitfalls section
  - Added Pitfall #5: Reserved Variable Names
  - Added Pitfall #6: Using `trap RETURN` (Bash idiom)
  - Updated code review section with new critical checks
- Enhanced 10-code-review-checklist.md
  - Added Critical Issue #6: Reserved/Read-Only Variable Names
  - Renumbered subsequent sections (7-12)
  - Updated quick reference with new checks
- Enhanced 09-common-patterns.md
  - Added "Function-Level Cleanup with `always` Block" section
  - Comparison table for `trap` vs `always` usage
  - Updated summary to mention both cleanup patterns

**Status**: Enhanced with real-world testing insights

---

### git-operations v1.0.0

Initial release of the git-operations skill providing safe git operations with styleable commit messages and comprehensive safety checks.

#### Added
- Safe commit operations with Git Safety Protocol enforcement
  - Authorship verification before amending commits
  - Push status checks to prevent rewriting public history
  - Comprehensive pre-commit validation
- Styleable commit messages with 6 built-in styles:
  - `conventional` - Standard format (feat:, fix:, docs:, etc.) [DEFAULT]
  - `pirate` - "Arr! Hoisted the new feature..."
  - `snarky` - "Obviously this needed attention..."
  - `emoji` - ✨ feat: with emoji prefixes
  - `minimal` - Plain messages without type prefixes
  - `corporate` - [SCOPE] Category: Description format
- Configuration via CLAUDE.md/CLAUDE.local.md
  - `Commit style:` - Select commit message style
  - `Commit attribution:` - Control attribution footers (none/claude/custom)
  - Project-local config overrides user-wide config
- Branch protection system
  - Blocks force-push to main/master (always)
  - Allows force-push to feature branches with warnings
  - Uses `--force-with-lease` for safer force-pushes
- Pre-commit hook handling
  - Smart amend logic for hook-modified files
  - Safety checks: authorship + push status
  - Falls back to new commit when amend is unsafe
- Push safety checks
  - Repository, remote, and branch validation
  - Upstream tracking verification
  - Ahead/behind status checks
  - Detached HEAD detection
- Single entry point design
  - `git-ops.zsh` script for all operations
  - Modular library structure (lib/commit-helpers.zsh, lib/safety-checks.zsh, lib/style-engine.zsh)
  - Clear error messages with actionable guidance
- Comprehensive documentation
  - SKILL.md with usage examples and integration patterns
  - references/commit-styles.md - Complete style library and transformations
  - references/safety-protocol.md - Detailed safety rules and decision trees

**Status**: Production ready with comprehensive documentation

---

### powershell-pragmatic v1.0.0

Initial release of the powershell-pragmatic skill providing pragmatic PowerShell coding patterns.

#### Added
- Pragmatic PowerShell coding guide
- Production-ready PowerShell patterns
- Error handling and logging strategies
- PSScriptAnalyzer integration
- Reusability and modularity patterns
- ASCII-only output requirements for user-facing text

**Status**: Complete reference documentation

---

### zsh-best-practices v1.0.0

Initial release providing comprehensive ZSH scripting guide for macOS.

#### Added
- Comprehensive ZSH scripting guide for macOS
- 10 comprehensive reference guides:
  - 01-naming-conventions.md
  - 02-typeset-and-scoping.md
  - 03-word-splitting-and-quoting.md
  - 04-array-indexing.md
  - 05-strict-mode-and-options.md
  - 06-json-processing.md
  - 07-environment-variables.md
  - 08-macos-specifics.md
  - 09-common-patterns.md
  - 10-code-review-checklist.md
- Critical differences from Bash documentation
- JSON processing best practices (avoiding jq pitfalls)
- macOS-specific considerations (BSD vs GNU tools)

**Status**: Complete reference documentation

---

### skill-tester v1.0.0

Initial release providing meta skill for testing and validating skills under development.

#### Added
- Meta skill for testing and validating skills under development
- Automated skill installation to .claude/skills/ (install-skill-for-testing.zsh)
- Skill validation tool (validate-skill.py)
- Testing workflow documentation
- Claude Code restart guidance
- Project structure understanding

**Status**: Functional and ready for use

---

### youtube-music-updater v1.0.0

Initial release providing YouTube Music desktop app update automation.

#### Added
- Update YouTube Music desktop app from GitHub releases
- Version checking and comparison
- App restart and quarantine attribute removal (macOS)
- Handles pear-devs GitHub releases
- macOS focused

**Status**: Functional for macOS
