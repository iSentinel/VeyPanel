[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'PackageProcessObservation.psm1') -Force

$clear = Measure-PackageProcessNames -Rows @()
if ($clear.status -ne 'CLEAR_OBSERVATION' -or $clear.desktop_count -ne 0 -or $clear.host_count -ne 0) {
    throw 'FAIL: empty process observation'
}
$rows = @(
    [pscustomobject]@{ Name = 'VeyPanel.Host.exe'; ExecutablePath = 'secret-canary' },
    [pscustomobject]@{ Name = 'veypanel.desktop.exe'; ProcessId = 123456789 }
)
$blocked = Measure-PackageProcessNames -Rows $rows
if ($blocked.status -ne 'BLOCKED' -or $blocked.desktop_count -ne 1 -or $blocked.host_count -ne 1) {
    throw 'FAIL: fixed process names not blocked'
}
$json = $blocked | ConvertTo-Json -Compress
if ($json.Contains('secret-canary') -or $json.Contains('123456789')) {
    throw 'FAIL: process observation exported private fields'
}
foreach ($invalid in @(
    [pscustomobject]@{ Name = 'unexpected.exe' },
    [pscustomobject]@{ Name = $null }
)) {
    $rejected = $false
    try { $null = Measure-PackageProcessNames -Rows @($invalid) }
    catch { $rejected = $true }
    if (-not $rejected) { throw 'FAIL: invalid process observation accepted' }
}
$rejected = $false
try { $null = Measure-PackageProcessNames -Rows (@($rows[0]) * 1025) }
catch { $rejected = $true }
if (-not $rejected) { throw 'FAIL: excessive process observation accepted' }
Write-Host 'PASS: conservative process observation fixtures'
