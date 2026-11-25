<#
.SYNOPSIS
Read-only observation of fixed VeyPanel process image names on native Windows.
.DESCRIPTION
Exit 0: no matching names observed; not a lifetime lock or proof of quiescence.
Exit 2: one or more matching names; stop maintenance and review privately.
Exit 1: observation unavailable or invalid. Never interpret this as clear.
No process is started or terminated. Output contains counts, not paths or PIDs.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
try {
    Import-Module (Join-Path $PSScriptRoot 'PackageProcessObservation.psm1') -Force
    $result = Get-PackageProcessObservation
    $result | ConvertTo-Json -Compress
    if ($result.status -eq 'BLOCKED') { exit 2 }
    if ($result.status -ne 'CLEAR_OBSERVATION') { exit 1 }
    exit 0
} catch {
    [Console]::Error.WriteLine('FAIL: PACKAGE_PROCESS_OBSERVATION_UNAVAILABLE')
    exit 1
}
