[CmdletBinding()]
param([string]$PublishDirectory = "publish")
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path $PublishDirectory).Path
$stdout = Join-Path ([IO.Path]::GetTempPath()) ("veypanel-" + [guid]::NewGuid() + ".out")
$stderr = "$stdout.err"
$process = $null
function Assert-Check([bool]$Condition, [string]$Name) {
    if (-not $Condition) { throw "FAIL: $Name" }
    Write-Host "PASS: $Name"
}
try {
    Remove-Item Env:VEYPANEL_LAN_IP, Env:VEYPANEL_PFX, Env:VEYPANEL_PFX_PASSWORD -ErrorAction SilentlyContinue
    $process = Start-Process -FilePath (Join-Path $root 'VeyPanel.Host.exe') -WorkingDirectory $root -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    $base = 'http://127.0.0.1:47860'
    $token = $null
    for ($i = 0; $i -lt 30; $i++) {
        if ($process.HasExited) { throw 'Host exited before readiness' }
        $log = Get-Content $stdout -Raw -ErrorAction SilentlyContinue
        if ($log -match 'http://127\.0\.0\.1:47860/#token=([A-F0-9]{64})') {
            $token = $Matches[1]
            try {
                $response = Invoke-WebRequest "$base/" -TimeoutSec 2
                if ($response.StatusCode -eq 200) { break }
            } catch { }
        }
        Start-Sleep -Seconds 1
    }
    Assert-Check ([bool]$token) 'Ephemeral access token'
    $page = Invoke-WebRequest "$base/" -TimeoutSec 5
    Assert-Check ($page.StatusCode -eq 200 -and $page.Content -match 'VeyPanel') 'Dashboard served'
    foreach ($asset in @('app.js', 'style.css')) {
        $response = Invoke-WebRequest "$base/$asset" -TimeoutSec 5
        Assert-Check ($response.StatusCode -eq 200) "Static asset $asset"
    }
    $url = "$base/api/v1/telemetry"
    foreach ($headers in @(@{}, @{Authorization='Bearer invalid'})) {
        $response = Invoke-WebRequest $url -Headers $headers -SkipHttpErrorCheck -TimeoutSec 5
        Assert-Check ($response.StatusCode -eq 401) 'Missing/invalid token rejected'
    }
    $headers = @{Authorization="Bearer $token"}
    $sample = $null
    for ($i = 0; $i -lt 10; $i++) {
        $sample = Invoke-RestMethod $url -Headers $headers -TimeoutSec 5
        if ($sample.status -eq 'ok') { break }
        Start-Sleep -Seconds 1
    }
    Assert-Check ($sample.status -eq 'ok') 'Native Windows counters available'
    Assert-Check ($null -ne $sample.cpuPercent -and $sample.cpuPercent -ge 0 -and $sample.cpuPercent -le 100) 'CPU in range'
    Assert-Check ($sample.memoryTotalBytes -gt 0 -and $sample.memoryAvailableBytes -le $sample.memoryTotalBytes -and $sample.memoryAvailableBytes -ge 0) 'Physical memory valid'
    Assert-Check ($null -ne $sample.memoryUsedPercent -and $sample.memoryUsedPercent -ge 0 -and $sample.memoryUsedPercent -le 100) 'RAM in range'
    Assert-Check ($null -ne $sample.resources -and $null -ne $sample.resources.networkStatus -and $null -ne $sample.resources.storageStatus) 'Resource inventory schema'
    foreach ($volume in $sample.resources.volumes) {
        if ($null -ne $volume.totalBytes) {
            Assert-Check ($volume.totalBytes -gt 0 -and $volume.freeBytes -ge 0 -and $volume.freeBytes -le $volume.totalBytes) 'Volume capacity valid'
        }
    }
    foreach ($nic in $sample.resources.network) {
        Assert-Check (($null -eq $nic.receiveBytesPerSecond -or $nic.receiveBytesPerSecond -ge 0) -and ($null -eq $nic.transmitBytesPerSecond -or $nic.transmitBytesPerSecond -ge 0)) 'Network rate valid or unavailable'
    }
    Assert-Check ($null -ne $sample.diskIo -and $sample.diskIo.status -in @('ok','partial','warming-up','unavailable')) 'PDH disk status'
    foreach ($metric in @($sample.diskIo.readBytesPerSecond, $sample.diskIo.writeBytesPerSecond, $sample.diskIo.readsPerSecond, $sample.diskIo.writesPerSecond)) {
        Assert-Check ($null -eq $metric -or $metric -ge 0) 'Disk I/O nonnegative or unavailable'
    }
    Write-Host "Disk I/O capability: $($sample.diskIo.status)"
    Assert-Check ($null -ne $sample.physicalDisks -and $sample.physicalDisks.status -in @('ok','partial','warming-up','unavailable')) 'Physical disk instances schema'
    foreach ($disk in $sample.physicalDisks.disks) {
        Assert-Check ($disk.instance -ne '_Total' -and -not [string]::IsNullOrWhiteSpace($disk.instance)) 'Physical disk instance identity'
        foreach ($metric in @($disk.readBytesPerSecond, $disk.writeBytesPerSecond, $disk.readsPerSecond, $disk.writesPerSecond)) {
            Assert-Check ($null -eq $metric -or $metric -ge 0) 'Physical disk metric valid or unavailable'
        }
    }
    Write-Host "Physical disk capability: $($sample.physicalDisks.status)"
    Assert-Check ($null -ne $sample.gpu -and $sample.gpu.status -in @('ok','partial','warming-up','unavailable')) 'GPU capability schema'
    foreach ($metric in @($sample.gpu.busiestEnginePercent, $sample.gpu.videoEncodePercent, $sample.gpu.videoDecodePercent)) {
        Assert-Check ($null -eq $metric -or ($metric -ge 0 -and $metric -le 100)) 'GPU percentage valid or unavailable'
    }
    Write-Host "GPU capability: $($sample.gpu.status)"
    Assert-Check ($null -ne $sample.gpu.inventoryStatus) 'DXGI inventory schema'
    foreach ($adapter in $sample.gpu.adapters) {
        Assert-Check (-not [string]::IsNullOrWhiteSpace($adapter.name)) 'GPU adapter name available or explicitly unmatched'
    }
    Assert-Check (Test-Path (Join-Path $root 'diagnostics/Get-StorageHealth.ps1')) 'Storage script packaged'
    Assert-Check (Test-Path (Join-Path $root 'diagnostics/StorageHealth.psm1')) 'Storage module packaged'
    Assert-Check ($null -ne $sample.storageHealth -and $sample.storageHealth.status -in @('warming-up','ok','partial','unavailable','timeout','stale')) 'Storage worker schema'
    $time = [DateTimeOffset]::Parse($sample.timestampUtc.ToString())
    Assert-Check ([Math]::Abs(([DateTimeOffset]::UtcNow - $time).TotalSeconds) -lt 5) 'Fresh timestamp'
    Start-Sleep -Seconds 2
    $next = Invoke-RestMethod $url -Headers $headers -TimeoutSec 5
    Assert-Check ([DateTimeOffset]::Parse($next.timestampUtc.ToString()) -gt $time) 'Sampling continues'
    $healthDeadline = [DateTimeOffset]::UtcNow.AddSeconds(25)
    while ($next.storageHealth.status -eq 'warming-up' -and [DateTimeOffset]::UtcNow -lt $healthDeadline) {
        Start-Sleep -Seconds 1
        $next = Invoke-RestMethod $url -Headers $headers -TimeoutSec 5
    }
    Assert-Check ($next.storageHealth.status -in @('ok','partial','unavailable','timeout')) 'Storage worker completes bounded attempt'
    Assert-Check ([Math]::Abs(([DateTimeOffset]::UtcNow - [DateTimeOffset]::Parse($next.timestampUtc.ToString())).TotalSeconds) -lt 5) 'Telemetry remains fresh during provider attempt'
    Write-Host "Storage provider capability: $($next.storageHealth.status); rows: $(@($next.storageHealth.disks).Count)"
    Write-Host 'PASS: Host integration smoke'
} finally {
    if ($process -and -not $process.HasExited) { Stop-Process -Id $process.Id -Force; $process.WaitForExit() }
    Remove-Item $stdout, $stderr -Force -ErrorAction SilentlyContinue
}
