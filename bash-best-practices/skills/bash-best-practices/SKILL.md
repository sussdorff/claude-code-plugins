---
name: bash-best-practices
description: This skill should be used when writing, reviewing, debugging, or refactoring Bash shell scripts for cross-platform use (macOS, Linux, WSL). Combines Bash coding best practices with ShellCheck linting integration. Use when migrating from ZSH to Bash, writing new Bash scripts, or reviewing existing code. Includes automated function discovery with metadata extraction. Always runs ShellCheck when reviewing or writing Bash code. Do NOT use for ZSH scripts (use zsh-best-practices instead) or POSIX sh scripts.
allowed_tools: Bash(shellcheck *)
---

# Bash Best Practices

Comprehensive guide for writing robust, maintainable, portable Bash scripts with integrated ShellCheck linting.

## Overview

Write production-ready Bash scripts that work consistently across macOS, Linux, and WSL environments. Focus on strict error handling, proper variable scoping, and cross-platform compatibility.

**Philosophy**: Write portable, predictable Bash code that fails fast and provides clear error messages. Prefer explicit patterns over clever tricks.

**Linting Requirement**: Always run ShellCheck when reviewing or writing Bash code. See the "Code Linting with ShellCheck" section for workflow integration.

## Bash Version Requirements

### Version Policy

**Development Target**: Bash 5.x (latest stable)
- Write code using modern Bash 5 features and idioms
- Leverage performance improvements and enhanced functionality
- Follow current best practices and patterns

**Minimum Requirement**: Bash 4.0+
- Scripts must run on Bash 4.0 as the lowest supported version
- Required for `mapfile`/`readarray` support (critical for safe array operations)
- Avoid Bash 5-only features unless providing fallbacks

### Platform Landscape

| Platform | Default Version | Status | Action Required |
|----------|----------------|--------|-----------------|
| **macOS** | 3.2.57 (2007) | ❌ Too old | `brew install bash` |
| **Linux (modern)** | 4.4 - 5.x | ✅ Usually OK | Varies by distro |
| **Windows (Git Bash)** | 4.4+ | ✅ Usually OK | Rarely needs update |
| **WSL** | 5.x | ✅ Current | No action needed |

### Why macOS Ships Ancient Bash

macOS includes Bash 3.2.57 from 2007 because later versions use GPLv3 license, which Apple avoids. **Never expect macOS users to have modern Bash by default.**

### Upgrade Instructions

**macOS** (most common issue):
```bash
# Install latest Bash (5.x) via Homebrew
brew install bash

# Verify installation
/opt/homebrew/bin/bash --version  # Apple Silicon
/usr/local/bin/bash --version     # Intel

# Scripts automatically use newer version with #!/usr/bin/env bash
# System default /bin/bash (3.2) remains untouched for compatibility
```

**Linux**:
```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install bash

# RHEL/CentOS/Fedora
sudo yum install bash

# Verify
bash --version
```

**Windows**:
- Git Bash: Update Git for Windows (includes Bash 4.4+)
- WSL: `sudo apt update && sudo apt upgrade bash`

### Version Check Pattern

Always include version checks in scripts that require Bash 4+:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Require Bash 4.0+ for mapfile support
if [[ "${BASH_VERSINFO[0]}" -lt 4 ]]; then
    echo "Error: Bash 4.0+ required (current: ${BASH_VERSION})" >&2
    echo "Install: brew install bash  (macOS)" >&2
    exit 1
fi
```

### Feature Compatibility

| Feature | Bash 3.2 | Bash 4.0+ | Bash 5.0+ |
|---------|----------|-----------|-----------|
| `mapfile`/`readarray` | ❌ | ✅ | ✅ |
| Associative arrays | ❌ | ✅ | ✅ |
| `;&` and `;;&` in case | ❌ | ✅ | ✅ |
| `**` globstar | ❌ | ✅ | ✅ |
| Negative array indices | ❌ | ❌ | ✅ |
| `wait -n` (wait any) | ❌ | ❌ | ✅ |

**Recommendation**: Use Bash 4.0+ features freely with version checks. Avoid Bash 5-only features unless providing fallbacks or documenting the requirement clearly.

## When to Use Bash (and When Not To)

### Bash is Excellent For

- **System automation**: File operations, process management, service orchestration
- **Glue scripts**: Connecting command-line tools together
- **CI/CD pipelines**: Build automation, deployment scripts
- **Quick prototyping**: Rapid iteration on system tasks
- **Environment setup**: Configuration, installation, bootstrapping

### Consider Alternatives When

- **Complex text processing** → Use `awk`, `perl`, or `sed`
  - Multi-pass parsing, complex transformations, CSV/TSV manipulation
- **Structured data (JSON/XML/YAML)** → Use `jq`, `yq`, or Python
  - Schema validation, deep transformations, API interaction
- **Heavy computation** → Use Python, Go, or compiled languages
  - Math operations, algorithms, data analysis
- **Complex business logic** → Use Python, Ruby, or other high-level languages
  - Object-oriented design, type safety, unit testing frameworks
- **Cross-platform GUI apps** → Use Python, Electron, or native frameworks
- **Performance-critical tasks** → Use Go, Rust, C, or compiled languages

**Rule of thumb**: Focus on **complexity, not line count**. Bash is excellent for orchestration (calling tools in sequence) even if scripts are long. Consider alternatives when individual functions become complex, need data structures beyond arrays, or implement business logic.

→ **Need detailed guidance?** See [14-tool-selection.md](references/14-tool-selection.md)

## Quick Decision Tree

Reference the appropriate guide based on current needs:

- **Is Bash the right tool?** → [14-tool-selection.md](references/14-tool-selection.md)
- **Organizing functions in libraries?** → [15-function-libraries.md](references/15-function-libraries.md)
- **Need script templates?** → [16-script-templates.md](references/16-script-templates.md)
- **Common pitfalls to avoid?** → [17-common-pitfalls.md](references/17-common-pitfalls.md)
- **CI/CD integration?** → [18-ci-cd-integration.md](references/18-ci-cd-integration.md)
- **Pre-commit hooks?** → [19-pre-commit-hooks.md](references/19-pre-commit-hooks.md)
- **Migrating from ZSH?** → [01-bash-vs-zsh.md](references/01-bash-vs-zsh.md)
- **Script initialization/strict mode?** → [02-strict-mode.md](references/02-strict-mode.md) - Edge cases, 4 pitfalls, 3 variations (paranoid/relaxed/debug)
- **Variable scope problems?** → [03-variable-scoping.md](references/03-variable-scoping.md)
- **Array indexing/iteration issues?** → [04-arrays.md](references/04-arrays.md) - Slicing, associative arrays (Bash 4+), 6 reusable patterns, 5 specific pitfalls
- **Path manipulation needed?** → [05-path-manipulation.md](references/05-path-manipulation.md)
- **Error handling patterns?** → [06-error-handling.md](references/06-error-handling.md)
- **Quoting/expansion confusion?** → [07-quoting-and-expansion.md](references/07-quoting-and-expansion.md)
- **Need common patterns/snippets?** → [08-common-patterns.md](references/08-common-patterns.md)
- **How to use ShellCheck?** → [09-shellcheck-integration.md](references/09-shellcheck-integration.md)
- **What does code review check?** → [10-code-review-checklist.md](references/10-code-review-checklist.md) - 100+ item checklist across 10 categories, pattern checks, anti-patterns, review workflow
- **IDE setup/hooks?** → [11-development-environment.md](references/11-development-environment.md)
- **When to suppress ShellCheck warnings?** → [12-shellcheck-suppression.md](references/12-shellcheck-suppression.md)
- **Function discovery workflow?** → [13-tool-integration.md](references/13-tool-integration.md)
- **extract.json setup and usage?** → [20-function-discovery-extract-json.md](references/20-function-discovery-extract-json.md)

## Critical Differences from ZSH

Bash differs from ZSH in several important ways:

### 1. Word Splitting by Default

```bash
# Bash: SPLITS on whitespace by default
var="foo bar"
for word in $var; do echo "$word"; done  # Two iterations

# ZSH: NO splitting by default
var="foo bar"
for word in $var; do echo "$word"; done  # ONE iteration
```

**→ Bash requires careful quoting to prevent word splitting**
**→ See:** [07-quoting-and-expansion.md](references/07-quoting-and-expansion.md)

### 2. 0-Based Array Indexing

Bash uses 0-based indexing (first element is `${arr[0]}`), while ZSH defaults to 1-based.

**→ See:** [04-arrays.md](references/04-arrays.md) for slicing, associative arrays, patterns, and pitfalls

### 3. Different Variable Scoping

Bash uses `local` and `declare` instead of ZSH's `typeset`:

```bash
# Bash
my_function() {
    local counter=0
    local -i number=42        # Integer
    local -a items=()         # Array
    declare -r CONST="value"  # Read-only
}
```

**→ See:** [03-variable-scoping.md](references/03-variable-scoping.md)

### 4. Strict Mode Instead of emulate

Bash uses `set -euo pipefail` for strict behavior (vs ZSH's `emulate -LR zsh`).

**→ See:** [02-strict-mode.md](references/02-strict-mode.md) for edge cases, pitfalls, and variations

### 5. Different Path Manipulation

```bash
# ZSH: Special parameter expansions
script_dir="${${(%):-%x}:A:h}"

# Bash: Standard commands
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
```

**→ See:** [05-path-manipulation.md](references/05-path-manipulation.md)

## Script Templates and Common Pitfalls

→ **Script templates**: See [16-script-templates.md](references/16-script-templates.md) for production-ready templates
→ **Common pitfalls**: See [17-common-pitfalls.md](references/17-common-pitfalls.md) for frequent mistakes and solutions

## Function Discovery Workflow

**IMPORTANT: For codebases with 100+ functions, generate extract.json at session start or when function discovery fails.**

Use a metadata-first approach for efficient function discovery. extract.json provides semantic search, category browsing, and precise extraction - reducing discovery from 10+ grep iterations to 2-3 structured queries.

### When to Use extract.json

✅ **Use when:**
- Large codebase (100+ functions across 5+ files)
- Starting new session (fresh context, need to understand structure)
- Function not found (grep fails, need better discovery)
- Semantic search needed (find by purpose, not just name)
- **Real-world:** PowerShell (708 functions), macOS (326 functions), VM (125 functions)

❌ **Skip when:**
- Small codebase (< 20 functions in 1-2 files)
- Known function name and location

### Quick Start

```bash
# 1. Generate (tree-sitter based, handles heredocs, bash/zsh)
uv run bash-best-practices/scripts/analyze-shell-functions.py \
    --path ./scripts \
    --output extract.json

# 2. Semantic search - finds by purpose, even if keyword not in name
jq '.index | to_entries[] | select(.value.purpose | test("backup"; "i")) | .key' extract.json

# 3. Get Read parameters (KEY PATTERN - use this!)
jq '.index."function_name" | {file_path: .file, offset: .start, limit: .size}' extract.json
# Returns: {"file_path": "/path/script.sh", "offset": 42, "limit": 25}
# Use directly in Read tool - zero guessing, precise extraction

# 4. Category browsing
jq '.categories.test[]' extract.json  # All test functions
```

### Agent Workflow

**Recommended pattern:**

1. **Session start or function not found** → Generate extract.json
2. **Discover** → Semantic search or category browse (jq)
3. **Extract params** → Get file_path, offset, limit (jq)
4. **Read** → Use exact parameters (Read tool)
5. **Regenerate** → After code changes or if stale

**Result:** 2-3 tool calls vs 10+ with grep. Precise, fast, semantic.

### Comprehensive Guide

**→ See:** [20-function-discovery-extract-json.md](references/20-function-discovery-extract-json.md) for:
- Setup and location best practices (where to put extract.json)
- When to regenerate (staleness management)
- All jq query patterns (semantic search, categories, parameters)
- Code commenting best practices (maximize discoverability)
- Integration workflows (pre-commit, CI/CD)

## Development Environment Setup (Optional)

For enhanced IDE experience with real-time feedback, install bash-language-server and configure the editor for ShellCheck integration.

**→ See:** [11-development-environment.md](references/11-development-environment.md) for IDE setup, pre-commit hooks, CI/CD integration, and editor-specific configurations

## Code Linting with ShellCheck

Always run ShellCheck when reviewing or writing Bash code. Use the combined lint-and-index workflow to keep validation synchronized with function metadata.

### Quick Workflow

```bash
# Recommended: Use the combined script
bash bash-best-practices/scripts/lint-and-index.sh --path .

# With specific severity level
bash bash-best-practices/scripts/lint-and-index.sh --path . --severity error

# Standalone ShellCheck (when extract.json doesn't need regeneration)
shellcheck --severity=warning script.sh
```

### When to Run

Run lint-and-index after:
- Making changes to any Bash script
- Refactoring code
- Before committing changes
- When switching branches (if code differs)

### Configuration

Use the provided `.shellcheckrc` configuration for consistent linting:

```bash
# Copy to project root
cp bash-best-practices/assets/.shellcheckrc .shellcheckrc

# Or use directly
shellcheck --config=bash-best-practices/assets/.shellcheckrc script.sh

# Or symlink for automatic detection
ln -s bash-best-practices/assets/.shellcheckrc .shellcheckrc
```

The configuration file disables problematic checks and enables useful optional checks. Review `assets/.shellcheckrc` for details.

### Common Issues

**Most frequent violations:**
- SC2086: Unquoted variable expansions
- SC2155: Declare and assign separately to avoid masking return values
- SC2164: Use `cd ... || exit` in case cd fails
- SC2046: Quote to prevent word splitting
- SC2034: Variable appears unused (often indicates typos)

**→ See:** [09-shellcheck-integration.md](references/09-shellcheck-integration.md) for detailed ShellCheck usage, configuration, CI/CD integration, and suppression guidelines
**→ See:** [12-shellcheck-suppression.md](references/12-shellcheck-suppression.md) for when and how to suppress warnings
**→ See:** [13-tool-integration.md](references/13-tool-integration.md) for complete workflow integration patterns

## Naming Conventions

### Files

- **Style:** `lower-kebab-case` for filenames
- **Extension:** `.sh` for all Bash scripts
- **Shebang:** `#!/usr/bin/env bash` for portability

```bash
# Files
fetch-ticket.sh
sync-branch.sh
configure-database.sh
```

### Variables

**Industry Standard (Google Shell Style Guide):**

```bash
# Constants & Environment Variables: UPPER_SNAKE_CASE
readonly SCRIPT_DIR="/path/to/script"
export API_URL="https://api.example.com"
declare -r MAX_RETRIES=3

# Regular variables: lowercase_snake_case
local ticket_id="CH2-12345"
local output_directory="/tmp/output"
local current_user="alice"

# Private/internal variables: _leading_underscore (optional)
local _internal_state="initialized"
local _temp_file="/tmp/temp"
```

### Functions

```bash
# Public functions: lowercase_with_underscores
fetch_ticket_data() {
    local ticket="$1"
    # ...
}

configure_api() {
    local instance="$1"
    # ...
}

# Private functions: _leading_underscore (optional)
_validate_json() {
    local file="$1"
    # ...
}
```

**→ See:** [01-bash-vs-zsh.md](references/01-bash-vs-zsh.md)

## Key Principles Summary

### 1. Be Explicit and Strict

```bash
# Good - Fail fast
set -euo pipefail

# Good - Clear types
declare -i counter=0
declare -r CONST="value"
declare -a items=()
```

### 2. Quote Everything

```bash
# Good - Always quote variables
local file="$1"
if [[ -f "$file" ]]; then
    cat "$file"
fi
```

### 3. Use [[ Over [

```bash
# Good - [[ is safer and more powerful
if [[ $var =~ ^[0-9]+$ ]]; then
    echo "Number: $var"
fi
```

### 4. Handle Errors Explicitly

```bash
# Good - Check return codes
if ! command_that_might_fail; then
    echo "Error: Command failed" >&2
    return 1
fi
```

### 5. Clean Up Resources

```bash
# Good - Automatic cleanup
trap cleanup EXIT
```

### 6. Code Review & Quality Checks

When writing or reviewing Bash scripts, check for common Bash bugs and always run ShellCheck. Use the comprehensive production checklist for thorough reviews.

**→ See:** [10-code-review-checklist.md](references/10-code-review-checklist.md) for 100+ item checklist across critical/important/style/security/performance categories

## Cross-Platform Considerations

### Write Once, Run Everywhere

```bash
# ✅ GOOD - Portable
local user
user="$(whoami)"

# ✅ GOOD - Works on BSD (macOS) and GNU (Linux)
find . -name "*.log" -type f -print0 | xargs -0 rm -f

# ❌ BAD - GNU-specific
find . -name "*.log" -delete  # Not on all systems
```

### Platform Detection

```bash
case "$(uname -s)" in
    Darwin)
        echo "macOS"
        ;;
    Linux)
        echo "Linux"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        echo "Windows (Git Bash/WSL)"
        ;;
esac
```

## Resources

### Scripts (Workflow Automation)

- `scripts/analyze-shell-functions.py` - Tree-sitter-based function analyzer (handles bash/zsh, heredocs, complex syntax)

**Usage**:
```bash
# Generate extract.json (recommended at session start for large codebases)
uv run bash-best-practices/scripts/analyze-shell-functions.py --path ./scripts --output extract.json
```

**Requirements**: `uv` (auto-installs tree-sitter dependencies on first run)

### Assets (Configuration)

- `assets/.shellcheckrc` - ShellCheck configuration for this skill

### References (Deep Dives)

For comprehensive coverage of specific topics:

- `references/01-bash-vs-zsh.md` - Critical differences when migrating from ZSH
- `references/02-strict-mode.md` - Understanding `set -euo pipefail` and variations
- `references/03-variable-scoping.md` - `local` vs `declare`, scoping rules
- `references/04-arrays.md` - Array operations, iteration, pitfalls
- `references/05-path-manipulation.md` - dirname, basename, realpath patterns
- `references/06-error-handling.md` - Error detection, trap, exit codes
- `references/07-quoting-and-expansion.md` - When to quote, word splitting rules
- `references/08-common-patterns.md` - Reusable patterns and templates
- `references/09-shellcheck-integration.md` - Advanced ShellCheck usage
- `references/10-code-review-checklist.md` - Complete review checklist
- `references/11-development-environment.md` - IDE setup, editor configurations
- `references/12-shellcheck-suppression.md` - When and how to suppress warnings
- `references/13-tool-integration.md` - Detailed guide on analyzer + ShellCheck workflow
- `references/14-tool-selection.md` - When to use Bash vs alternatives (awk, Python, jq, etc.)
- `references/15-function-libraries.md` - Organizing reusable functions in lib/ directories, sourcing patterns
- `references/16-script-templates.md` - Production-ready script templates for common scenarios
- `references/17-common-pitfalls.md` - Frequent mistakes and how to avoid them
- `references/18-ci-cd-integration.md` - GitHub Actions, GitLab CI, Jenkins, CircleCI examples
- `references/19-pre-commit-hooks.md` - Automated validation with pre-commit framework and Git hooks
- `references/20-function-discovery-extract-json.md` - **Comprehensive extract.json guide** (setup, jq patterns, commenting best practices)

### External Resources

- **Google Shell Style Guide**: https://google.github.io/styleguide/shellguide.html
- **ShellCheck**: https://www.shellcheck.net/
- **ShellCheck GitHub**: https://github.com/koalaman/shellcheck
- **Bash Reference Manual**: https://www.gnu.org/software/bash/manual/
- **Bash Pitfalls**: https://mywiki.wooledge.org/BashPitfalls

## Quick Reference

### Before Writing Code

1. Start with the recommended template (includes strict mode)
2. **Run ShellCheck** on existing code before modifying
3. Check if functionality exists in coreutils/standard commands
4. Consider cross-platform compatibility (macOS/Linux/WSL)

### Script Checklist

- [ ] Starts with `#!/usr/bin/env bash`
- [ ] Includes `set -euo pipefail`
- [ ] Uses `readonly` for script metadata (SCRIPT_DIR, SCRIPT_NAME)
- [ ] Has cleanup function with `trap cleanup EXIT`
- [ ] Uses `local` for all function variables
- [ ] Quotes all variable expansions: `"$var"`
- [ ] Uses `[[` instead of `[` for conditionals
- [ ] Proper array iteration: `"${array[@]}"`
- [ ] Checks command return codes explicitly
- [ ] Has error messages to stderr: `>&2`
- [ ] **Passes ShellCheck with no errors**

### After Writing/Modifying Code

1. **Run lint-and-index** on modified files
   ```bash
   bash bash-best-practices/scripts/lint-and-index.sh --path .
   ```
2. Fix all error-level violations
3. Address warning-level violations when possible
4. Document any intentional warning suppressions
5. Verify extract.json is updated (function count should be accurate)
6. Test on target platforms (macOS, Linux, WSL)

### Common Mistakes to Avoid

- ❌ Not using strict mode (`set -euo pipefail`)
- ❌ Unquoted variables (`$var` instead of `"$var"`)
- ❌ Using `[` instead of `[[`
- ❌ Global variables in functions (missing `local`)
- ❌ Incorrect array syntax (`${arr[@]}` vs `"${arr[@]}"`)
- ❌ Not checking command return codes
- ❌ Using ZSH-specific syntax
- ❌ Skipping ShellCheck
- ❌ Ignoring cross-platform differences
- ❌ Unsafe `cd` operations (`cd dir` vs `cd dir || exit`)
