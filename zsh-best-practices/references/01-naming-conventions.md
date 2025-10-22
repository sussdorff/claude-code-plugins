# Naming Conventions for ZSH Scripts

Based on Christopher Allen's Opinionated Best Practices with adaptations for modern ZSH development.

## File Naming Conventions

### File Extensions

**Recommendation: Use `.zsh` for all ZSH scripts**

```zsh
# All ZSH scripts use .zsh extension
fetch-ticket-standalone.zsh    # Executable script
jira-handler.zsh                # Executable script
utility-functions.zsh           # Library/sourced script
string-manipulations.zsh        # Library/sourced script
```

**Rationale:**
- Immediately identifies ZSH scripts (vs bash .sh files)
- Consistent extension regardless of executable vs library
- Aligns with modern ZSH project conventions
- Works well with editor syntax highlighting

**Alternative approach** (Christopher Allen's): Use `.sh` for executables (relies on shebang), `.zsh` for libraries. Both are valid; consistency within a project matters most.

### File Naming Style

**Recommendation: Use `lower-kebab-case` for filenames**

```zsh
# Good - kebab-case
fetch-ticket-standalone.zsh
configure-database.zsh
string-manipulation-utils.zsh

# Also acceptable - snake_case (Allen's preference)
fetch_ticket_standalone.zsh
configure_database.zsh
string_manipulation_utils.zsh

# Avoid - CamelCase or spaces
FetchTicket.zsh                 # Slows tab completion
fetch ticket standalone.zsh     # Spaces cause issues
```

**Why kebab-case:**
- Clean, readable
- Works well in URLs and Git repositories
- Common in modern CLI tools
- Easy to type

**Why some prefer snake_case:**
- Consistent with variable naming
- Aligns with traditional Unix conventions
- Allen's preferred approach

**Choose one and be consistent within your project.**

## Strategic Use of Case

### Lower Case Preference

Use lower case for most script names to align with Unix command conventions (`ls`, `cd`, `grep`).

### Strategic Mixed Case

Use intentional capitalization to prevent mistakes:

```zsh
# Strategic capitals force intentional selection
connectAlice.zsh    # Capital A
connectBob.zsh      # Capital B
deployProduction.zsh   # Capital P
deployStaging.zsh      # Capital S
```

**Benefit:** Slowing down tab completion can prevent accidental execution of the wrong script.

### Combining Separators Strategically

Mix separators for complex names to enable selective highlighting:

```zsh
project_charles-build_production-part_one.zsh
# Double-click selects: project_charles, build_production, or part_one
```

**Use cases:**
- Long, complex script names
- Multiple logical components
- Enables copy/paste of name parts

## File Naming Best Practices

### 1. Use Descriptive Names

The script's name should clearly indicate its purpose:

```zsh
# Good - clear purpose
setup-database.zsh
backup-user-data.zsh
validate-configuration.zsh

# Avoid - cryptic
setup.zsh
bkup.zsh
chkcfg.zsh
```

### 2. Prefix with Action Words

Start with a verb indicating the action:

```zsh
install-packages.zsh
remove-temp-files.zsh
generate-report.zsh
fetch-ticket-data.zsh
```

### 3. Keep It Short but Clear

Balance between clarity and brevity:

```zsh
# Good
sync-backup.zsh
deploy-app.zsh

# Too verbose
synchronize-backup-directory-to-remote-server.zsh
deploy-application-to-production-environment.zsh

# Too cryptic
sb.zsh
dap.zsh
```

### 4. Avoid Overuse of Acronyms

Use acronyms only when commonly understood:

```zsh
# Good
setup-api-server.zsh       # API is well-known
configure-ssh-keys.zsh     # SSH is well-known

# Avoid
setup-cl-env.zsh           # What's "cl"? Command-line? Client?
config-db-conn-mgr.zsh     # Too many abbreviations
```

### 5. Avoid Spaces and Special Characters

Use only alphanumeric characters, hyphens, and underscores:

```zsh
# Good
generate-report.zsh
backup_database.zsh

# Avoid
generate report.zsh        # Spaces require quoting
backup-database!.zsh       # Special characters
```

### 6. Test Script Naming

Clearly mark test scripts:

```zsh
# Functional test of entire script
fetch-ticket-standalone-TEST.zsh

# Function-specific test
parse-table-FTEST.zsh
validate-json-FTEST.zsh
```

### 7. Related Scripts: Use Prefixes

Group related scripts with a common prefix:

```zsh
jira-fetch-ticket.zsh
jira-handler.zsh
jira-configure.zsh

zutil-script-template.zsh
zutil-git-tool.zsh
zutil-parse-params.zsh
```

### 8. Private/Internal Scripts: Underscore Prefix

Prefix with `_` for scripts not meant to be executed directly:

```zsh
_config.zsh                    # Configuration, sourced by others
_common-utilities.zsh          # Utility functions
_jira-functions.zsh            # Internal library

# Public scripts that source private ones:
fetch-ticket.zsh               # Sources _jira-functions.zsh
```

### 9. Versioning

Include version for non-current versions:

```zsh
deploy-website.zsh             # Current/working version
deploy-website-legacy.zsh      # Legacy version
deploy-website-v1.2.zsh        # Specific old version
deploy-website-experimental.zsh # Experimental version
```

### 10. Strategic Examples

```zsh
# Versioned scripts
process-data-v1.zsh
process-data-v2.zsh

# Test scripts
get-database-TEST.zsh
parse-json-FTEST.zsh

# Configurations
config-server-main.zsh
config-server-backup.zsh

# Environment-specific
deploy-production.zsh
deploy-staging.zsh
deploy-development.zsh
```

## Variable Naming Conventions

### Requirements (ZSH Syntax)

**Cannot use in variable/function names:**
- Hyphens: `-`
- Periods: `.`
- Special characters: `!@#$%^&*()+={} []|\\:;"'<>?/`

**Must use:**
- Underscores: `_`
- Alphanumeric: `a-zA-Z0-9`

### Industry-Standard Conventions

Based on POSIX standard, Google Shell Style Guide, and community consensus.

#### Constants & Environment Variables: UPPER_SNAKE_CASE

**When to use:**
- Read-only constants (`typeset -r`)
- Exported environment variables (`export`)
- Global configuration values

```zsh
# Read-only constants
typeset -r SCRIPT_DIR="/path/to/script"
typeset -r MAX_RETRY_COUNT=3
typeset -r LOG_FILE_PATH="/var/log/app.log"

# Exported environment variables
export JIRA_API_BASE="https://api.atlassian.net"
export DATABASE_CONNECTION_STRING="postgresql://..."
export VERBOSE_MODE=true
```

**POSIX Standard:** "Environment variable names consist solely of uppercase letters, digits, and underscore."

#### Regular Variables: lowercase_snake_case

**When to use:**
- All regular variables (local and script-scoped)
- Function parameters
- Loop variables
- Temporary variables

```zsh
# Script-scoped variables
typeset ticket_id="CH2-12345"
typeset output_directory="/tmp/output"
typeset current_user_name="alice"
typeset config_file_path="/etc/app/config"

# Function-local variables
process_ticket() {
    typeset ticket="$1"
    typeset ticket_data
    typeset output_path="/tmp/output"

    # Short single-word locals
    typeset count=0
    typeset result
    typeset temp

    # Typed variables
    typeset -i counter=0        # Integer
    typeset -a items=()         # Array
    typeset -A config=()        # Associative array
}
```

**Rule of Thumb:** "If it's your variable, lowercase it. If you export it or it's a constant, uppercase it."

#### Private/Internal Variables: _leading_underscore

**When to use:**
- Internal implementation details
- Variables not meant for external use
- Private globals in libraries

```zsh
# Private globals (internal to script/library)
typeset -g _internal_state="initialized"
typeset -g _debug_mode=false

# Private function variables
_process_internal() {
    typeset _internal_message="$1"
    typeset _debug_level=2
    echo "$_internal_message"
}
```

## Function Naming Conventions

### Use lowercase_with_underscores

**Industry standard:** Function names use lowercase letters with underscores separating words.

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

log_message() {
    typeset level="$1"
    typeset message="$2"
    # ...
}

# Private/internal functions: _leading_underscore
_validate_json() {
    typeset json_file="$1"
    # ...
}

_log_internal() {
    typeset _internal_message="$1"
    # ...
}
```

**Why lowercase_with_underscores:**
- Consistent with variable naming
- Matches most shell projects (Oh My Zsh, Google Style Guide)
- Easy to read and type
- Clear distinction from constants (UPPERCASE)

## Project Organization

### Recommended Directory Structure

```
project-name/
├── README.md
├── .gitignore
├── Makefile
├── bin/                       # Executable scripts
│   ├── build-project.zsh
│   ├── deploy-project.zsh
│   └── test-project.zsh
├── config/                    # Configuration scripts
│   ├── setup-environment.zsh
│   └── configure-database.zsh
├── lib/                       # Library scripts (sourced)
│   ├── utility-functions.zsh
│   ├── string-manipulations.zsh
│   └── _common-utilities.zsh  # Private lib
├── tests/                     # Test scripts
│   ├── build-project-TEST.zsh
│   ├── deploy-project-TEST.zsh
│   └── parse-table-FTEST.zsh
└── docs/                      # Documentation
    ├── CONTRIBUTING.md
    ├── CHANGELOG.md
    └── LICENSE
```

## Consistency Over Style

**Most Important Rule:** Whatever conventions you choose, **be consistent** throughout your codebase.

- Pick one file naming style (kebab-case OR snake_case)
- Stick with one extension approach (.zsh for all OR .sh/.zsh split)
- Apply variable naming consistently
- Document your choices in README.md

## Summary

### Files
- **Extension**: `.zsh` for all ZSH scripts
- **Style**: `lower-kebab-case` (or `snake_case` - choose one)
- **Shebang**: `#!/usr/bin/env zsh`
- **Prefixes**: `_` for private, verb-first for actions
- **Tests**: `-TEST.zsh` suffix

### Variables (Industry Standard)
- **Constants & Exports**: `UPPER_SNAKE_CASE` (POSIX standard)
- **Regular variables**: `lowercase_snake_case`
- **Private variables**: `_leading_underscore`

**Rule:** "If it's your variable, lowercase it. If you export it or it's a constant, uppercase it."

### Functions
- **Public**: `lowercase_with_underscores`
- **Private**: `_lowercase_with_underscores`

### Key Principle
**Consistency within a project** trumps any specific convention. These recommendations follow POSIX, Google Shell Style Guide, and Oh My Zsh conventions for maximum compatibility.
