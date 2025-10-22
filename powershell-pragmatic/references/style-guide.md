# PowerShell Style Guide

Complete style guidelines for writing clean, consistent PowerShell code.

## Philosophy

These guidelines promote consistency and readability across codebases. While not mandatory, following them makes code easier to scan and understand. Project-specific rules always take precedence.

## Capitalization Conventions

### Terminology

- **lowercase** - all lowercase, no word separation
- **UPPERCASE** - all capitals, no word separation
- **PascalCase** - capitalize the first letter of each word
- **camelCase** - capitalize first letter of each word except the first

### When to Use Each

**PascalCase** (most PowerShell identifiers):
- Module names: `MyAwesomeModule`
- Function/cmdlet names: `Get-UserInfo`, `Set-Configuration`
- Class names: `DatabaseConnection`
- Enum names: `LogLevel`
- Attribute names: `ValidateCustomAttribute`
- Public fields/properties: `$Script:Configuration`
- Global variables: `$Global:AppSettings`
- Constants: `$MaxRetryCount`
- Parameters: `$ComputerName`, `$FilePath`

**camelCase** (optional, for private scope):
- Private variables within functions: `$localCounter`, `$tempValue`
- Private module variables: `$script:cachedData`

**lowercase** (PowerShell keywords):
- Keywords: `param`, `begin`, `process`, `end`, `foreach`, `if`, `switch`
- Operators: `-eq`, `-ne`, `-match`, `-like`, `-and`, `-or`

**UPPERCASE** (documentation only):
- Comment-based help keywords: `.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER`

### Special Cases

**Two-letter acronyms** - Both letters capitalized:
- `$PSBoundParameters`
- `Get-PSDrive`
- `$VM`, `$DB`, `$UI`

**Longer acronyms** - Only first letter capitalized:
- `Start-AzureRmVM` (not `Start-AzureRMVM`)
- `$SqlConnection` (not `$SQLConnection`)
- `Get-HtmlContent` (not `Get-HTMLContent`)

**Common words** (not acronyms):
- `$OKButton` (not `$OkButton`)
- `$UserID` (not `$UserId`)

**Variable names starting with acronym**:
- PascalCase: `$DBConnection`, `$VMHost`
- camelCase: `$dbConnection`, `$vmHost` (lowercase both letters)

## Code Layout

### One True Brace Style (OTBS)

Opening brace at the **end** of the line, closing brace at the **beginning** of a line:

```powershell
# ✅ CORRECT
enum Color {
    Black
    White
}

function Get-Data {
    [CmdletBinding()]
    param(
        [string]$Name
    )

    process {
        if ($Name -eq 'Test') {
            Write-Output 'Found Test'
        } else {
            Write-Output 'Not Found'
        }
    }
}

# Exception: Single-line scriptblocks
Get-Process | Where-Object { $_.CPU -gt 100 }
```

**Why OTBS**:
- No exceptions needed - always consistent
- New lines can be inserted anywhere without breaking code
- Required for DSC and some scriptblock parameters
- Most PowerShell code already follows this

### Indentation

Use **4 spaces** per level (not tabs):

```powershell
function Test-Code {
    foreach ($item in $collection) {
        if ($item.Value -gt 10) {
            Write-Output $item
        }
    }
}
```

**Continuation lines** may indent more than one level:

```powershell
function Test-Example {
    $result = [System.Math]::Pow($base,
                                  $exponent)

    $params = @{
        Name        = $name
        Value       = $value
        Description = $description
    }
}
```

### Line Length

Aim for **115 characters** maximum.

**Rationale**:
- PowerShell console: 119 characters max on output
- GitHub: Displays ~121-126 characters depending on browser
- Side-by-side diffs fit on 1080p monitors

**Break long lines** using:

1. **Splatting** (preferred):
```powershell
$params = @{
    Path        = $FilePath
    Filter      = '*.log'
    Recurse     = $true
    ErrorAction = 'Stop'
}
Get-ChildItem @params
```

2. **Natural line continuation** (parentheses, brackets, braces):
```powershell
$message = (
    "This is a very long message " +
    "that spans multiple lines " +
    "using string concatenation"
)

$array = @(
    'Item1'
    'Item2'
    'Item3'
)
```

3. **Pipeline continuation**:
```powershell
Get-Process |
    Where-Object { $_.CPU -gt 100 } |
    Sort-Object -Property CPU -Descending |
    Select-Object -First 10
```

### Whitespace

**Blank lines**:
```powershell
# Two blank lines before/after functions
function Get-FirstFunction {
    # ...
}


function Get-SecondFunction {
    # ...
}


# Single blank line between methods in a class
class MyClass {
    [void] MethodOne() {
        # ...
    }

    [void] MethodTwo() {
        # ...
    }
}

# End each file with a single blank line
```

**Trailing whitespace**: Remove all trailing whitespace from lines.

**Spaces around operators**:
```powershell
# ✅ CORRECT
$result = $value1 + $value2
$isValid = $count -gt 10 -and $status -eq 'Active'

# ❌ WRONG
$result=$value1+$value2
$isValid=$count-gt 10-and$status-eq'Active'
```

**Spaces around colons** (exception for switch parameters):
```powershell
# Switch parameters - no spaces around colon
Get-ChildItem -Recurse:$true
Get-Process -Verbose:$false

# Hashtables - spaces around assignment
$config = @{
    Name  = 'Test'
    Value = 123
}
```

**Spaces in scriptblocks and subexpressions**:
```powershell
# ✅ CORRECT - Space inside braces/parentheses
$count = $( Get-ChildItem ).Count
Get-Process | Where-Object { $_.CPU -gt 100 }

# ❌ WRONG - No spaces
$count = $(Get-ChildItem).Count
Get-Process | Where-Object {$_.CPU -gt 100}

# Variable delimiters - no space inside
${My-Variable-Name}
```

**Spaces in brackets**:
```powershell
# ✅ CORRECT - No spaces
$array[0]
$hash['key']
[int]$number

# ❌ WRONG - Unnecessary spaces
$array[ 0 ]
$hash[ 'key' ]
[ int ]$number
```

**Commas and semicolons**:
```powershell
# ✅ CORRECT - Space after, not before
$array = @(1, 2, 3, 4)
$params = @{A = 1; B = 2}

# ❌ WRONG
$array = @(1,2,3,4)
$array = @(1 , 2 , 3 , 4)
```

**Unary operators** - No space:
```powershell
# ✅ CORRECT
$i++
$i--
$negative = -$value
$yesterday = (Get-Date).AddDays(-1)

# ❌ WRONG
$i ++
$i --
$negative = - $value
$yesterday = (Get-Date).AddDays(- 1)
```

### Semicolons

**Avoid semicolons** as line terminators:

```powershell
# ✅ GOOD
$name = 'Test'
$value = 123

# ❌ BAD - Unnecessary semicolons
$name = 'Test';
$value = 123;
```

**Hashtables** - No semicolons on separate lines:
```powershell
# ✅ GOOD
$config = @{
    Name  = 'Test'
    Value = 123
}

# ❌ BAD
$config = @{
    Name  = 'Test';
    Value = 123;
}

# Acceptable: Single line
$config = @{Name = 'Test'; Value = 123}
```

## Function Structure

### Always Start with CmdletBinding

```powershell
# ✅ ALWAYS USE THIS TEMPLATE
function Verb-Noun {
    [CmdletBinding()]
    param(
        [Parameter()]
        [string]$Parameter
    )

    begin {
        # Optional
    }

    process {
        # Main logic
    }

    end {
        # Optional
    }
}
```

### Preferred Block Order

Always use this order (even if you don't need all blocks):
1. `[CmdletBinding()]` and other attributes
2. `param()`
3. `begin {}`
4. `process {}`
5. `end {}`

```powershell
# ✅ CORRECT ORDER
function Get-Example {
    [CmdletBinding()]
    [OutputType([PSCustomObject])]
    param(
        [string]$Name
    )

    begin {
        Write-Verbose 'Starting operation'
    }

    process {
        # Return object here for pipeline support
        [PSCustomObject]@{
            Name = $Name
        }
    }

    end {
        Write-Verbose 'Operation complete'
    }
}
```

**Why this order**: It's the execution order, making code easier to follow.

### Avoid return Keyword

```powershell
# ❌ BAD
function Get-Data {
    param($Name)
    $data = Get-SomeData -Name $Name
    return $data
}

# ✅ GOOD
function Get-Data {
    [CmdletBinding()]
    param([string]$Name)

    process {
        Get-SomeData -Name $Name
    }
}
```

## Naming Conventions

### Functions and Cmdlets

Use **Verb-Noun** format with approved verbs:

```powershell
# ✅ CORRECT
function Get-UserData { }
function Set-Configuration { }
function New-Report { }
function Remove-TempFile { }

# ❌ WRONG - Not approved verbs
function Fetch-UserData { }   # Use Get
function Create-Report { }     # Use New
function Delete-TempFile { }   # Use Remove
```

Get approved verbs:
```powershell
Get-Verb | Out-GridView
```

Common approved verbs:
- **Data**: Get, Set, New, Remove, Clear, Add, Copy, Move
- **Lifecycle**: Start, Stop, Restart, Suspend, Resume
- **Diagnostic**: Test, Measure, Trace, Debug
- **Communication**: Read, Write, Send, Receive
- **Other**: Invoke, Update, Install, Uninstall, Show, Format

### Parameters

Use standard PowerShell parameter names:

| Concept | Correct | Incorrect |
|---------|---------|-----------|
| Computer name | `$ComputerName` | `$Computer`, `$Server`, `$Host`, `$Machine` |
| File path | `$Path`, `$FilePath` | `$File`, `$FileName` |
| Credentials | `$Credential` | `$Cred`, `$Credentials`, `$User` |
| Force operation | `$Force` | `$Forced`, `$Override` |

**Why**: Consistency with built-in cmdlets, predictable for users.

### Variables

```powershell
# Public/script scope: PascalCase
$Script:Configuration = @{}
$Global:AppSettings = @{}

# Private/local: PascalCase or camelCase
$userName = 'test'  # camelCase (optional style)
$UserName = 'test'  # PascalCase (also valid)

# Be consistent within a script/module
```

## Comments and Documentation

### Comment-Based Help

Place **inside** the function, at the top:

```powershell
function Get-UserReport {
    <#
    .SYNOPSIS
        Generates a user activity report

    .DESCRIPTION
        Retrieves user information from Active Directory and creates a
        comprehensive activity report including login history, group
        membership, and recent file modifications.

    .PARAMETER UserName
        The username (SamAccountName) to generate the report for.
        Accepts pipeline input.

    .PARAMETER IncludeGroups
        Include group membership information in the report.

    .PARAMETER StartDate
        Start date for activity analysis. Defaults to 30 days ago.

    .EXAMPLE
        Get-UserReport -UserName jdoe

        Generates a basic activity report for user jdoe.

    .EXAMPLE
        'jdoe', 'asmith' | Get-UserReport -IncludeGroups

        Generates reports with group information for multiple users.

    .EXAMPLE
        Get-UserReport -UserName jdoe -StartDate (Get-Date).AddDays(-7)

        Generates a report for the last 7 days of activity.

    .INPUTS
        System.String
        You can pipe usernames to this function.

    .OUTPUTS
        PSCustomObject
        Returns a custom object with user activity information.

    .NOTES
        Requires Active Directory PowerShell module.
        User must have read permissions in Active Directory.

    .LINK
        https://docs.example.com/user-reports

    .LINK
        Get-ADUser
    #>
    [CmdletBinding()]
    param(...)
}
```

**Required sections**: SYNOPSIS, DESCRIPTION, PARAMETER (for each), EXAMPLE
**Recommended**: INPUTS, OUTPUTS, NOTES, LINK

### Inline Comments

Write in **English**, use **complete sentences**:

```powershell
# ✅ GOOD - Explains WHY
# Retry needed because API has intermittent timeout issues
for ($i = 0; $i -lt 3; $i++) {
    try {
        Invoke-ApiCall
        break
    } catch {
        Start-Sleep -Seconds 2
    }
}

# ❌ BAD - Explains obvious WHAT
# Loop 3 times
for ($i = 0; $i -lt 3; $i++) {
    ...
}
```

**Block comments** for documentation:
```powershell
<#
This function implements a complex algorithm that:
1. Retrieves data from multiple sources
2. Correlates based on timestamp
3. Filters outliers using statistical methods
4. Returns aggregated results
#>
```

**Inline comments** sparingly:
```powershell
# Use only when code isn't self-explanatory
$timeout = 30  # API documented maximum is 30 seconds
```

## Avoid Backticks

**Prefer splatting and natural continuation**:

```powershell
# ❌ BAD - Backtick continuation
Get-ChildItem -Path C:\Logs `
    -Filter *.log `
    -Recurse `
    -ErrorAction Stop

# ✅ GOOD - Splatting
$params = @{
    Path        = 'C:\Logs'
    Filter      = '*.log'
    Recurse     = $true
    ErrorAction = 'Stop'
}
Get-ChildItem @params

# ✅ GOOD - Pipeline continuation
Get-ChildItem -Path C:\Logs -Filter *.log |
    Where-Object { $_.Length -gt 1MB } |
    Remove-Item -Force
```

## Strings

### Quote Choice

- **Single quotes** for literal strings
- **Double quotes** when interpolation needed

```powershell
# ✅ GOOD
$literal = 'This is a simple string'
$interpolated = "Hello, $userName"
$path = "C:\Users\$userName\Documents"

# Escape quotes by doubling
$message = 'It''s a nice day'
$json = "{ ""name"": ""$userName"" }"
```

### Here-Strings

For multi-line strings:

```powershell
$message = @"
This is a here-string.
It can span multiple lines.
Variables like $userName are expanded.
"@

$literal = @'
This is a literal here-string.
Variables like $userName are NOT expanded.
'@
```

**Note**: Opening `@"` or `@'` must be at end of line, closing `"@` or `'@` must be at beginning of line.

## Splatting

Use splatting for commands with many parameters:

```powershell
# ✅ GOOD - Easy to read and modify
$params = @{
    Path        = $logPath
    Filter      = '*.log'
    Recurse     = $true
    ErrorAction = 'Stop'
}
Get-ChildItem @params

# For positional parameters, use array
$args = @(
    $FilePath
    $Destination
)
Copy-Item @args

# Can combine with additional parameters
Get-ChildItem @params -File
```

## Best Practices Summary

### Capitalization
- ✅ PascalCase for all public identifiers
- ✅ lowercase for keywords and operators
- ✅ UPPERCASE for help keywords
- ✅ camelCase optional for private variables

### Layout
- ✅ Use One True Brace Style (OTBS)
- ✅ 4 spaces per indentation level
- ✅ Limit lines to 115 characters
- ✅ Two blank lines around functions
- ✅ Remove trailing whitespace
- ✅ End files with single blank line

### Whitespace
- ✅ Space after commas and semicolons
- ✅ Spaces around operators
- ✅ Space inside `$( )` and `{ }`
- ✅ No space inside `[]` or for unary operators
- ❌ No trailing whitespace

### Structure
- ✅ Always use `[CmdletBinding()]`
- ✅ Order: param, begin, process, end
- ✅ Return objects in `process` block
- ❌ Don't use `return` keyword

### Naming
- ✅ Use approved Verb-Noun format
- ✅ Follow standard parameter names
- ✅ Use singular nouns

### Documentation
- ✅ Include comment-based help
- ✅ Write comments in English
- ✅ Explain WHY, not WHAT
- ✅ Provide examples in help

### Misc
- ✅ Use splatting over backticks
- ✅ Prefer natural line continuation
- ❌ Avoid semicolons as line terminators
- ❌ Avoid backticks for line continuation
