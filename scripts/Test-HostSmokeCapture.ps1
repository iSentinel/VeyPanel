[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'HostSmokeCapture.psm1') -Force
function New-FixtureReader([string]$Text) {
    return [IO.StreamReader]::new([IO.MemoryStream]::new([Text.Encoding]::UTF8.GetBytes($Text)))
}
$expected = 'A' * 64
$other = 'B' * 64
$lines = @('secret-canary', "LAN dashboard: https://127.0.0.1:47861/#token=$other", "Local dashboard: http://127.0.0.1:47860/#token=$expected")
$reader = New-FixtureReader ($lines -join [Environment]::NewLine)
try {
    $result = @(Read-HostAccessToken -Reader $reader)
    if ($result.Count -ne 1 -or $result[0] -cne $expected) { throw 'FAIL: exact private bootstrap extraction' }
    Write-Host 'PASS: exact private bootstrap extraction'
} finally { $reader.Dispose() }
$reader = New-FixtureReader "secret-canary Local dashboard: http://127.0.0.1:47860/#token=$expected"
try {
    $rejected = $false
    try { $null = Read-HostAccessToken -Reader $reader }
    catch {
        if ($_.Exception.Message -ne 'Owner bootstrap line unavailable') { throw 'FAIL: unexpected bootstrap failure category' }
        $rejected = $true
    }
    if (-not $rejected) { throw 'FAIL: malformed bootstrap line accepted' }
    Write-Host 'PASS: malformed bootstrap line rejected without raw output'
} finally { $reader.Dispose() }
