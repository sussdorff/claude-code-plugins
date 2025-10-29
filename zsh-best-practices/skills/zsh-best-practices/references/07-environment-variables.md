# Environment Variables Reference for ZSH

Comprehensive guide to useful environment variables and conventions in ZSH scripts, based on Christopher Allen's Opinionated Best Practices.

## Operating System Variables

Get information about the OS and hardware:

```zsh
# Operating system type (Linux, Darwin, etc.)
typeset -r OsType=$(uname -s)

# Kernel version
typeset -r OsKernelVersion=$(uname -r)

# Machine hardware (x86_64, arm64, etc.)
typeset -r OsMachineHardware=$(uname -m)

# Operating system release
typeset -r OsReleaseName=$(uname -v)

# Example usage
if [[ "$OsType" == "Darwin" ]]; then
    echo "Running on macOS"
elif [[ "$OsType" == "Linux" ]]; then
    echo "Running on Linux"
fi
```

## System and Shell Variables

Standard environment variables available in most shells:

```zsh
# Home directory
$HOME                # /Users/username
${HOME}              # Preferred bracket notation

# Current username
$USER                # username
$LOGNAME             # login name (may differ from USER)

# Hostname
$HOSTNAME            # Short hostname
$(hostname)          # Full hostname
$(hostname -f)       # Fully qualified domain name (FQDN)

# Shell path
$SHELL               # /bin/zsh

# Path search directories
$PATH                # Colon-separated list of directories

# Terminal type
$TERM                # xterm-256color, etc.

# Locale settings
$LANG                # en_US.UTF-8
$LC_ALL              # Override all locale settings
```

## macOS-Specific Variables

Variables particularly useful on macOS:

```zsh
# macOS version
typeset -r MacOsVersion=$(sw_vers -productVersion)  # 14.5

# macOS build
typeset -r MacOsBuild=$(sw_vers -buildVersion)      # 23F79

# macOS product name
typeset -r MacOsName=$(sw_vers -productName)        # macOS

# Architecture
typeset -r MacArchitecture=$(uname -m)              # arm64 or x86_64

# Check if running on Apple Silicon
if [[ "$MacArchitecture" == "arm64" ]]; then
    echo "Running on Apple Silicon"
fi

# Check macOS version
if [[ "${MacOsVersion%%.*}" -ge 13 ]]; then
    echo "Running macOS 13 (Ventura) or later"
fi
```

## User Environment Information

User-specific details:

```zsh
# Current user
$USER                      # username
$UID                       # User ID (numeric)
$EUID                      # Effective user ID
$USERNAME                  # Same as $USER (ZSH-specific)

# User's home
$HOME                      # /Users/username
~                          # Expands to $HOME
~username                  # Another user's home

# User's group
$GID                       # Group ID (numeric)
$(id -gn)                  # Group name

# Check if root
if [[ $EUID -eq 0 ]]; then
    echo "Running as root"
fi

# Full user info
typeset -r UserFullName=$(id -F)           # macOS: Full Name
typeset -r UserName=$(id -un)              # username
typeset -r UserGroup=$(id -gn)             # primary group
```

## Shell Environment Variables

ZSH and shell-specific variables:

```zsh
# ZSH version
$ZSH_VERSION               # 5.9

# Shell options
$options                   # Array of set options
$-                         # Current shell flags

# Shell level (nesting)
$SHLVL                     # 1, 2, 3... (increments with each subshell)

# Last command exit status
$?                         # 0 = success, non-zero = error

# Process ID
$$                         # Current shell's PID
$PPID                      # Parent process PID

# Random number
$RANDOM                    # Random integer 0-32767

# Check if interactive
if [[ -o interactive ]]; then
    echo "Running interactively"
fi
```

## ZSH-Specific Variables

Variables unique to ZSH:

```zsh
# Script/function information
$0                         # Script name or "zsh" if interactive
${(%):-%x}                 # Current script file path (ZSH-specific)
${(%):-%N}                 # Current function name

# ZSH version
$ZSH_VERSION               # 5.9
$ZSH_PATCHLEVEL            # Patch level

# History
$HISTFILE                  # ~/.zsh_history
$HISTSIZE                  # Number of commands in memory
$SAVEHIST                  # Number saved to file

# Arrays (ZSH-specific features)
$path                      # Array version of $PATH
$fpath                     # Function search path (array)

# Module info
$modules                   # Loaded modules

# Get script directory (ZSH way)
typeset -r ScriptDir="${${(%):-%x}:A:h}"
```

## Working Directory Information

Current directory and navigation:

```zsh
# Current directory
$PWD                       # Current working directory (absolute)
$(pwd)                     # Same as $PWD
$OLDPWD                    # Previous directory

# Change to previous directory
cd -                       # Uses $OLDPWD
cd "$OLDPWD"              # Explicit

# Directory stack
dirs                       # Show directory stack
pushd /path               # Push and cd
popd                      # Pop and cd

# Example: Save current dir
typeset -r OriginalDir="$PWD"
cd /somewhere/else
# ... do work ...
cd "$OriginalDir"         # Return
```

## Script Environment

Variables for script location and execution:

```zsh
# Script path (ZSH-specific, most reliable)
typeset -r ScriptPath="${(%):-%x}"
typeset -r ScriptDir="${${(%):-%x}:A:h}"
typeset -r ScriptName="${${(%):-%x}:t}"

# Alternative (works in bash too, but less reliable in ZSH)
typeset -r ScriptPathAlt="$0"
typeset -r ScriptDirAlt="$(cd "$(dirname "$0")" && pwd)"

# Absolute path resolution
typeset -r ScriptAbsolute="${(%):-%x:A}"

# Script directory for includes
source "${ScriptDir}/_common-functions.zsh"
source "${ScriptDir}/lib/utilities.zsh"

# Example: Construct paths relative to script
typeset -r ConfigFile="${ScriptDir}/../config/app.conf"
typeset -r DataDir="${ScriptDir}/../data"
```

## Caller Script Information

When script is sourced or called by another:

```zsh
# Calling script info
$0                         # Calling script name
${(%):-%x}                 # Current script (even when sourced)

# Detect if sourced vs executed
if [[ "${(%):-%x}" != "${0}" ]]; then
    echo "Script is being sourced"
else
    echo "Script is being executed"
fi

# Function calling context
$funcstack                 # Array of function call stack
$functrace                 # Array of function trace
```

## Process Information

Process and execution details:

```zsh
# Process IDs
$$                         # Current shell PID
$PPID                      # Parent process PID
$!                         # Last background process PID

# Exit status
$?                         # Last command exit status

# Background jobs
jobs                       # List background jobs
$jobstates                 # Job states array

# Example: Check if command succeeded
if some_command; then
    echo "Success (exit $?)"
else
    echo "Failed with exit code $?"
fi

# Wait for background process
some_command &
local bgpid=$!
wait $bgpid
echo "Background process exited with $?"
```

## Script Arguments

Command-line argument handling:

```zsh
# All arguments
$@                         # All args as separate words
$*                         # All args as single string
"$@"                       # Proper: preserves spacing
"$*"                       # Single string (IFS-separated)

# Argument count
$#                         # Number of arguments

# Individual arguments
$1, $2, $3...              # Positional parameters
${10}                      # Use braces for $10+

# Shift arguments
shift                      # Remove $1, shift others down
shift 2                    # Remove $1 and $2

# Example: Parse arguments
process_Args() {
    echo "Script: $0"
    echo "Args: $#"

    local count=1
    for arg in "$@"; do
        echo "  Arg $count: $arg"
        (( count++ ))
    done
}

process_Args "arg1" "arg 2" "arg3"
```

## Git Environment Variables

Git-specific variables (when in git repo):

```zsh
# Local repository info
$(git rev-parse --show-toplevel)          # Repo root
$(git branch --show-current)              # Current branch
$(git rev-parse --short HEAD)             # Short commit hash
$(git rev-parse HEAD)                     # Full commit hash
$(git status --porcelain)                 # Changes (parseable)

# Global git configuration
$GIT_AUTHOR_NAME                          # From git config
$GIT_AUTHOR_EMAIL
$GIT_COMMITTER_NAME
$GIT_COMMITTER_EMAIL

# Example: Get repo info
if git rev-parse --git-dir > /dev/null 2>&1; then
    typeset -r RepoRoot=$(git rev-parse --show-toplevel)
    typeset -r CurrentBranch=$(git branch --show-current)
    echo "In repo: $RepoRoot"
    echo "Branch: $CurrentBranch"
fi
```

## Other Common Variables

Additional useful environment variables:

```zsh
# Editor
$EDITOR                    # Default editor (vim, nano, etc.)
$VISUAL                    # Visual editor
$PAGER                     # Pager (less, more)

# Temporary directory
$TMPDIR                    # /tmp or /var/tmp
$(mktemp -d)               # Create temp dir

# Language/Locale
$LANG                      # en_US.UTF-8
$LC_ALL                    # Override all LC_* variables
$LC_CTYPE                  # Character classification

# Timezone
$TZ                        # America/Los_Angeles

# Display (X11)
$DISPLAY                   # :0

# SSH
$SSH_CONNECTION            # SSH connection info
$SSH_CLIENT                # SSH client info
$SSH_TTY                   # SSH TTY
```

## Best Practices for Using Environment Variables

### 1. Prefer Read-Only for Constants

```zsh
typeset -r ScriptDir="${${(%):-%x}:A:h}"
typeset -r ConfigPath="${ScriptDir}/config.conf"
```

### 2. Use Brackets for Clarity

```zsh
# Good
echo "${HOME}/documents"
echo "${USER}-${HOSTNAME}"

# Works but less clear
echo "$HOME/documents"
```

### 3. Provide Defaults

```zsh
# Use default if variable not set
typeset editor="${EDITOR:-vim}"
typeset tmpdir="${TMPDIR:-/tmp}"

# Or set default if not set
: ${EDITOR:=vim}
```

### 4. Check Before Using

```zsh
if [[ -z "${JIRA_TOKEN}" ]]; then
    echo "Error: JIRA_TOKEN not set" >&2
    exit 1
fi
```

### 5. Export Only When Needed

```zsh
# Local to script
typeset API_KEY="secret"

# Available to child processes
export JIRA_API_BASE="https://api.atlassian.net"
```

## Quick Reference Table

| Variable | Description | Example |
|----------|-------------|---------|
| `$HOME` | Home directory | `/Users/username` |
| `$USER` | Username | `username` |
| `$PWD` | Current directory | `/Users/username/project` |
| `$OLDPWD` | Previous directory | `/Users/username` |
| `$0` | Script name | `my-script.zsh` |
| `$#` | Argument count | `3` |
| `$@` | All arguments | `arg1 arg2 arg3` |
| `$?` | Last exit status | `0` or `1` |
| `$$` | Current PID | `12345` |
| `$PPID` | Parent PID | `12344` |
| `${(%):-%x}` | Current script path (ZSH) | `/path/to/script.zsh` |
| `$ZSH_VERSION` | ZSH version | `5.9` |
| `$(uname -s)` | OS type | `Darwin` |
| `$(uname -m)` | Architecture | `arm64` |

## Summary

- Use `typeset -r` for constants derived from environment
- Prefer ZSH-specific `${(%):-%x}` for script location
- Always quote variable expansions: `"$VAR"` not `$VAR`
- Provide sensible defaults: `${VAR:-default}`
- Check critical variables before use
- Export only what child processes need
