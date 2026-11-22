[CmdletBinding()]
param(
    [string]$InstallerPath,
    [string]$DriverCatalogPath,
    [switch]$RequireReady
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows only.' }
$expectedHash = '42b2aefaacb3474511517a56b96ee9f0517f30ac38b5dd2fda9fd5b478f5021a'
$checks = [System.Collections.Generic.List[object]]::new()
function Add-Check([string]$Name, [string]$Status, [string]$Detail) {
    $checks.Add([pscustomobject]@{ Check = $Name; Status = $Status; Detail = $Detail })
}
function Test-PinnedInstaller {
    if (-not $InstallerPath) {
        Add-Check 'Apollo v0.4.6 installer' 'NOT TESTED' 'No installer supplied.'
        return
    }
    $hash = (Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256).Hash
    $sig = Get-AuthenticodeSignature -LiteralPath $InstallerPath
    $valid = ($hash -eq $expectedHash) -and ($sig.Status -eq 'Valid')
    Add-Check 'Apollo v0.4.6 installer' $(if ($valid) {'PASS'} else {'FAIL'}) "SHA256 match: $($hash -eq $expectedHash); Authenticode: $($sig.Status)"
}
function Test-DriverCatalog {
    if (-not $DriverCatalogPath) {
        Add-Check 'Driver catalog signature' 'NOT TESTED' 'No catalog supplied; never bypass driver signing.'
        return
    }
    $sig = Get-AuthenticodeSignature -LiteralPath $DriverCatalogPath
    Add-Check 'Driver catalog signature' $(if ($sig.Status -eq 'Valid') {'PASS'} else {'FAIL'}) "$($sig.Status); signature alone does not establish package compatibility."
}
$os = Get-CimInstance Win32_OperatingSystem
Add-Check 'OS' $(if ([int]$os.BuildNumber -ge 22000) {'PASS'} else {'WARN'}) "$($os.Caption) build $($os.BuildNumber)"
$gpus = @(Get-CimInstance Win32_VideoController)
foreach ($gpu in $gpus) {
    Add-Check 'GPU inventory' 'INFO' "$($gpu.Name); driver $($gpu.DriverVersion)"
}
if ($gpus.Name -match 'Intel.*Arc') {
    Add-Check 'Intel Arc discovery' 'PASS' 'Adapter name detected; encode capability NOT TESTED.'
} else {
    Add-Check 'Intel Arc discovery' 'WARN' 'Intel Arc not identified by adapter name.'
}
try {
    Add-Type -AssemblyName System.Windows.Forms
    foreach ($screen in [Windows.Forms.Screen]::AllScreens) {
        $b = $screen.Bounds
        Add-Check 'Desktop display' 'INFO' "$($screen.DeviceName): $($b.Width)x$($b.Height), x=$($b.X), y=$($b.Y), primary=$($screen.Primary)"
    }
} catch { Add-Check 'Desktop display' 'NOT TESTED' 'Interactive display enumeration unavailable.' }
try {
    $devices = @(Get-PnpDevice -PresentOnly -Class Display -ErrorAction Stop | Where-Object {
        $_.FriendlyName -match 'SudoVDA|Apollo|Virtual Display|Virtual Monitor'
    })
    if ($devices.Count) {
        foreach ($device in $devices) { Add-Check 'Virtual adapter inventory' 'INFO' "$($device.FriendlyName): $($device.Status)" }
    } else { Add-Check 'Virtual adapter inventory' 'NOT TESTED' 'No matching adapter name; this is not proof of absence.' }
} catch { Add-Check 'Virtual adapter inventory' 'NOT TESTED' 'PnP query unavailable.' }
$client = [Net.Sockets.TcpClient]::new()
try {
    $pending = $client.ConnectAsync('127.0.0.1', 47990)
    $reachable = $pending.Wait(2000) -and $client.Connected
    Add-Check 'Local Apollo TCP port' $(if ($reachable) {'INFO'} else {'NOT TESTED'}) 'TCP reachability only; identity, TLS and API are not verified.'
} catch { Add-Check 'Local Apollo TCP port' 'NOT TESTED' 'Not reachable.' }
finally { $client.Dispose() }
try { Test-PinnedInstaller } catch { Add-Check 'Apollo v0.4.6 installer' 'FAIL' 'Unable to verify supplied file.' }
try { Test-DriverCatalog } catch { Add-Check 'Driver catalog signature' 'FAIL' 'Unable to verify supplied file.' }
$checks | Format-Table -AutoSize -Wrap
$failed = @($checks | Where-Object Status -eq 'FAIL').Count
$pending = @($checks | Where-Object { $_.Status -in @('WARN', 'NOT TESTED') }).Count
Write-Host "Failures: $failed; warnings or unavailable checks: $pending"
if ($failed -gt 0 -or ($RequireReady -and $pending -gt 0)) { exit 1 }
exit 0
