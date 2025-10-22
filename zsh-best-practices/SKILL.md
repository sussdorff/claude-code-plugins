---
name: zsh-best-practices
description: This skill should be used when writing, reviewing, debugging, or refactoring ZSH shell scripts on macOS. Use for macOS system administration scripts, maintaining existing ZSH scripts, or projects leveraging ZSH-specific features. Includes automated function discovery with metadata extraction. For new cross-platform scripts, use bash-best-practices instead.
allowed_tools: Bash(zsh -n *)
---

# ZSH Best Practices

Comprehensive guide for writing robust, maintainable ZSH scripts with focus on macOS compatibility and modern patterns.

## When to Use This Skill

**Use zsh-best-practices when**:
- Writing macOS system administration scripts
- Maintaining existing ZSH scripts
- Writing scripts that intentionally leverage ZSH-specific features (associative arrays, advanced globbing, etc.)
- Interactive shell configuration (oh-my-zsh, dotfiles)
- ZSH is the default/preferred shell in your environment

**Use bash-best-practices instead when**:
- Writing new cross-platform scripts (Linux, macOS, WSL)
- Need maximum portability across different systems
- Targeting servers/containers (Bash more universally available)
- Working in environments where ZSH might not be installed

**Migration path**: If migrating ZSH scripts to Bash, see bash-best-practices reference `01-bash-vs-zsh.md` for critical differences.

## Quick Decision Tree

Reference the appropriate guide based on your current need:

- **File/variable naming issues?** → [01-naming-conventions.md](references/01-naming-conventions.md)
- **Variable scope problems?** → [02-typeset-and-scoping.md](references/02-typeset-and-scoping.md)
- **Word splitting confusion?** → [03-word-splitting-and-quoting.md](references/03-word-splitting-and-quoting.md)
- **Array indexing errors?** → [04-array-indexing.md](references/04-array-indexing.md)
- **Script options/strict mode?** → [05-strict-mode-and-options.md](references/05-strict-mode-and-options.md)
- **JSON processing failing?** → [06-json-processing.md](references/06-json-processing.md)
- **Need environment variables?** → [07-environment-variables.md](references/07-environment-variables.md)
- **macOS-specific issues?** → [08-macos-specifics.md](references/08-macos-specifics.md)
- **Common patterns/snippets?** → [09-common-patterns.md](references/09-common-patterns.md)
- **What does code review check?** → [10-code-review-checklist.md](references/10-code-review-checklist.md)
- **extract.json setup and usage?** → [20-function-discovery-extract-json.md](references/20-function-discovery-extract-json.md)

## Function Discovery Workflow

**IMPORTANT: For codebases with 100+ functions, generate extract.json at session start or when function discovery fails.**

Use extract.json for semantic search and precise function extraction in large ZSH codebases.

### Quick Start

```bash
# 1. Generate (handles both bash and zsh files)
uv run zsh-best-practices/scripts/analyze-shell-functions.py \
    --path ./scripts \
    --output extract.json

# 2. Semantic search - finds by purpose
jq '.index | to_entries[] | select(.value.purpose | test("backup"; "i")) | .key' extract.json

# 3. Get Read parameters (use directly in Read tool)
jq '.index."function_name" | {file_path: .file, offset: .start, limit: .size}' extract.json
```

### Agent Workflow

1. **Session start or function not found** → Generate extract.json
2. **Discover** → Semantic search or category browse (jq)
3. **Extract params** → Get file_path, offset, limit (jq)
4. **Read** → Use exact parameters (Read tool)

**Result:** 2-3 tool calls vs 10+ with grep.

**→ See:** [20-function-discovery-extract-json.md](references/20-function-discovery-extract-json.md) for complete guide (setup, jq patterns, commenting best practices)

## Critical Differences from Bash

ZSH differs from Bash in several important ways:

### 1. No Word Splitting by Default

```zsh
# Bash: splits on whitespace
var="foo bar"
for word in $var; do echo "$word"; done  # Two iterations

# ZSH: NO splitting by default
var="foo bar"
for word in $var; do echo "$word"; done  # ONE iteration

# ZSH: Explicit splitting with ${=var}
for word in ${=var}; do echo "$word"; done  # Two iterations
```

**→ See:** [03-word-splitting-and-quoting.md](references/03-word-splitting-and-quoting.md)

### 2. 1-Based Array Indexing

```zsh
# Bash: 0-based
arr=("first" "second")
echo "${arr[0]}"  # "first"

# ZSH: 1-based (default)
arr=("first" "second")
echo "${arr[1]}"  # "first"
echo "${arr[0]}"  # empty!
```

**→ See:** [04-array-indexing.md](references/04-array-indexing.md)

### 3. Different Variable Scoping

ZSH uses dynamic scoping and provides powerful `typeset` for variable management:

```zsh
# Prefer typeset over local
my_Function() {
    typeset -i counter=0        # Integer
    typeset -a items=()         # Array
    typeset -A config=()        # Associative array
    typeset -r CONST="value"    # Read-only
}
```

**→ See:** [02-typeset-and-scoping.md](references/02-typeset-and-scoping.md)

### 4. emulate for Consistency

User's `.zshrc` can change default behavior. Always start scripts with:

```zsh
#!/usr/bin/env zsh
emulate -LR zsh
```

This resets all options to ZSH defaults, ensuring consistent behavior.

**→ See:** [05-strict-mode-and-options.md](references/05-strict-mode-and-options.md)

## Common Pitfalls

### Pitfall 1: Pipes Create Subshells (Variables Lost)

```zsh
# ❌ WRONG - counter stays 0
counter=0
echo "data" | while read line; do
    counter=$((counter + 1))
done
echo "$counter"  # Still 0!

# ✅ CORRECT - Load into array first
local -a lines
while IFS= read -r line; do
    lines+=("$line")
done < <(command)

counter=0
for line in "${lines[@]}"; do
    counter=$((counter + 1))
done
echo "$counter"  # Correct value
```

**→ See:** [06-json-processing.md](references/06-json-processing.md)

### Pitfall 2: Off-By-One Array Errors

```zsh
# ❌ WRONG - bash thinking
arr=("a" "b" "c")
echo "${arr[0]}"  # empty in ZSH!

# ✅ CORRECT - ZSH is 1-based
echo "${arr[1]}"  # "a"
```

### Pitfall 3: Forgetting Quotes

```zsh
# ❌ WRONG - word splitting in bash mode
file="my file.txt"
touch $file  # Creates "my" and "file.txt"

# ✅ CORRECT - always quote
touch "$file"  # Creates "my file.txt"
```

### Pitfall 4: Global Variable Leakage

```zsh
# ❌ WRONG - accidental global
my_Function() {
    result="value"  # Global!
}

# ✅ CORRECT - explicit scope
my_Function() {
    typeset result="value"  # Local to function
}
```

Enable warnings:
```zsh
setopt warn_create_global
```

### Pitfall 5: Reserved Variable Names

```zsh
# ❌ WRONG - using reserved variable
check_status() {
    typeset status=$(git status)  # Error: read-only variable!
}

# ✅ CORRECT - different name
check_status() {
    typeset git_status=$(git status)  # Works fine
}
```

**Common reserved variables:**
- `status` - Exit status of last pipeline
- `pipestatus` - Array of pipeline exit statuses
- `ERRNO` - Last system error number
- `signals` - Array of signal names

**→ See:** [10-code-review-checklist.md](references/10-code-review-checklist.md)

### Pitfall 6: Using `trap RETURN` (Bash idiom)

```zsh
# ❌ WRONG - Bash idiom that fails in ZSH
my_function() {
    typeset temp=$(mktemp)
    trap "rm -f '$temp'" RETURN  # Error: undefined signal!
    # ...
}

# ✅ CORRECT - ZSH always block
my_function() {
    typeset temp=$(mktemp)
    {
        # ... function code ...
    } always {
        rm -f "$temp"  # Runs on ALL exits
    }
}
```

**→ See:** [09-common-patterns.md](references/09-common-patterns.md)

## Recommended Script Template

Use this template as a starting point for new ZSH scripts:

```zsh
#!/usr/bin/env zsh
#
# Script: my-script.zsh
# Description: Brief description of what this script does
# Usage: my-script.zsh [OPTIONS] <args>
# Requires: jq, curl (list dependencies)

# Reset to known ZSH defaults
emulate -LR zsh

# Enable strict error handling
setopt ERR_EXIT       # Exit on error
setopt ERR_RETURN     # Return on error in functions
setopt NO_UNSET       # Error on undefined variables
setopt PIPE_FAIL      # Fail if any command in pipeline fails

# Enable useful options
setopt EXTENDED_GLOB  # Extended pattern matching
setopt NULL_GLOB      # Don't error on no glob matches

# Script information (ZSH-specific, works when sourced)
typeset -r script_path="${(%):-%x}"
typeset -r script_dir="${${(%):-%x}:A:h}"
typeset -r script_name="${${(%):-%x}:t}"

# Cleanup function
cleanup() {
    # Remove temporary files
    if [[ -n "${tmp_dir:-}" ]] && [[ -d "$tmp_dir" ]]; then
        rm -rf "$tmp_dir"
    fi
}

# Register cleanup for all exit scenarios
trap cleanup EXIT INT TERM

# Main script logic
main() {
    # Check arguments
    if [[ $# -lt 1 ]]; then
        echo "Usage: $script_name <arg>" >&2
        return 1
    fi

    # Create temporary directory
    typeset -r tmp_dir=$(mktemp -d -t "${script_name}-XXXXXX")

    # Your logic here
    typeset input="$1"
    echo "Processing: $input"

    # ...

    return 0
}

# Run main with all arguments
main "$@"
```

### Template Design Rationale

1. **`emulate -LR zsh`**: Ensures consistent behavior regardless of `.zshrc` configuration
2. **Strict error handling**: Catches errors early
3. **`typeset -r`**: Read-only constants for script metadata
4. **`trap cleanup EXIT`**: Automatic resource cleanup
5. **`${(%):-%x}`**: ZSH-specific way to get script path (works when sourced)
6. **Temporary directory**: Safe location for temp files with automatic cleanup

## When emulate Is Critical vs Nice-to-Have

### Critical (Always Use)

- Scripts that will be sourced into user's shell
- Scripts run by end-users (unknown environment)
- Library scripts used by multiple projects
- System scripts with strict requirements

### Nice-to-Have (Recommended)

- Scripts that spawn as new processes (get fresh ZSH anyway)
- Scripts using `set -euo pipefail` (already strict)
- Internal-only scripts in controlled environments

**Recommendation:** Include it in the template. It's a one-line safety guarantee that costs nothing.

## File Extensions and Shebangs

### File Extensions

**Recommendation:** Use `.zsh` for all ZSH scripts

```zsh
# All use .zsh extension
fetch-ticket.zsh          # Executable
jira-handler.zsh          # Executable
utility-functions.zsh     # Library
```

**Why:** Immediately identifies ZSH scripts, consistent regardless of executable vs library.

**→ See:** [01-naming-conventions.md](references/01-naming-conventions.md)

### Shebang

**Recommendation:** Use `#!/usr/bin/env zsh` for portability

```zsh
#!/usr/bin/env zsh
# Portable - finds zsh in PATH
```

**Exception:** Use `#!/bin/zsh` for installers and Recovery mode scripts

**→ See:** [08-macos-specifics.md](references/08-macos-specifics.md)

## Naming Conventions

### Files

- **Style:** `lower-kebab-case` for filenames
- **Extension:** `.zsh` for all ZSH scripts
- **Variables:** `lower_snake_case`

```zsh
# Files
fetch-ticket-standalone.zsh
configure-database.zsh

# Variables
typeset ticket_id="CH2-12345"
typeset output_directory="/tmp/output"
```

### Variables

**Industry Standard (POSIX/Google Style Guide):**

```zsh
# Constants & Environment Variables: UPPER_SNAKE_CASE
typeset -r SCRIPT_DIR="/path/to/script"
export JIRA_API_URL="https://api.example.com"
typeset -g MAX_RETRIES=3

# Regular variables: lowercase_snake_case
typeset ticket_id="CH2-12345"
typeset output_directory="/tmp/output"
typeset current_user="alice"

# Private variables: _leading_underscore
typeset -g _internal_state="initialized"
typeset _temp_file="/tmp/temp"
```

**Rule of thumb:** "If it's your variable, lowercase it. If you export it or it's a constant, uppercase it."

### Functions

```zsh
# Public functions: lowercase_with_underscores
fetch_ticket_data() {
    typeset ticket="$1"
    # ...
}

configure_jira_api() {
    typeset instance="$1"
    # ...
}

# Private functions: _leading_underscore
_validate_json() {
    typeset file="$1"
    # ...
}
```

**→ See:** [01-naming-conventions.md](references/01-naming-conventions.md)

## When to Read Full Resources

### Start Here (Quick Reference)

- This SKILL.md file provides essential patterns and decision tree
- Use for quick lookups and common scenarios

### Read Full References When

1. **Migrating from Bash**: Read [03-word-splitting](references/03-word-splitting-and-quoting.md), [04-array-indexing](references/04-array-indexing.md), [05-strict-mode](references/05-strict-mode-and-options.md)

2. **Deep JSON Processing**: Read [06-json-processing.md](references/06-json-processing.md) for file-based patterns, array loading, and avoiding pipe pitfalls

3. **Variable Management**: Read [02-typeset-and-scoping.md](references/02-typeset-and-scoping.md) for comprehensive `typeset` usage

4. **macOS-Specific Development**: Read [08-macos-specifics.md](references/08-macos-specifics.md) for architecture detection, version checking, BSD vs GNU differences

5. **New to ZSH**: See [Christopher Allen's Opinionated ZSH Best Practices](https://gist.github.com/ChristopherA/562c2e62d01cf60458c5fa87df046fbd) for complete opinionated guide

## Quick Pattern Search

When looking for specific patterns without reading full references, use these grep commands:

```bash
# Find cleanup/trap patterns
grep -n "trap\|cleanup\|always" references/09-common-patterns.md

# Find typeset usage examples
grep -n "typeset -[iAar]" references/02-typeset-and-scoping.md

# Find JSON construction patterns
grep -n "jq -n" references/06-json-processing.md

# Find array loading patterns
grep -n "while IFS=.*read" references/06-json-processing.md

# Find setopt recommendations
grep -n "setopt" references/05-strict-mode-and-options.md

# Find macOS-specific patterns
grep -n "Darwin\|macos\|BSD" references/08-macos-specifics.md

# Find reserved variable names
grep -n "reserved\|read-only" references/10-code-review-checklist.md

# Find word splitting examples
grep -n "\${=.*}" references/03-word-splitting-and-quoting.md
```

## Key Principles Summary

### 1. Be Explicit

```zsh
# Good - Clear intent
typeset -i counter=0
typeset -r CONST="value"
typeset -a items=()
```

### 2. Fail Fast

```zsh
setopt ERR_EXIT NO_UNSET PIPE_FAIL
```

### 3. Clean Up

```zsh
trap cleanup EXIT INT TERM
```

### 4. Embrace ZSH

```zsh
# Don't fight ZSH's defaults
arr=("a" "b" "c")
echo "${arr[1]}"  # ZSH is 1-based

# Use ZSH-specific features
typeset -r ScriptDir="${${(%):-%x}:A:h}"
```

### 5. Be Consistent

Pick conventions and stick with them throughout your project.

### 6. Code Review & Quality Checks

When writing or reviewing ZSH scripts, Claude Code **checks for common ZSH bugs** using this skill's knowledge.

**Critical issues (always fixed):**
- Global variable leakage (missing `typeset`/`local`)
- `(( var++ ))` with `NO_UNSET` (causes failures)
- Wrong array append syntax (`arr+=elem` vs `arr+=(elem)`)
- Unquoted variable expansions
- 0-based array indexing (Bash habits)
- Reserved variable names (`status`, `pipestatus`, `ERRNO`, etc.)
- Bash idioms that fail in ZSH (`trap ... RETURN`)

**Important issues (usually fixed):**
- Missing recommended setopts
- `autoload` without `-U` flag
- `zparseopts` without `-F` flag

**Style suggestions (case-by-case):**
- Explicit type declarations
- Script metadata patterns
- Cleanup handlers

The agent provides context-aware explanations and fixes, not just error messages.

**→ See:** [10-code-review-checklist.md](references/10-code-review-checklist.md) for complete checklist

## Resources

### Scripts

- `scripts/analyze-shell-functions.py` - Tree-sitter-based function analyzer (handles bash/zsh)

**Usage**:
```bash
# Generate extract.json (recommended at session start for large codebases)
uv run zsh-best-practices/scripts/analyze-shell-functions.py --path ./scripts --output extract.json
```

### References

- `references/20-function-discovery-extract-json.md` - **Comprehensive extract.json guide** (setup, jq patterns, commenting best practices)
- [Complete reference list](references/)

## Further Reading

### External Resources

- [Christopher Allen's Opinionated ZSH Best Practices](https://gist.github.com/ChristopherA/562c2e62d01cf60458c5fa87df046fbd) - Primary source for this skill
- [ZSH Documentation](http://zsh.sourceforge.net/Doc/)
- [Moving to ZSH (Scripting OS X)](https://scriptingosx.com/2019/08/moving-to-zsh-part-8-scripting-zsh/)
- [ZSH Guide (Bash to ZSH)](https://github.com/hmml/awesome-zsh)

## Summary

- **Always use:** `emulate -LR zsh` and strict error handling
- **Prefer:** `typeset` over `local` for ZSH scripts
- **Remember:** ZSH doesn't split words by default (`${=var}` to split)
- **Arrays:** 1-based indexing (embrace it, don't use `KSH_ARRAYS`)
- **Shebang:** `#!/usr/bin/env zsh` (portable)
- **Extensions:** `.zsh` for all ZSH scripts
- **Naming:** `lower-kebab-case` files, `lower_snake_case` variables
- **macOS:** ZSH is default since Catalina 10.15
- **Review:** Claude Code checks for bugs when writing/reviewing ZSH scripts
