# Performance Optimization in PowerShell

Guide to writing performant PowerShell code based on best practices and real-world patterns.

## Core Principles

### PERF-01: If Performance Matters, Test It

PowerShell has numerous performance quirks. If you're aware of multiple techniques and dealing with large datasets, **measure** performance using `Measure-Command` or the Profiler module.

```powershell
# Example: foreach vs ForEach-Object
Measure-Command {
    foreach ($result in Get-ChildItem) {
        $result.Name
    }
}

Measure-Command {
    Get-ChildItem | ForEach-Object {
        $_.Name
    }
}
```

**Key insight**: The `foreach` language construct is typically faster than piping to `ForEach-Object`, but **always measure** on the hardware and PowerShell version that matters to you.

### PERF-02: Balance Performance with Readability

Performance is not the only consideration. If a script processes 10 items, a 30% performance improvement won't add up to significant time.

**Trade-offs**: It's okay to use slower-performing techniques that are easier to read, understand, and maintain.

```powershell
# Slower but very readable
$content = Get-Content -Path $file
foreach ($line in $content) {
    Do-Something -Input $line
}

# Faster (streaming) but less obvious for beginners
Get-Content -Path $file | ForEach-Object {
    Do-Something -Input $_
}
```

**Consider both**:
- Aesthetics and readability
- Performance and scalability
- Team familiarity with patterns
- Maintenance burden

### PERF-03: Performance Hierarchy

General rule of thumb (always test to confirm):

1. **Language features** > .NET Framework methods > Script > Pipeline
2. Compiled .NET methods > PowerShell functions
3. Simple PowerShell script > Calling cmdlets in loops

```powershell
# Fastest: Language feature
$arr -contains $value

# Fast: .NET method
$arr.Contains($value)

# Slower: Cmdlet call
Where-Object { $_ -eq $value }
```

**Note**: Cmdlet overhead is significant. Language constructs and .NET methods are usually faster unless cmdlets do substantial work.

## Array Operations

### Anti-Pattern: Array Concatenation in Loops

```powershell
# ❌ VERY SLOW - Creates new array each iteration
$results = @()
foreach ($item in 1..10000) {
    $results += $item
}
```

**Problem**: Arrays are fixed-size in .NET. `+=` creates a **new** array, copies all elements, then adds the new one. For 10,000 items, this is O(n²) complexity.

### Solution 1: Use ArrayList

```powershell
# ✅ FAST - Dynamic resizing
$results = [System.Collections.ArrayList]::new()
foreach ($item in 1..10000) {
    [void]$results.Add($item)
}
```

**Note**: Use `[void]` to suppress Add() return value.

### Solution 2: Use Generic List

```powershell
# ✅ FAST - Type-safe and dynamic
$results = [System.Collections.Generic.List[int]]::new()
foreach ($item in 1..10000) {
    $results.Add($item)
}
```

### Solution 3: Use Pipeline

```powershell
# ✅ BEST - Most PowerShell-idiomatic
$results = 1..10000 | ForEach-Object {
    Process-Item $_
}
```

**Benefit**: PowerShell handles collection for you.

## Pipeline Performance

### When to Use Pipeline

```powershell
# ✅ GOOD - Large dataset, streaming
Get-ChildItem -Path C:\Logs -Recurse |
    Where-Object { $_.Length -gt 1GB } |
    Remove-Item -Force
```

**Benefits**:
- Memory efficient (streaming)
- Readable
- Handles large datasets well

### When to Avoid Pipeline

```powershell
# ⚠️ SLOW - Pipeline overhead for small operations
1..10 | ForEach-Object { $_ * 2 }

# ✅ FASTER - Language construct
foreach ($i in 1..10) { $i * 2 }
```

**Rule of thumb**: For small datasets or simple operations, language constructs (`foreach`, `if`, `switch`) are faster than pipeline cmdlets.

### Pipeline Blocking Cmdlets

Some cmdlets block the pipeline (must receive all input before outputting):

- `Sort-Object`
- `Group-Object`
- `Measure-Object`
- `Select-Object -Last`
- `Select-Object -Unique`

```powershell
# ❌ BLOCKS - Must load entire file into memory
Get-Content -Path huge.log |
    Sort-Object |
    Select-Object -First 10

# ✅ BETTER - Filter first
Get-Content -Path huge.log |
    Where-Object { $_ -match 'ERROR' } |
    Select-Object -First 10
```

## File I/O

### Reading Large Files

```powershell
# ❌ SLOW - Loads entire file into memory
$content = Get-Content -Path huge.log
foreach ($line in $content) {
    Process-Line $line
}

# ✅ STREAMING - One line at a time
Get-Content -Path huge.log | ForEach-Object {
    Process-Line $_
}

# ✅ FASTEST - .NET StreamReader for maximum performance
$sr = [System.IO.StreamReader]::new($filePath)
try {
    while ($null -ne ($line = $sr.ReadLine())) {
        Process-Line $line
    }
} finally {
    $sr.Dispose()
}
```

### Reading Files with -Raw

```powershell
# For files you need as a single string
$content = Get-Content -Path file.txt -Raw

# Much faster than:
$content = (Get-Content -Path file.txt) -join "`n"
```

### Writing Files

```powershell
# ❌ SLOW - Multiple file writes
foreach ($line in $data) {
    Add-Content -Path $file -Value $line
}

# ✅ FAST - Single file write
$data | Set-Content -Path $file

# ✅ FASTEST - .NET StreamWriter
$sw = [System.IO.StreamWriter]::new($filePath)
try {
    foreach ($line in $data) {
        $sw.WriteLine($line)
    }
} finally {
    $sw.Dispose()
}
```

## String Operations

### String Concatenation

```powershell
# ❌ SLOW - Creates new string each iteration
$result = ""
foreach ($item in 1..1000) {
    $result += "Line $item`n"
}

# ✅ FAST - StringBuilder
$sb = [System.Text.StringBuilder]::new()
foreach ($item in 1..1000) {
    [void]$sb.AppendLine("Line $item")
}
$result = $sb.ToString()

# ✅ ALSO GOOD - Array join
$lines = foreach ($item in 1..1000) {
    "Line $item"
}
$result = $lines -join "`n"
```

### String Comparison

```powershell
# Faster
$string -eq 'value'

# Slower
$string.Equals('value')

# Case-insensitive comparison
$string -ieq 'value'      # PowerShell operator
$string.ToLower() -eq 'value'.ToLower()  # Slower
```

## Filtering and Comparison

### Where-Object vs .Where() Method

```powershell
# ❌ SLOWER - Cmdlet
$results = Get-Process | Where-Object { $_.CPU -gt 100 }

# ✅ FASTER - .Where() method (PowerShell 4.0+)
$results = (Get-Process).Where({ $_.CPU -gt 100 })

# ✅ FASTEST - Language construct
$processes = Get-Process
$results = foreach ($proc in $processes) {
    if ($proc.CPU -gt 100) {
        $proc
    }
}
```

### Select-Object vs .ForEach() Method

```powershell
# ❌ SLOWER - Cmdlet
$names = Get-Process | Select-Object -ExpandProperty Name

# ✅ FASTER - .ForEach() method (PowerShell 4.0+)
$names = (Get-Process).ForEach('Name')

# ✅ ALSO FAST - Property access in foreach
$names = foreach ($proc in Get-Process) {
    $proc.Name
}
```

## Hashtable Lookups

### Use Hashtables for Lookups

```powershell
# ❌ VERY SLOW - Array search in loop
$users = @(
    [PSCustomObject]@{ Id = 1; Name = 'Alice' }
    [PSCustomObject]@{ Id = 2; Name = 'Bob' }
    # ... thousands more
)

foreach ($id in $idsToFind) {
    $user = $users | Where-Object { $_.Id -eq $id }  # O(n) lookup
}

# ✅ FAST - Hashtable lookup
$userHash = @{}
foreach ($user in $users) {
    $userHash[$user.Id] = $user
}

foreach ($id in $idsToFind) {
    $user = $userHash[$id]  # O(1) lookup
}
```

**Performance**: Hashtable lookups are O(1) vs array searches at O(n).

## Regular Expressions

### Pre-compile Regex for Repeated Use

```powershell
# ❌ SLOW - Recompiles regex each iteration
foreach ($line in $lines) {
    if ($line -match '\b[A-Z]{2,3}-\d{4,6}\b') {
        # Process
    }
}

# ✅ FASTER - Pre-compiled regex
$regex = [regex]::new('\b[A-Z]{2,3}-\d{4,6}\b', [System.Text.RegularExpressions.RegexOptions]::Compiled)
foreach ($line in $lines) {
    if ($regex.IsMatch($line)) {
        # Process
    }
}
```

## Avoid Unnecessary Type Conversions

```powershell
# ❌ SLOW - Repeated conversions
foreach ($item in $items) {
    $number = [int]$item.Value
    $doubled = $number * 2
}

# ✅ FASTER - Convert once if needed
foreach ($item in $items) {
    $doubled = $item.Value * 2  # PowerShell converts automatically
}
```

## Language Feature Comparisons

### Foreach vs ForEach-Object

```powershell
# Generally faster: Language construct
foreach ($item in $collection) {
    Process-Item $item
}

# Generally slower: Cmdlet (but supports pipeline streaming)
$collection | ForEach-Object {
    Process-Item $_
}
```

**When to use ForEach-Object**:
- Large datasets (streaming)
- Already in pipeline
- Need Begin/Process/End blocks

**When to use foreach**:
- Small to medium datasets
- Performance critical
- Structured programming preferred

### Switch vs If/ElseIf

```powershell
# For many conditions, switch is often faster
switch ($value) {
    1 { 'One' }
    2 { 'Two' }
    3 { 'Three' }
    default { 'Other' }
}

# vs
if ($value -eq 1) { 'One' }
elseif ($value -eq 2) { 'Two' }
elseif ($value -eq 3) { 'Three' }
else { 'Other' }
```

## Parallel Processing

### ForEach-Object -Parallel (PowerShell 7+)

```powershell
# Process items in parallel
1..10 | ForEach-Object -Parallel {
    Start-Sleep -Seconds 2
    "Processed $_"
} -ThrottleLimit 5
```

**Use cases**:
- CPU-intensive tasks
- I/O-bound operations
- Independent processing (no shared state)

### Runspaces for Maximum Control

```powershell
$runspacePool = [runspacefactory]::CreateRunspacePool(1, 5)
$runspacePool.Open()

$jobs = foreach ($item in $items) {
    $ps = [powershell]::Create().AddScript({
        param($data)
        # Process data
    }).AddArgument($item)

    $ps.RunspacePool = $runspacePool

    [PSCustomObject]@{
        PowerShell = $ps
        Handle     = $ps.BeginInvoke()
    }
}

# Collect results
$results = foreach ($job in $jobs) {
    $job.PowerShell.EndInvoke($job.Handle)
    $job.PowerShell.Dispose()
}

$runspacePool.Close()
$runspacePool.Dispose()
```

## Cmdlet vs .NET Method Examples

### Test-Path vs [System.IO.File]::Exists

```powershell
# Slower but more features
if (Test-Path -Path $file -PathType Leaf) { }

# Faster for simple existence check
if ([System.IO.File]::Exists($file)) { }
```

### Get-Content vs [System.IO.File]::ReadAllText

```powershell
# Slower - PowerShell cmdlet
$content = Get-Content -Path $file -Raw

# Faster - .NET method
$content = [System.IO.File]::ReadAllText($file)
```

**When to use .NET**:
- Performance critical paths
- Simple operations
- Document why in comments

**When to use cmdlets**:
- Need PowerShell features (pipeline, -WhatIf, etc.)
- Complex operations
- Readability more important than performance

## Measuring Performance

### Measure-Command

```powershell
$time1 = Measure-Command {
    # Method 1
}

$time2 = Measure-Command {
    # Method 2
}

Write-Host "Method 1: $($time1.TotalMilliseconds)ms"
Write-Host "Method 2: $($time2.TotalMilliseconds)ms"
```

### Multiple Iterations

```powershell
$iterations = 100
$time = Measure-Command {
    foreach ($i in 1..$iterations) {
        # Code to test
    }
}

$average = $time.TotalMilliseconds / $iterations
Write-Host "Average time: ${average}ms"
```

### Using System.Diagnostics.Stopwatch

```powershell
$sw = [System.Diagnostics.Stopwatch]::StartNew()

# Code to measure

$sw.Stop()
Write-Host "Elapsed: $($sw.Elapsed.TotalMilliseconds)ms"
```

## Real-World Example: Optimize Log Processing

```powershell
# ❌ SLOW VERSION
function Process-Logs {
    param([string]$LogPath)

    $errors = @()
    $content = Get-Content -Path $LogPath

    foreach ($line in $content) {
        if ($line -match 'ERROR') {
            $errors += $line  # Array concatenation
        }
    }

    return $errors
}

# ✅ FAST VERSION
function Process-Logs {
    param([string]$LogPath)

    # Stream file, use pipeline, let PowerShell collect
    Get-Content -Path $LogPath |
        Where-Object { $_ -match 'ERROR' }
}

# ✅ FASTEST VERSION (for huge files)
function Process-Logs {
    param([string]$LogPath)

    $errors = [System.Collections.Generic.List[string]]::new()
    $sr = [System.IO.StreamReader]::new($LogPath)
    $regex = [regex]::new('ERROR', [System.Text.RegularExpressions.RegexOptions]::Compiled)

    try {
        while ($null -ne ($line = $sr.ReadLine())) {
            if ($regex.IsMatch($line)) {
                $errors.Add($line)
            }
        }
    } finally {
        $sr.Dispose()
    }

    return $errors.ToArray()
}
```

## Best Practices Summary

1. ✅ Always measure performance if it matters (use `Measure-Command`)
2. ✅ Balance performance with readability
3. ✅ Use ArrayList or Generic.List instead of array concatenation
4. ✅ Use hashtables for lookups instead of array searches
5. ✅ Stream large files, don't load entirely into memory
6. ✅ Use `foreach` instead of `ForEach-Object` for small datasets
7. ✅ Pre-compile regex for repeated use
8. ✅ Use StringBuilder for string concatenation in loops
9. ✅ Consider .NET methods for performance-critical simple operations
10. ✅ Document when using .NET methods over PowerShell cmdlets
11. ⚠️ Remember: foreach (language) > .Where() > Where-Object (cmdlet)
12. ⚠️ Remember: .ForEach() > Select-Object for property extraction
13. ❌ Don't append to arrays in loops
14. ❌ Don't recompile regex in loops
15. ❌ Don't load entire large files with Get-Content without -Raw
