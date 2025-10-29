# Error Handling in PowerShell

Comprehensive guide to error handling patterns based on PowerShell best practices.

## Core Principles

### ERR-01: Use -ErrorAction Stop for Cmdlets

When trapping errors, use `-ErrorAction Stop` on cmdlets to generate terminating, trappable exceptions.

```powershell
try {
    Get-Item -Path $FilePath -ErrorAction Stop
    Remove-Item -Path $FilePath -ErrorAction Stop
} catch {
    $errorDetails = $_
    Write-Error "Failed to process file: $($errorDetails.Exception.Message)"
}
```

### ERR-02: Use $ErrorActionPreference for Non-Cmdlets

For non-cmdlet commands, set `$ErrorActionPreference = 'Stop'` before executing, then reset to `'Continue'`.

```powershell
try {
    $ErrorActionPreference = 'Stop'
    $result = & SomeExternalCommand -Arguments $args
    $ErrorActionPreference = 'Continue'

    # Continue with rest of operations
    Process-Result $result
} catch {
    $ErrorActionPreference = 'Continue'
    Handle-Error $_
}
```

**Rationale**: External commands and executables don't respect `-ErrorAction`, so you must change the preference variable.

## Anti-Patterns to Avoid

### ERR-03: Avoid Using Flags

DON'T use flags to handle errors:

```powershell
# ❌ BAD - Flag-based error handling
try {
    $continue = $true
    Do-Something -ErrorAction Stop
} catch {
    $continue = $false
}

if ($continue) {
    Do-This
    Set-That
    Get-Those
}
```

DO put the entire transaction in the Try block:

```powershell
# ✅ GOOD - Transaction-based error handling
try {
    Do-Something -ErrorAction Stop
    Do-This
    Set-That
    Get-Those
} catch {
    Handle-Error $_
}
```

**Benefit**: Easier to follow logic, clearer flow control.

### ERR-04: Avoid Using $?

DON'T use `$?` to examine errors:

```powershell
# ❌ BAD
Do-Something
if (-not $?) {
    Write-Warning "Something went wrong"
}
```

**Problem**: `$?` doesn't mean an error did or didn't occur - it reports whether the last command considered itself successful. You get no details on what actually happened.

**Better approach**: Use try/catch with `-ErrorAction Stop` to get proper error details.

### ERR-05: Avoid Null Variable Testing for Errors

DON'T test for null variables as error conditions:

```powershell
# ❌ BAD
$user = Get-ADUser -Identity $userName
if ($user) {
    $user | Do-Something
} else {
    Write-Warning "Could not get user $userName"
}
```

**Problem**: Logically contorted, harder to debug, doesn't provide actual error information.

**Better approach**: Use try/catch with `-ErrorAction Stop`:

```powershell
# ✅ GOOD
try {
    $user = Get-ADUser -Identity $userName -ErrorAction Stop
    $user | Do-Something
} catch {
    Write-Error "Failed to get user $userName: $_"
}
```

**Exception**: Some commands/technologies won't produce terminating exceptions, so null testing may be the only option.

### ERR-06: Copy $_ Immediately in Catch

Within a `catch` block, `$_` contains the last error (as does `$Error[0]`). **Immediately copy** them into your own variable:

```powershell
try {
    Do-Something -ErrorAction Stop
} catch {
    # Copy immediately - executing more commands can hijack $_
    $errorDetails = $_

    # Now safe to execute additional commands
    Write-Error "Operation failed: $($errorDetails.Exception.Message)"
    Write-Verbose "Stack trace: $($errorDetails.ScriptStackTrace)"

    # Re-throw or handle as needed
    throw $errorDetails
}
```

**Rationale**: Executing additional commands can cause `$_` to get "hijacked" or `$Error[0]` to contain a different error.

## Advanced Error Handling

### Using PSCmdlet Methods

For advanced functions, use `$PSCmdlet` methods instead of `Write-Error` or `throw`:

```powershell
function Get-UserData {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$UserName
    )

    try {
        $user = Get-ADUser -Identity $UserName -ErrorAction Stop
    } catch {
        $errorDetails = $_

        # Use PSCmdlet.WriteError for non-terminating errors
        $PSCmdlet.WriteError(
            [System.Management.Automation.ErrorRecord]::new(
                $errorDetails.Exception,
                'UserNotFound',
                [System.Management.Automation.ErrorCategory]::ObjectNotFound,
                $UserName
            )
        )
        return
    }

    # Or use PSCmdlet.ThrowTerminatingError for terminating errors
    if (-not $user.Enabled) {
        $exception = [System.InvalidOperationException]::new("User $UserName is disabled")
        $errorRecord = [System.Management.Automation.ErrorRecord]::new(
            $exception,
            'UserDisabled',
            [System.Management.Automation.ErrorCategory]::InvalidOperation,
            $UserName
        )
        $PSCmdlet.ThrowTerminatingError($errorRecord)
    }

    return $user
}
```

**Benefits**:
- Better integration with PowerShell error streams
- More control over error categories
- Proper error record creation with custom error IDs

### Cleanup with Finally

Use `finally` blocks for guaranteed cleanup:

```powershell
$tempFile = New-TemporaryFile
$connection = $null

try {
    # Establish resources
    $connection = Connect-Database -Server $server
    $data = Get-Content -Path $tempFile

    # Process data
    Invoke-DatabaseQuery -Connection $connection -Query $query

    # Early return still triggers finally
    if ($someCondition) {
        return $result
    }
} catch {
    $errorDetails = $_
    Write-Error "Operation failed: $($errorDetails.Exception.Message)"
} finally {
    # Guaranteed cleanup
    if ($connection) {
        Disconnect-Database -Connection $connection
    }
    if (Test-Path $tempFile) {
        Remove-Item -Path $tempFile -ErrorAction SilentlyContinue
    }
}
```

**When to use**:
- Resource cleanup (files, connections, handles)
- Logging operation completion
- Resetting state
- Any code that MUST run regardless of success/failure

## Error Handling for Pipelines

When accepting pipeline input, handle errors carefully to avoid breaking the pipeline:

```powershell
function Process-Item {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
        [string]$Path
    )

    process {
        try {
            # Process this pipeline item
            $item = Get-Item -Path $Path -ErrorAction Stop
            $item | Do-Something
        } catch {
            # Log error but don't break pipeline
            $errorDetails = $_
            Write-Warning "Failed to process $Path: $($errorDetails.Exception.Message)"

            # Optionally write non-terminating error
            $PSCmdlet.WriteError($_)

            # Continue to next pipeline item
            return
        }
    }
}

# Usage
Get-ChildItem *.txt | Process-Item  # Continues even if some items fail
```

## Practical Patterns

### Pattern: Retry Logic

```powershell
function Invoke-WithRetry {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$ScriptBlock,

        [Parameter()]
        [int]$MaxRetries = 3,

        [Parameter()]
        [int]$DelaySeconds = 2
    )

    $attempt = 0
    while ($attempt -lt $MaxRetries) {
        try {
            $attempt++
            & $ScriptBlock
            return  # Success
        } catch {
            $errorDetails = $_
            if ($attempt -lt $MaxRetries) {
                Write-Verbose "Attempt $attempt failed, retrying in $DelaySeconds seconds..."
                Start-Sleep -Seconds $DelaySeconds
            } else {
                Write-Error "All $MaxRetries attempts failed: $($errorDetails.Exception.Message)"
                throw $errorDetails
            }
        }
    }
}

# Usage
Invoke-WithRetry -ScriptBlock {
    Invoke-RestMethod -Uri $apiEndpoint -ErrorAction Stop
} -MaxRetries 3
```

### Pattern: Validation with Custom Errors

```powershell
function Set-UserConfig {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ConfigPath,

        [Parameter(Mandatory = $true)]
        [hashtable]$Settings
    )

    # Validate configuration
    if (-not (Test-Path -Path $ConfigPath)) {
        $exception = [System.IO.FileNotFoundException]::new("Configuration file not found: $ConfigPath")
        $errorRecord = [System.Management.Automation.ErrorRecord]::new(
            $exception,
            'ConfigFileNotFound',
            [System.Management.Automation.ErrorCategory]::ObjectNotFound,
            $ConfigPath
        )
        $PSCmdlet.ThrowTerminatingError($errorRecord)
    }

    # Validate settings
    $requiredKeys = @('Server', 'Database', 'Port')
    foreach ($key in $requiredKeys) {
        if (-not $Settings.ContainsKey($key)) {
            $exception = [System.ArgumentException]::new("Missing required setting: $key")
            $errorRecord = [System.Management.Automation.ErrorRecord]::new(
                $exception,
                'MissingRequiredSetting',
                [System.Management.Automation.ErrorCategory]::InvalidArgument,
                $key
            )
            $PSCmdlet.ThrowTerminatingError($errorRecord)
        }
    }

    # Apply settings
    $Settings | ConvertTo-Json | Set-Content -Path $ConfigPath
}
```

### Pattern: Aggregate Error Handling

```powershell
function Process-MultipleItems {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Items
    )

    $errors = @()
    $successCount = 0

    foreach ($item in $Items) {
        try {
            Process-SingleItem -Item $item -ErrorAction Stop
            $successCount++
        } catch {
            $errors += [PSCustomObject]@{
                Item      = $item
                Error     = $_.Exception.Message
                Timestamp = Get-Date
            }
        }
    }

    # Report results
    Write-Verbose "Processed $successCount of $($Items.Count) items successfully"

    if ($errors.Count -gt 0) {
        Write-Warning "Encountered $($errors.Count) errors:"
        $errors | Format-Table -AutoSize
    }

    # Return errors for further processing
    return $errors
}
```

## Error Categories

Use appropriate error categories when creating error records:

- **ObjectNotFound**: Resource doesn't exist
- **InvalidArgument**: Parameter validation failed
- **InvalidOperation**: Operation not valid in current state
- **OperationStopped**: Operation was stopped/cancelled
- **PermissionDenied**: Insufficient permissions
- **ResourceExists**: Resource already exists (conflict)
- **ResourceUnavailable**: Resource exists but unavailable
- **NotImplemented**: Feature not implemented
- **AuthenticationError**: Authentication failed
- **SecurityError**: Security violation

## Best Practices Summary

1. ✅ Always use `-ErrorAction Stop` with cmdlets in try/catch
2. ✅ Set `$ErrorActionPreference = 'Stop'` for external commands
3. ✅ Put entire transaction in try block (avoid flags)
4. ✅ Copy `$_` immediately in catch blocks
5. ✅ Use `finally` for guaranteed cleanup
6. ✅ Use `$PSCmdlet.WriteError()` for non-terminating errors
7. ✅ Use `$PSCmdlet.ThrowTerminatingError()` for terminating errors
8. ❌ Don't test `$?` for errors
9. ❌ Don't test null variables as error conditions (when avoidable)
10. ❌ Don't use `throw` in advanced functions (use PSCmdlet methods)
