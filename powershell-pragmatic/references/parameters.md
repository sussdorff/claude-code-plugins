# Parameter Best Practices

Comprehensive guide to PowerShell parameters, validation, and parameter sets.

## Basic Parameter Declaration

```powershell
function Get-Example {
    [CmdletBinding()]
    param(
        # Mandatory parameter
        [Parameter(Mandatory = $true)]
        [string]$Name,

        # Optional parameter with default
        [Parameter()]
        [int]$Count = 10,

        # Switch parameter
        [Parameter()]
        [switch]$Force
    )
}
```

## Parameter Attributes

### Parameter Attribute Properties

```powershell
param(
    [Parameter(
        Mandatory = $true,                    # Required parameter
        Position = 0,                          # Positional (first position)
        ValueFromPipeline = $true,             # Accept from pipeline
        ValueFromPipelineByPropertyName = $true, # Accept by property name
        ValueFromRemainingArguments = $true,   # Collect remaining args
        HelpMessage = 'Enter a computer name'  # Help text
    )]
    [string]$ComputerName
)
```

**Best practices**:
- Be generous with `ValueFromPipelineByPropertyName` - enables easy pipeline scenarios
- Use `Position` sparingly - named parameters are more readable
- Always include `HelpMessage` for mandatory parameters

### Aliases for Pipeline Binding

Use aliases to enhance pipeline compatibility:

```powershell
param(
    [Parameter(ValueFromPipelineByPropertyName = $true)]
    [Alias('PSComputerName', 'CN', 'MachineName')]
    [string]$ComputerName
)

# Now works with objects that have any of these properties:
# - ComputerName
# - PSComputerName
# - CN
# - MachineName
```

## Validation Attributes

### ValidateNotNullOrEmpty

Ensures parameter is not null, empty string, or empty collection:

```powershell
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$UserName
)

# Rejects: $null, "", @()
# Accepts: Any non-empty value
```

### ValidateNotNull

Allows empty strings/collections but not null:

```powershell
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNull()]
    $Data
)

# Rejects: $null
# Accepts: "", @(), any value
```

**Use case**: When empty string or empty array are valid inputs.

### AllowNull / AllowEmptyString / AllowEmptyCollection

Override default validation for mandatory parameters:

```powershell
param(
    # Allow null for mandatory parameter (unusual but valid)
    [Parameter(Mandatory = $true)]
    [AllowNull()]
    [string]$OptionalConfig,

    # Allow empty string
    [Parameter(Mandatory = $true)]
    [AllowEmptyString()]
    [string]$Description,

    # Allow empty array
    [Parameter(Mandatory = $true)]
    [AllowEmptyCollection()]
    [string[]]$Tags
)
```

### ValidateSet

Restrict to specific values:

```powershell
param(
    [Parameter()]
    [ValidateSet('Low', 'Medium', 'High', 'Critical')]
    [string]$Priority = 'Medium',

    # Case-insensitive by default
    [Parameter()]
    [ValidateSet('Red', 'Green', 'Blue', IgnoreCase = $true)]
    [string]$Color
)
```

**Tab completion**: ValidateSet automatically provides tab completion in PowerShell 5.0+

**Dynamic ValidateSet** (PowerShell 5.0+):

```powershell
class ValidateServerNames : System.Management.Automation.IValidateSetValuesGenerator {
    [string[]] GetValidValues() {
        return (Get-ADComputer -Filter *).Name
    }
}

param(
    [Parameter()]
    [ValidateSet([ValidateServerNames])]
    [string]$ServerName
)
```

### ValidateRange

Numeric or date range validation:

```powershell
param(
    # Numeric range
    [Parameter()]
    [ValidateRange(1, 100)]
    [int]$Percentage,

    # Date range
    [Parameter()]
    [ValidateRange([datetime]'2020-01-01', [datetime]'2025-12-31')]
    [datetime]$EventDate,

    # Positive numbers only
    [Parameter()]
    [ValidateRange('Positive')]
    [int]$Count
)
```

**Special values**: `'Positive'`, `'Negative'`, `'NonNegative'`, `'NonPositive'`

### ValidateLength

String length validation:

```powershell
param(
    # Password must be 8-128 characters
    [Parameter()]
    [ValidateLength(8, 128)]
    [string]$Password,

    # Minimum length only
    [Parameter()]
    [ValidateLength(1, [int]::MaxValue)]
    [string]$Description
)
```

### ValidateCount

Array element count validation:

```powershell
param(
    # Require 1-5 items
    [Parameter()]
    [ValidateCount(1, 5)]
    [string[]]$Items,

    # At least one item
    [Parameter()]
    [ValidateCount(1, [int]::MaxValue)]
    [string[]]$RequiredItems
)
```

### ValidatePattern

Regular expression validation:

```powershell
param(
    # Email address pattern
    [Parameter()]
    [ValidatePattern('^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$')]
    [string]$EmailAddress,

    # IP address pattern
    [Parameter()]
    [ValidatePattern('^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')]
    [string]$IPAddress,

    # Custom error message (PowerShell 6.0+)
    [Parameter()]
    [ValidatePattern('^[A-Z]{2,3}-[0-9]{4,6}$',
        ErrorMessage = 'Ticket number must be in format: ABC-12345')]
    [string]$TicketNumber
)
```

### ValidateScript

Custom validation logic:

```powershell
param(
    # File must exist
    [Parameter()]
    [ValidateScript({ Test-Path $_ })]
    [string]$FilePath,

    # Date must be in the future
    [Parameter()]
    [ValidateScript({ $_ -gt (Get-Date) })]
    [datetime]$FutureDate,

    # Custom error message (PowerShell 6.0+)
    [Parameter()]
    [ValidateScript(
        { Test-Path $_ },
        ErrorMessage = 'File {0} does not exist'
    )]
    [string]$ConfigPath,

    # Complex validation
    [Parameter()]
    [ValidateScript({
        if ($_ -lt 0 -or $_ -gt 100) {
            throw "Value must be between 0 and 100"
        }
        if ($_ % 10 -ne 0) {
            throw "Value must be a multiple of 10"
        }
        return $true
    })]
    [int]$MultipleOfTen
)
```

**Important**: `$_` refers to the parameter value being validated.

### ValidateDrive

Validates that path uses specific drive:

```powershell
param(
    # Must be on C: drive
    [Parameter()]
    [ValidateDrive('C')]
    [string]$SystemPath,

    # Multiple drives allowed
    [Parameter()]
    [ValidateDrive('C', 'D', 'E')]
    [string]$DataPath
)
```

### ValidateUserDrive (PowerShell 6.0+)

Ensures path is on user-accessible drive (not system drives):

```powershell
param(
    [Parameter()]
    [ValidateUserDrive()]
    [string]$UserFilePath
)
```

## Parameter Types

### String Parameters

```powershell
param(
    # Simple string
    [string]$Name,

    # String array
    [string[]]$Names,

    # Be careful with pipeline - [string] converts objects to strings
    [Parameter(ValueFromPipeline = $true)]
    [string]$InputObject  # Gets object.ToString(), not the object itself
)
```

**Warning**: Using `[string]` or `[object]` for pipeline input can be problematic. Be specific about types when possible.

### Switch Parameters

```powershell
param(
    # Boolean flag
    [switch]$Force,

    [switch]$Recurse,

    [switch]$WhatIf
)

# Usage:
# Get-Example -Force
# Get-Example -Force:$false
# Get-Example -Force:$true
```

**Never use** `[bool]` **for flags** - always use `[switch]`.

### Credential Parameters

```powershell
param(
    # Standard credential parameter
    [Parameter()]
    [PSCredential]
    [System.Management.Automation.Credential()]
    $Credential
)

# Usage:
# Get-Example -Credential (Get-Credential)
# Get-Example -Credential 'DOMAIN\User'  # Prompts for password
```

**Best practice**: Always name credential parameters `$Credential` (not `$Cred`, `$Credentials`, etc.).

### Numeric Parameters

```powershell
param(
    [int]$Count,
    [long]$LargeNumber,
    [double]$Percentage,
    [decimal]$Money
)
```

### Enum Parameters

```powershell
enum LogLevel {
    Debug
    Info
    Warning
    Error
    Critical
}

param(
    [LogLevel]$Level = [LogLevel]::Info
)

# Usage:
# Get-Example -Level Error
# Get-Example -Level ([LogLevel]::Critical)
```

### Collection Parameters

```powershell
param(
    # Array
    [string[]]$Names,

    # ArrayList
    [System.Collections.ArrayList]$Items,

    # Generic List
    [System.Collections.Generic.List[string]]$Strings,

    # Hashtable
    [hashtable]$Config,

    # Dictionary
    [System.Collections.Generic.Dictionary[string, object]]$Settings
)
```

## Parameter Sets

Use parameter sets when parameters are mutually exclusive:

```powershell
function Get-Data {
    [CmdletBinding(DefaultParameterSetName = 'ByName')]
    param(
        [Parameter(Mandatory = $true, ParameterSetName = 'ByName')]
        [string]$Name,

        [Parameter(Mandatory = $true, ParameterSetName = 'ById')]
        [int]$Id,

        [Parameter(Mandatory = $true, ParameterSetName = 'ByDate')]
        [datetime]$Date,

        # Common parameter available to all sets
        [Parameter()]
        [switch]$IncludeDetails
    )

    switch ($PSCmdlet.ParameterSetName) {
        'ByName' {
            Get-DataByName -Name $Name
        }
        'ById' {
            Get-DataById -Id $Id
        }
        'ByDate' {
            Get-DataByDate -Date $Date
        }
    }
}

# Usage:
# Get-Data -Name 'Test'      # ByName set
# Get-Data -Id 123           # ById set
# Get-Data -Date '2024-01-01' # ByDate set
# Get-Data -Name 'Test' -Id 123  # ERROR: Can't mix sets
```

**Best practices**:
- Always specify `DefaultParameterSetName`
- Use `$PSCmdlet.ParameterSetName` to determine which set was used
- Include `[OutputType()]` per parameter set if outputs differ

### Parameter Set with Multiple Parameters

```powershell
function Connect-Service {
    [CmdletBinding(DefaultParameterSetName = 'Credential')]
    [OutputType([PSCustomObject], ParameterSetName = 'Credential')]
    [OutputType([PSCustomObject], ParameterSetName = 'Token')]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Server,

        [Parameter(Mandatory = $true, ParameterSetName = 'Credential')]
        [PSCredential]$Credential,

        [Parameter(Mandatory = $true, ParameterSetName = 'Token')]
        [string]$AccessToken,

        [Parameter(ParameterSetName = 'Token')]
        [datetime]$TokenExpiry,

        # Available to all sets
        [Parameter()]
        [int]$Port = 443
    )

    if ($PSCmdlet.ParameterSetName -eq 'Credential') {
        # Authenticate with credential
    } else {
        # Authenticate with token
    }
}
```

## Dynamic Parameters

Create parameters that only appear based on conditions:

```powershell
function Get-DynamicExample {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('File', 'Directory', 'Registry')]
        [string]$Type
    )

    dynamicparam {
        $paramDictionary = [System.Management.Automation.RuntimeDefinedParameterDictionary]::new()

        # Add parameter only when Type is 'File'
        if ($Type -eq 'File') {
            $attributes = [System.Management.Automation.ParameterAttribute]::new()
            $attributes.Mandatory = $true

            $attributeCollection = [System.Collections.ObjectModel.Collection[System.Attribute]]::new()
            $attributeCollection.Add($attributes)

            $param = [System.Management.Automation.RuntimeDefinedParameter]::new(
                'Extension',
                [string],
                $attributeCollection
            )

            $paramDictionary.Add('Extension', $param)
        }

        return $paramDictionary
    }

    process {
        if ($PSBoundParameters.ContainsKey('Extension')) {
            Write-Host "File extension: $($PSBoundParameters['Extension'])"
        }
    }
}

# Usage:
# Get-DynamicExample -Type File -Extension '.txt'  # Extension parameter appears
# Get-DynamicExample -Type Directory               # Extension not available
```

## Standard Parameter Names

Follow PowerShell conventions for common parameters:

| Concept | Use | Don't Use |
|---------|-----|-----------|
| Computer | `$ComputerName` | `$Computer`, `$Server`, `$Machine`, `$Host` |
| File | `$Path` or `$FilePath` | `$File`, `$FileName` |
| Credentials | `$Credential` | `$Cred`, `$Credentials` |
| Confirmation | `$Confirm` | `$Confirmed` |
| Force | `$Force` | `$Forced`, `$Override` |
| Location | `$Path` | `$Location`, `$Dir` |

Run `Get-Command *-* | Select-Object -ExpandProperty Parameters` to see what built-in cmdlets use.

## ValueFromRemainingArguments

Collect extra arguments:

```powershell
function Invoke-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    & $Command @Arguments
}

# Usage:
# Invoke-Command -Command 'Get-Process' -Name 'powershell' -Id 1234
# Arguments becomes: @('-Name', 'powershell', '-Id', '1234')
```

## SupportsShouldProcess

Add `-WhatIf` and `-Confirm` support:

```powershell
function Remove-CustomItem {
    [CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if ($PSCmdlet.ShouldProcess($Path, 'Delete item')) {
        Remove-Item -Path $Path -Force
    }
}

# Usage:
# Remove-CustomItem -Path C:\test.txt -WhatIf  # Shows what would happen
# Remove-CustomItem -Path C:\test.txt -Confirm # Prompts for confirmation
```

**ConfirmImpact levels**: `'None'`, `'Low'`, `'Medium'`, `'High'`

- `'High'`: Always prompts (unless `-Confirm:$false`)
- `'Medium'`: Prompts if `$ConfirmPreference -le 'Medium'`
- `'Low'`: Rarely prompts

## Transformation Attributes

### ArgumentCompleter

Provide custom tab completion:

```powershell
param(
    [Parameter()]
    [ArgumentCompleter({
        param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)

        $completions = @('Option1', 'Option2', 'Option3')
        $completions | Where-Object { $_ -like "$wordToComplete*" }
    })]
    [string]$Choice
)
```

### ArgumentTransformations

Custom parameter transformation:

```powershell
class ToLowerTransformAttribute : System.Management.Automation.ArgumentTransformationAttribute {
    [object] Transform([System.Management.Automation.EngineIntrinsics]$engineIntrinsics, [object]$inputData) {
        return $inputData.ToString().ToLower()
    }
}

param(
    [ToLowerTransform()]
    [string]$Name
)

# Usage:
# Get-Example -Name 'TEST'  # Automatically converted to 'test'
```

## Best Practices Summary

1. ✅ Use `[CmdletBinding()]` on all functions
2. ✅ Use validation attributes instead of manual validation
3. ✅ Use `[switch]` for boolean flags, never `[bool]`
4. ✅ Name credential parameters `$Credential`
5. ✅ Follow standard parameter names (`$ComputerName`, `$Path`, etc.)
6. ✅ Use `DefaultParameterSetName` when using parameter sets
7. ✅ Be generous with `ValueFromPipelineByPropertyName`
8. ✅ Use `[OutputType()]` attribute
9. ✅ Include `HelpMessage` for mandatory parameters
10. ✅ Use parameter aliases to enhance pipeline compatibility
11. ❌ Don't use `[string]` or `[object]` for pipeline input when more specific types work
12. ❌ Don't validate parameters in function body when attributes can do it
