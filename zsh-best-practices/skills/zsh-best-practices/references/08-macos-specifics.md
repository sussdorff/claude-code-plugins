# macOS-Specific ZSH Considerations

ZSH best practices and patterns specific to macOS development.

## ZSH on macOS

### Default Shell Since Catalina

**macOS Catalina (10.15) and later:** ZSH is the default shell

```zsh
# Check default shell
echo $SHELL              # /bin/zsh

# Check ZSH version
echo $ZSH_VERSION        # 5.9 (as of macOS 14)

# ZSH location
which zsh                # /bin/zsh
```

**Why the change:**
- Apple stopped updating bash (stuck at 3.2 from 2007)
- GPL v3 licensing concerns
- ZSH offers modern features and better scripting

### macOS ZSH Version

macOS ships with ZSH but may lag behind latest versions:

```zsh
# Check installed version
zsh --version            # zsh 5.9 (x86_64-apple-darwin23.0)

# Compare to latest
# Latest as of 2024: 5.9
# macOS 14 (Sonoma): 5.9
# macOS 13 (Ventura): 5.9
# macOS 12 (Monterey): 5.8.1
```

**Updating ZSH (optional):**
```zsh
# Via Homebrew
brew install zsh

# Check versions
/bin/zsh --version       # System ZSH
/opt/homebrew/bin/zsh --version  # Homebrew ZSH (Apple Silicon)
/usr/local/bin/zsh --version     # Homebrew ZSH (Intel)
```

## Shebang Best Practices for macOS

### Recommended: `#!/usr/bin/env zsh`

```zsh
#!/usr/bin/env zsh
# Portable, finds zsh in PATH
```

**Benefits:**
- Works on macOS (default `/bin/zsh`)
- Works if user installed newer ZSH via Homebrew
- Portable to Linux and other systems
- Standard recommendation

**Where it's located:**
```zsh
which env                # /usr/bin/env (always present on macOS)
```

### Alternative: `#!/bin/zsh`

```zsh
#!/bin/zsh
# Direct path to system ZSH
```

**When to use:**
- Installation scripts that must work in Recovery mode
- Package installers (postinstall scripts)
- System-level scripts
- When `/usr/bin/env` may not be available

**Tradeoff:** Less portable, but guaranteed on macOS

### Recovery Mode Consideration

In macOS Recovery mode, PATH may be limited:

```zsh
# Recovery mode - /usr/bin/env may not work
#!/bin/zsh               # Better for Recovery

# Normal mode - env works fine
#!/usr/bin/env zsh       # Preferred for normal scripts
```

**For installers/system scripts:**
```zsh
#!/bin/zsh
# This script runs during installation
```

**For user scripts:**
```zsh
#!/usr/bin/env zsh
# User-facing scripts
```

## macOS-Specific Paths

### Standard Directories

```zsh
# System ZSH
/bin/zsh                 # System ZSH (5.9 on Sonoma)

# Homebrew locations
/opt/homebrew/bin/zsh    # Apple Silicon (M1/M2/M3)
/usr/local/bin/zsh       # Intel

# User directories
~/Library                # User library
~/Library/Application Support
~/Library/Preferences

# System directories
/Library                 # System-wide library
/System/Library          # macOS system files (read-only)
/usr/local               # User-installed software (Intel)
/opt/homebrew            # Homebrew on Apple Silicon
```

### PATH Differences

```zsh
# Apple Silicon Homebrew adds
/opt/homebrew/bin
/opt/homebrew/sbin

# Intel Homebrew adds
/usr/local/bin
/usr/local/sbin

# Check architecture
uname -m                 # arm64 or x86_64

# Set PATH appropriately
if [[ "$(uname -m)" == "arm64" ]]; then
    # Apple Silicon
    typeset -r BrewPrefix="/opt/homebrew"
else
    # Intel
    typeset -r BrewPrefix="/usr/local"
fi

path=("${BrewPrefix}/bin" "${BrewPrefix}/sbin" $path)
```

## Architecture Detection

### Apple Silicon vs Intel

```zsh
# Detect architecture
typeset -r Arch=$(uname -m)

if [[ "$Arch" == "arm64" ]]; then
    echo "Running on Apple Silicon (M1/M2/M3)"
    typeset -r IsAppleSilicon=true
elif [[ "$Arch" == "x86_64" ]]; then
    echo "Running on Intel"
    typeset -r IsAppleSilicon=false
fi

# Check if running under Rosetta 2
if [[ "$Arch" == "x86_64" ]] && [[ "$(sysctl -n machdep.cpu.brand_string)" =~ "Apple" ]]; then
    echo "Apple Silicon running under Rosetta 2"
fi
```

### Universal Scripts

```zsh
#!/usr/bin/env zsh

# Work on both architectures
typeset -r Arch=$(uname -m)

case "$Arch" in
    arm64)
        typeset -r BinPath="/opt/homebrew/bin"
        ;;
    x86_64)
        typeset -r BinPath="/usr/local/bin"
        ;;
    *)
        echo "Unknown architecture: $Arch" >&2
        exit 1
        ;;
esac

# Use architecture-specific path
export PATH="${BinPath}:${PATH}"
```

## macOS Version Detection

### Get macOS Version

```zsh
# Product version
typeset -r MacOsVersion=$(sw_vers -productVersion)
# Examples: 14.5, 13.6, 12.7

# Build version
typeset -r MacOsBuild=$(sw_vers -buildVersion)
# Example: 23F79

# Product name
typeset -r MacOsName=$(sw_vers -productName)
# Output: macOS

# Major version
typeset -r MacOsMajor=${MacOsVersion%%.*}
# Example: 14 from 14.5
```

### Version Comparisons

```zsh
# Check if macOS 13+
if [[ ${MacOsVersion%%.*} -ge 13 ]]; then
    echo "Running macOS 13 (Ventura) or later"
fi

# Check specific version
case "${MacOsVersion%%.*}" in
    14)
        echo "macOS 14 Sonoma"
        ;;
    13)
        echo "macOS 13 Ventura"
        ;;
    12)
        echo "macOS 12 Monterey"
        ;;
    *)
        echo "macOS ${MacOsVersion}"
        ;;
esac

# Detailed version check
autoload is-at-least
if is-at-least 13.0 ${MacOsVersion}; then
    echo "macOS 13.0 or later"
fi
```

## macOS Commands and Utilities

### macOS-Specific Commands

```zsh
# System information
sw_vers                  # macOS version
system_profiler          # Detailed system info
sysctl                   # System control

# File system
mdls                     # Metadata list
mdfind                   # Spotlight search
xattr                    # Extended attributes

# Applications
open                     # Open files/apps
osascript                # AppleScript runner
defaults                 # Preferences

# Examples
open .                   # Open current dir in Finder
open -a Safari           # Open Safari
mdfind "kind:document"   # Find documents via Spotlight
```

### Common macOS Patterns

```zsh
# Open file in default app
open_File() {
    local file="$1"
    if [[ -f "$file" ]]; then
        open "$file"
    fi
}

# Get app bundle identifier
get_Bundle_Id() {
    local app="$1"
    osascript -e "id of app \"$app\"" 2>/dev/null
}

# Check if app is running
is_App_Running() {
    local app="$1"
    pgrep -x "$app" > /dev/null
}

# Quit app gracefully
quit_App() {
    local app="$1"
    osascript -e "tell application \"$app\" to quit" 2>/dev/null
}
```

## Compatibility Fixes

### realpath for Older macOS

Older macOS versions don't have `realpath`:

```zsh
# Check if realpath exists, provide fallback
if ! command -v realpath &> /dev/null; then
    realpath() {
        [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
    }
fi

# Usage
typeset -r ScriptPath=$(realpath "$0")
```

### GNU vs BSD Commands

macOS uses BSD versions of commands (different from Linux):

```zsh
# sed differences
sed -i '' 's/old/new/' file     # macOS (BSD) - requires empty string
sed -i 's/old/new/' file         # Linux (GNU)

# Portable sed
if [[ "$(uname -s)" == "Darwin" ]]; then
    sed -i '' 's/old/new/' file
else
    sed -i 's/old/new/' file
fi

# date differences
date -r 1609459200                 # macOS (BSD) - seconds since epoch
date -d @1609459200                # Linux (GNU)

# Portable date
if [[ "$(uname -s)" == "Darwin" ]]; then
    date -r "$timestamp"
else
    date -d "@$timestamp"
fi

# stat differences
stat -f %Sm "$file"                # macOS (BSD)
stat -c %y "$file"                 # Linux (GNU)
```

## Finder Integration

### Configure Finder for .zsh Files

Make .zsh files open in Terminal by default:

1. Right-click a .zsh file
2. "Get Info"
3. "Open with:" → Terminal.app
4. "Change All..."

**Caveat:** Files execute without parameters when opened this way.

### Launch from Finder

Scripts opened via Finder don't receive command-line arguments:

```zsh
#!/usr/bin/env zsh

# Detect if opened via Finder (no args, specific environment)
if [[ $# -eq 0 ]] && [[ -z "${SSH_CONNECTION}" ]]; then
    echo "Opened via Finder - prompting for parameters"

    # Use osascript to get input
    local input=$(osascript -e 'Tell application "System Events" to display dialog "Enter parameters:" default answer ""' -e 'text returned of result' 2>/dev/null)

    if [[ -n "$input" ]]; then
        # Re-run with parameters
        exec "$0" $=input
    fi
    exit 0
fi

# Normal execution with args
echo "Args: $@"
```

## Security Considerations

### Gatekeeper and Code Signing

Downloaded scripts may be quarantined:

```zsh
# Check quarantine attribute
xattr script.zsh          # Shows com.apple.quarantine if present

# Remove quarantine
xattr -d com.apple.quarantine script.zsh

# Or allow execution
chmod +x script.zsh
xattr -c script.zsh       # Clear all attributes

# Check if file is signed
codesign -dv script.zsh 2>&1
```

### Running Unverified Scripts

```zsh
# User may need to:
# 1. Right-click → Open (instead of double-click)
# 2. Confirm "Open Anyway" in System Settings → Security

# Or remove quarantine programmatically
remove_Quarantine() {
    local file="$1"
    if xattr "$file" 2>/dev/null | grep -q "com.apple.quarantine"; then
        echo "Removing quarantine from $file"
        xattr -d com.apple.quarantine "$file"
    fi
}
```

## Useful macOS Patterns

### Detect if Running on macOS

```zsh
# Check if macOS
if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "This script requires macOS" >&2
    exit 1
fi

# Or set flag
typeset -r IsMacOs=$([[ "$(uname -s)" == "Darwin" ]] && echo true || echo false)
```

### Notification Center

```zsh
# Display notification
display_Notification() {
    local title="$1"
    local message="$2"

    osascript -e "display notification \"$message\" with title \"$title\""
}

# Usage
display_Notification "Build Complete" "Project built successfully"
```

### Clipboard Access

```zsh
# Copy to clipboard
echo "text to copy" | pbcopy

# Paste from clipboard
pbpaste

# Functions
copy_To_Clipboard() {
    echo "$1" | pbcopy
    echo "Copied to clipboard: $1"
}

get_From_Clipboard() {
    pbpaste
}
```

## Summary

### macOS ZSH Essentials

- **Default since:** macOS Catalina (10.15)
- **System location:** `/bin/zsh`
- **Shebang:** `#!/usr/bin/env zsh` (portable) or `#!/bin/zsh` (system/installer)
- **Architecture:** Check with `uname -m` (arm64 vs x86_64)
- **Version:** `sw_vers -productVersion`

### Key Differences from Linux

- BSD command variants (sed, date, stat)
- Different Homebrew paths (Intel vs Apple Silicon)
- Finder integration considerations
- Gatekeeper/quarantine attributes
- macOS-specific commands (open, osascript, defaults)

### Best Practices

1. Use `#!/usr/bin/env zsh` for user scripts
2. Use `#!/bin/zsh` for installers/system scripts
3. Handle both Intel and Apple Silicon paths
4. Test BSD vs GNU command differences
5. Consider Gatekeeper when distributing scripts
6. Provide `realpath` fallback for older macOS
7. Document macOS version requirements
