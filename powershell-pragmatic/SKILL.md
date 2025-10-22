---
name: powershell-pragmatic
description: Pragmatic PowerShell coding guide based on PoshCode best practices. Use when writing PowerShell scripts, functions, or modules. Emphasizes practical, production-ready patterns over dogmatic rules - focuses on readability, error handling, and reusability. ALWAYS runs PSScriptAnalyzer when reviewing or writing PowerShell code.
allowed_tools: Bash, Read, Edit, Write, Glob, Grep
---

# PowerShell Pragmatic

## Overview

Provide guidance for writing pragmatic PowerShell code based on the PoshCode/PowerShellPracticeAndStyle repository. Focus on the 20% of practices that solve 80% of problems - emphasizing readability, proper error handling, and building reusable tools.

**Philosophy**: These are practices and guidelines, not strict rules. If following a guideline prevents accomplishing the task, it's been misunderstood. Adapt based on context.

**Linting Requirement**: This skill ALWAYS runs PSScriptAnalyzer when reviewing or writing PowerShell code. See the "Code Linting with PSScriptAnalyzer" section below for workflow integration.

## Quick Decision Trees

### Tool vs Controller Decision

**Ask first**: What am I building?

- **Tool** (reusable function/module):
  - Accept input via parameters only
  - Output raw data to pipeline
  - Use [CmdletBinding()]
  - Follow Verb-Noun naming
  - Maximize reusability

- **Controller** (automation script):
  - Can output formatted data
  - Can use Write-Host for user interaction
  - Not designed for reuse
  - Orchestrates tools to solve specific business process

### Function Naming Pattern

**Pattern established in production code**:

- **Get-*** → Returns processable data
  - Example: `Get-UserInfo`, `Get-DatabaseStatus`
  - Purpose: Query and return objects for further processing

- **Invoke-*** → Fire-and-forget operations
  - Example: `Invoke-DatabaseBackup`, `Invoke-ServiceRestart`
  - Purpose: Execute actions without returning results
  - Note: These don't return values for processing

### Logging Decision

**Choose ONE approach per context**:

- **Write-CustomLog** (or equivalent centralized logger):
  - Use when log files are needed
  - Already outputs to console via Write-Host
  - NEVER combine with Write-Host (redundant)

- **Write-Host**:
  - ONLY when log files are not needed
  - Pure UI display for interactive scripts

- **Write-Verbose**:
  - Detailed execution information
  - Controlled by -Verbose switch

- **Write-Debug**:
  - Information useful for debugging
  - Controlled by -Debug switch

## Core Function Structure

### Essential Template

Every function should start with this template:

```powershell
function Verb-Noun {
    [CmdletBinding()]
    [OutputType([PSCustomObject])]
    param(
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$ParameterName
    )

    begin {
        # Optional: Setup that runs once
    }

    process {
        # Main logic - runs for each pipeline object
        # Return objects here (not in begin/end)
        [PSCustomObject]@{
            Property = $value
        }
    }

    end {
        # Optional: Cleanup that runs once
    }
}
```

**Key points**:
- Use `[CmdletBinding()]` for all functions (enables -Verbose, -Debug, etc.)
- Order: `param()`, `begin`, `process`, `end`
- Return objects in `process {}` block for pipeline support
- NEVER use `return` keyword - just place the object on its own line
- Include at least a `process {}` block if taking pipeline input

### Parameter Essentials

```powershell
param(
    # Use validation attributes instead of manual checks
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ComputerName,

    [Parameter()]
    [ValidateRange(1, 100)]
    [int]$RetryCount = 3,

    [Parameter()]
    [ValidateSet('Low', 'Medium', 'High')]
    [string]$Priority = 'Medium',

    # Boolean flags
    [Parameter()]
    [switch]$Force
)
```

**Common validation attributes**: `[ValidateNotNullOrEmpty()]`, `[ValidateRange(min, max)]`, `[ValidateSet()]`, `[ValidatePattern()]`, `[ValidateScript()]`

**Important**: Use `[switch]` for boolean parameters, not `[bool]`

For comprehensive parameter patterns, see `references/parameters.md`

## Error Handling Pattern

### Essential Pattern

```powershell
try {
    # For cmdlets: use -ErrorAction Stop
    Get-Item -Path $FilePath -ErrorAction Stop

    # For non-cmdlets: set $ErrorActionPreference
    $ErrorActionPreference = 'Stop'
    $result = SomeExternalCommand
    $ErrorActionPreference = 'Continue'

    # Rest of transaction
    Do-This
    Set-That
} catch {
    # IMMEDIATELY copy error to own variable
    $errorDetails = $_

    # Use PSCmdlet methods for proper error handling
    $PSCmdlet.WriteError(
        [System.Management.Automation.ErrorRecord]::new(
            $errorDetails.Exception,
            'OperationFailed',
            [System.Management.Automation.ErrorCategory]::OperationStopped,
            $FilePath
        )
    )
}
```

### Critical Anti-Patterns to Avoid

**DON'T use flags**:
```powershell
# ❌ BAD
try {
    $continue = $true
    Do-Something -ErrorAction Stop
} catch {
    $continue = $false
}
if ($continue) { Do-Next }
```

**DO put entire transaction in try**:
```powershell
# ✅ GOOD
try {
    Do-Something -ErrorAction Stop
    Do-Next
} catch {
    Handle-Error
}
```

**Other anti-patterns**: Testing `$?` for errors, testing for null variables as error condition, using `throw` instead of `$PSCmdlet.ThrowTerminatingError()`

### Cleanup Pattern

```powershell
$tempFile = New-TemporaryFile
try {
    # Do work with temp file
    $content = Get-Content -Path $tempFile
} finally {
    # Guaranteed cleanup
    Remove-Item -Path $tempFile -ErrorAction SilentlyContinue
}
```

For detailed error handling patterns, see `references/error-handling.md`

## Code Style Essentials

### One True Brace Style (OTBS)

```powershell
# Opening brace at end of line
if ($condition) {
    Do-Something
} else {
    Do-Other
}

# Exception: Single-line scriptblocks
Get-ChildItem | Where-Object { $_.Length -gt 10mb }
```

### Key Formatting Rules

```powershell
# Spaces around operators
$result = $value1 + $value2

# Splatting for long commands
$params = @{
    Path        = $FilePath
    Filter      = '*.log'
    Recurse     = $true
    ErrorAction = 'Stop'
}
Get-ChildItem @params
```

### Capitalization

- **PascalCase**: Functions, cmdlets, parameters, module names, classes, public variables
- **camelCase**: Private variables within functions (optional)
- **lowercase**: Keywords and operators (`foreach`, `if`, `-eq`, `-match`)

For complete style guidelines, see `references/style-guide.md`

## Output Best Practices

### Tools Output Raw Data

```powershell
# ✅ GOOD - Returns bytes (most granular)
function Get-DiskInfo {
    [CmdletBinding()]
    [OutputType([PSCustomObject])]
    param([string]$DriveLetter)

    process {
        $drive = Get-PSDrive -Name $DriveLetter
        [PSCustomObject]@{
            Drive     = $DriveLetter
            FreeBytes = $drive.Free
            UsedBytes = $drive.Used
        }
    }
}

# ❌ BAD - Premature conversion limits reusability
function Get-DiskInfo {
    ...
    FreeGB = [math]::Round($drive.Free / 1GB, 2)
}
```

**Key principle**: Output the most granular data possible. Let consumers format as needed.

### Use OutputType Attribute

```powershell
[OutputType([PSCustomObject])]
[OutputType([string], ParameterSetName = 'AsString')]
```

### Output One Type at a Time

```powershell
# ✅ GOOD - Single output type
function Get-User {
    process {
        Get-ADUser -Filter * | ForEach-Object {
            [PSCustomObject]@{
                Name  = $_.Name
                Email = $_.EmailAddress
            }
        }
    }
}

# ❌ BAD - Mixed output types
function Get-Status {
    "Starting operation..."  # String
    Get-Process              # Process objects
    42                       # Integer
}
```

**Exception**: For internal/private functions, returning multiple types for efficiency is acceptable.

## Key Language Patterns

### Variable Syntax Edge Cases

```powershell
# ✅ CORRECT - Use braces for drive variables
$path = "${systemDrive}:\Windows\System32"

# ❌ WRONG - Doesn't work
$path = "$systemDrive:\Windows\System32"
```

### Avoid Backticks

```powershell
# ❌ BAD - Backtick for line continuation
Get-Process `
    -Name powershell `
    -ErrorAction Stop

# ✅ GOOD - Use splatting
$params = @{
    Name        = 'powershell'
    ErrorAction = 'Stop'
}
Get-Process @params
```

### Hashtable Declaration

```powershell
# ✅ GOOD - Multi-line without semicolons
$config = @{
    Server   = 'localhost'
    Port     = 5432
    Database = 'mydb'
}

# ❌ BAD - Semicolons unnecessary
$config = @{
    Server = 'localhost';
    Port = 5432;
}
```

## Naming Conventions

### Use Approved Verbs

```powershell
# Get list of approved verbs
Get-Verb

# Common approved verbs:
Get, Set, New, Remove, Add, Clear, Write, Read,
Invoke, Start, Stop, Test, Update, Install, Uninstall
```

### Standard Parameter Names

Follow PowerShell conventions:
- `$ComputerName` (not `$Server`, `$Computer`, `$Machine`)
- `$Path` or `$FilePath` (not `$File`, `$FileName`)
- `$Credential` (for PSCredential parameters)
- `$Force` (for switch to skip confirmations)
- `$WhatIf` and `$Confirm` (via SupportsShouldProcess)

## Performance Tips

### Avoid Array Appending in Loops

```powershell
# ❌ BAD - Creates new array each iteration
$results = @()
foreach ($item in $items) {
    $results += Process-Item $item
}

# ✅ GOOD - Use ArrayList
$results = [System.Collections.ArrayList]::new()
foreach ($item in $items) {
    [void]$results.Add((Process-Item $item))
}

# ✅ BETTER - Use pipeline
$results = $items | ForEach-Object { Process-Item $_ }
```

### Prefer PowerShell Over .NET

```powershell
# ✅ PREFER - PowerShell native
Test-Path -Path $file

# ⚠️ AVOID - .NET method (unless performance critical)
[System.IO.File]::Exists($file)
```

For detailed performance patterns, see `references/performance.md`

## Security Essentials

```powershell
# Use PSCredential for credentials
param(
    [PSCredential]$Credential
)

# Use SecureString for sensitive data
$securePassword = ConvertTo-SecureString -String $plaintext -AsPlainText -Force

# Avoid Invoke-Expression
# ❌ DANGEROUS
Invoke-Expression $userInput

# ✅ SAFE - Validate and use proper cmdlets
if ($userInput -match '^[a-zA-Z0-9]+$') {
    & $userInput
}
```

## Documentation

### Comment-Based Help

```powershell
function Get-UserReport {
    <#
    .SYNOPSIS
        Generates user activity report

    .DESCRIPTION
        Retrieves user information from Active Directory and formats
        it into a comprehensive activity report.

    .PARAMETER UserName
        The username to generate report for. Accepts pipeline input.

    .EXAMPLE
        Get-UserReport -UserName jdoe

        Generates basic report for user jdoe.

    .INPUTS
        System.String

    .OUTPUTS
        PSCustomObject

    .NOTES
        Requires Active Directory module.
    #>
    [CmdletBinding()]
    param(...)
}
```

### Inline Comments

```powershell
# Write comments in English using complete sentences
# Use inline comments sparingly - only when code isn't self-explanatory

# Good comment - explains WHY
# Retry logic needed because external API has intermittent issues
for ($i = 0; $i -lt 3; $i++) {
    try {
        Invoke-ApiCall
        break
    } catch {
        Start-Sleep -Seconds 2
    }
}
```

## Code Linting with PSScriptAnalyzer

### When to Lint

**IMPORTANT**: Always run PSScriptAnalyzer when:
- Reviewing PowerShell code
- Writing new PowerShell functions or modules
- Refactoring existing PowerShell code
- Before committing PowerShell changes

### Running PSScriptAnalyzer

```powershell
# Install PSScriptAnalyzer (if not already installed)
Install-Module -Name PSScriptAnalyzer -Scope CurrentUser -Force

# Lint a single file
Invoke-ScriptAnalyzer -Path .\script.ps1

# Lint directory recursively
Invoke-ScriptAnalyzer -Path .\windows\ -Recurse

# Use settings file (recommended)
Invoke-ScriptAnalyzer -Path .\windows\ -Recurse -Settings .\assets\PSScriptAnalyzerSettings.psd1

# Filter by severity
Invoke-ScriptAnalyzer -Path .\windows\ -Recurse -Severity Error,Warning

# Auto-fix issues
Invoke-ScriptAnalyzer -Path .\script.ps1 -Fix
```

### Integration into Review Workflow

When reviewing or writing PowerShell code:

1. **Before making changes**: Run analysis to establish baseline
2. **During development**: Use VS Code integration for real-time feedback
3. **Before finalizing**: Run full analysis and fix violations
4. **Report findings**: Include PSScriptAnalyzer results in code review

### Example Review Workflow

```powershell
# Step 1: Analyze target files
$results = Invoke-ScriptAnalyzer -Path .\windows\SharedFunctions.psm1 -Settings .\assets\PSScriptAnalyzerSettings.psd1

# Step 2: Categorize by severity
$errors = $results | Where-Object { $_.Severity -eq 'Error' }
$warnings = $results | Where-Object { $_.Severity -eq 'Warning' }

# Step 3: Report summary
Write-Host "PSScriptAnalyzer Results:"
Write-Host "  Errors: $($errors.Count)"
Write-Host "  Warnings: $($warnings.Count)"

# Step 4: Show top violations
$results | Group-Object RuleName |
    Sort-Object Count -Descending |
    Select-Object -First 10 |
    Format-Table Name, Count

# Step 5: Auto-fix what's possible
Invoke-ScriptAnalyzer -Path .\windows\SharedFunctions.psm1 -Fix
```

### Settings File Location

This skill includes a PSScriptAnalyzer settings file at:
`assets/PSScriptAnalyzerSettings.psd1`

This file is configured with pragmatic rules that align with this skill's guidelines.

### Common Violations and Fixes

**Missing CmdletBinding**:
```powershell
# ❌ Violation
function Get-Data {
    param([string]$Path)
}

# ✅ Fixed
function Get-Data {
    [CmdletBinding()]
    param([string]$Path)
}
```

**Using return keyword**:
```powershell
# ❌ Violation
function Get-Total {
    return $sum
}

# ✅ Fixed
function Get-Total {
    $sum  # Just output to pipeline
}
```

**Missing parameter validation**:
```powershell
# ❌ Violation
param([string]$Path)

# ✅ Fixed
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Path
)
```

**Non-approved verbs**:
```powershell
# ❌ Violation
function Generate-Report { }

# ✅ Fixed
function New-Report { }
```

### Interpreting Results

PSScriptAnalyzer output includes:
- **RuleName**: Which rule was violated
- **Severity**: Error, Warning, or Information
- **ScriptPath**: File containing the violation
- **Line**: Line number
- **Message**: Explanation and recommendation

Focus on:
1. **Errors first**: These are critical violations
2. **Warnings**: Should be addressed for production code
3. **Information**: Nice-to-have improvements

## Resources

### References (Deep Dives)

For comprehensive coverage of specific topics:

- `references/error-handling.md` - Complete error handling patterns and anti-patterns
- `references/parameters.md` - All parameter validation techniques and advanced patterns
- `references/performance.md` - Performance optimization strategies and benchmarks
- `references/style-guide.md` - Complete style guidelines and conventions
- `assets/PSScriptAnalyzerSettings.psd1` - Linting configuration for this skill

### External Resources

- **PoshCode Best Practices**: [https://poshcode.gitbook.io/powershell-practice-and-style/](https://poshcode.gitbook.io/powershell-practice-and-style/)
- **Approved Verbs**: Run `Get-Verb` in PowerShell
- **About Topics**: `Get-Help about_Functions_Advanced`
- **PSScriptAnalyzer**: [https://github.com/PowerShell/PSScriptAnalyzer](https://github.com/PowerShell/PSScriptAnalyzer)
- **PSScriptAnalyzer Docs**: [https://learn.microsoft.com/en-us/powershell/utility-modules/psscriptanalyzer/](https://learn.microsoft.com/en-us/powershell/utility-modules/psscriptanalyzer/)

## Quick Reference

### Before Writing Code

1. Is this a tool (reusable) or controller (specific automation)?
2. Does PowerShell already have a built-in way? (Use `Get-Command *keyword*`)
3. Should this accept pipeline input?
4. **Run PSScriptAnalyzer** on existing code before modifying

### Function Checklist

- [ ] Starts with `[CmdletBinding()]`
- [ ] Uses approved Verb-Noun naming
- [ ] Has `process {}` block if accepting pipeline input
- [ ] Uses validation attributes instead of manual checks
- [ ] Has `[OutputType()]` attribute
- [ ] Returns objects in `process {}` block (not `begin` or `end`)
- [ ] Uses `-ErrorAction Stop` in try/catch blocks
- [ ] Has comment-based help (at minimum: SYNOPSIS, DESCRIPTION, EXAMPLE)
- [ ] No `return` keyword
- [ ] No backticks for line continuation
- [ ] **Passes PSScriptAnalyzer with no errors**

### After Writing/Modifying Code

1. **Run PSScriptAnalyzer** on modified files
2. Fix all Error-level violations
3. Address Warning-level violations when possible
4. Use `-Fix` parameter for auto-fixable issues
5. Document any intentional rule suppressions

### Common Mistakes to Avoid

- ❌ Using Write-Host for script output (use pipeline)
- ❌ Testing `$?` for errors
- ❌ Appending to arrays in loops
- ❌ Using `return` keyword
- ❌ Validating parameters in function body (use attributes)
- ❌ Mixing output types from a function
- ❌ Forgetting to copy `$_` immediately in catch blocks
- ❌ Using backticks instead of splatting
