<#
.SYNOPSIS
Read-only Windows Storage Provider diagnostic; not a SMART health verdict.
.PARAMETER AsJson
Print the sanitized report as JSON rather than a table.
.EXAMPLE
powershell.exe -NoProfile -File scripts/Get-StorageHealth.ps1 -AsJson
#>
[CmdletBinding()]
param([switch]$AsJson, [Alias('h','Help')][switch]$Usage)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
if ($Usage) { Write-Output 'Usage: Get-StorageHealth.ps1 [-AsJson] [-Help]'; exit 0 }
if ($env:OS -ne 'Windows_NT') { Write-Error 'Windows required'; exit 2 }
Import-Module (Join-Path $PSScriptRoot 'StorageHealth.psm1') -Force
$rows = @()
$status = 'ok'
try {
    $disks = @(Get-PhysicalDisk -ErrorAction Stop)
    if ($disks.Count -gt 128) { $disks = @($disks | Select-Object -First 128); $status = 'partial' }
    foreach ($disk in $disks) {
        $counters = $null
        $success = $false
        try {
            $records = @(Get-StorageReliabilityCounter -PhysicalDisk $disk -ErrorAction Stop)
            if ($records.Count -eq 1) { $counters = $records[0]; $success = $true }
        } catch { }
        $rows += ConvertTo-StorageHealthRow -Disk $disk -Counters $counters -QuerySucceeded $success
    }
    if ($rows.Count -eq 0) { $status = 'unavailable' }
    elseif (@($rows | Where-Object { $_.counterStatus -ne 'provider-reported' }).Count -gt 0) { $status = 'partial' }
} catch { $status = 'unavailable' }
$report = [pscustomobject]@{
    schemaVersion = 1
    timestampUtc = [DateTimeOffset]::UtcNow.ToString('o')
    status = $status
    source = 'Windows Storage Provider'
    disks = @($rows)
}
if ($AsJson) { $report | ConvertTo-Json -Depth 5 }
else {
    Write-Host "Storage Provider status: $status"
    $rows | Format-Table name, mediaType, busType, providerHealth, counterStatus, temperatureC, wearPercent, powerOnHours -AutoSize
    Write-Host 'Provider-reported counters are not an independent SMART or NVMe health verdict.'
}
if ($status -eq 'unavailable') { exit 1 }
exit 0
