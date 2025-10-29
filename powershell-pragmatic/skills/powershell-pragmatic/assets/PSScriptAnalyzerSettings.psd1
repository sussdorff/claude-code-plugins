# PSScriptAnalyzer Settings for PowerShell Pragmatic Skill
# Based on PoshCode best practices and pragmatic PowerShell patterns
# https://poshcode.gitbook.io/powershell-practice-and-style/

@{
    # Only show Error and Warning severity issues
    # Information-level issues are nice-to-have but not critical
    Severity = @('Error', 'Warning')

    # Exclude rules that conflict with established pragmatic patterns
    ExcludeRules = @(
        # Write-Host is acceptable for UI output in controller scripts
        # Tools should use pipeline, but controllers can use Write-Host
        'PSAvoidUsingWriteHost'

        # Global variables are used intentionally in main script pattern
        # (e.g., $global:CharlyServerPath, $global:Silent)
        'PSAvoidGlobalVars'

        # Plural nouns are sometimes necessary for clarity
        # (e.g., Get-Services vs Get-Service when returning multiple)
        # 'PSUseSingularNouns'  # Uncomment if you want to allow plurals
    )

    # Explicitly include high-priority rules
    IncludeRules = @(
        # Function structure - CRITICAL
        'PSUseCmdletCorrectly'
        'PSUseApprovedVerbs'
        'PSReservedCmdletChar'
        'PSReservedParams'
        'PSAvoidDefaultValueSwitchParameter'

        # Parameters - HIGH PRIORITY
        'PSUseDeclaredVarsMoreThanAssignments'
        'PSAvoidUsingPositionalParameters'

        # Code quality - HIGH PRIORITY
        'PSAvoidUsingCmdletAliases'
        'PSAvoidInvokingEmptyMembers'
        'PSPossibleIncorrectComparisonWithNull'
        'PSPossibleIncorrectUsageOfRedirectionOperator'
        'PSAvoidUsingDoubleQuotesForConstantString'

        # Security - CRITICAL
        'PSAvoidUsingPlainTextForPassword'
        'PSAvoidUsingConvertToSecureStringWithPlainText'
        'PSUsePSCredentialType'
        'PSAvoidUsingInvokeExpression'

        # Error handling
        'PSUseShouldProcessForStateChangingFunctions'

        # Output and return patterns
        'PSAvoidUsingEmptyCatchBlock'
        'PSReturnCorrectTypesForDSCFunctions'
    )

    # Include default rules (recommended)
    IncludeDefaultRules = $true

    # Rule-specific configuration
    Rules = @{
        # One True Brace Style (OTBS)
        # Opening brace on same line, new line after
        PSPlaceOpenBrace = @{
            Enable = $true
            OnSameLine = $true
            NewLineAfter = $true
            IgnoreOneLineBlock = $true
        }

        # Closing brace formatting
        PSPlaceCloseBrace = @{
            Enable = $true
            NewLineAfter = $true
            IgnoreOneLineBlock = $true
            NoEmptyLineBefore = $false
        }

        # Consistent 4-space indentation
        PSUseConsistentIndentation = @{
            Enable = $true
            IndentationSize = 4
            PipelineIndentation = 'IncreaseIndentationForFirstPipeline'
            Kind = 'space'  # Use spaces, not tabs
        }

        # Whitespace consistency
        PSUseConsistentWhitespace = @{
            Enable = $true
            CheckInnerBrace = $true
            CheckOpenBrace = $true
            CheckOpenParen = $true
            CheckOperator = $true
            CheckPipe = $true
            CheckPipeForRedundantWhitespace = $false
            CheckSeparator = $true
            CheckParameter = $false  # Don't enforce space after parameter
        }

        # Align assignment statements in hashtables
        PSAlignAssignmentStatement = @{
            Enable = $true
            CheckHashtable = $true
        }

        # No aliases allowed (use full cmdlet names)
        PSAvoidUsingCmdletAliases = @{
            AllowList = @()  # No exceptions - always use full names
        }

        # Require correct casing for built-in cmdlets/parameters
        PSUseCorrectCasing = @{
            Enable = $true
        }

        # Compatibility checks (optional - adjust based on your environment)
        # PSUseCompatibleCmdlets = @{
        #     Compatibility = @('desktop-5.1.14393.206-windows')
        # }
    }
}
