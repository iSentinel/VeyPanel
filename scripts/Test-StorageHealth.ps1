$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'StorageHealth.psm1') -Force
$disk = [pscustomobject]@{ FriendlyName='Fixture NVMe'; Model='Fixture'; MediaType='SSD'; BusType='NVMe'; Size=1024; HealthStatus='Healthy'; SerialNumber='DO-NOT-EXPORT'; UniqueId='DO-NOT-EXPORT' }
function Check([bool]$Condition, [string]$Label) {
    if (-not $Condition) { throw "FAIL: $Label" }
    Write-Host "PASS: $Label"
}
$row = ConvertTo-StorageHealthRow -Disk $disk -Counters ([pscustomobject]@{ Temperature=37; Wear=0; PowerOnHours=11; ReadErrorsTotal=0; WriteErrorsTotal=2 }) -QuerySucceeded $true
Check ($row.counterStatus -eq 'provider-reported' -and $row.temperatureC -eq 37 -and $row.wearPercent -eq 0 -and $row.readErrorsTotal -eq 0) 'Valid provider counters including zero'
$missing = ConvertTo-StorageHealthRow -Disk $disk -Counters $null -QuerySucceeded $false
Check ($missing.counterStatus -eq 'unavailable' -and $null -eq $missing.wearPercent -and $null -eq $missing.temperatureC) 'Unavailable values remain null'
$partial = ConvertTo-StorageHealthRow -Disk $disk -Counters ([pscustomobject]@{ Temperature=0; Wear=101; PowerOnHours=4; ReadErrorsTotal=-1; WriteErrorsTotal='' }) -QuerySucceeded $true
Check ($partial.counterStatus -eq 'partial' -and $null -eq $partial.temperatureC -and $null -eq $partial.wearPercent -and $partial.powerOnHours -eq 4 -and $null -eq $partial.readErrorsTotal -and $null -eq $partial.writeErrorsTotal) 'Sentinels and invalid values rejected'
Check (($row | ConvertTo-Json) -notmatch 'DO-NOT-EXPORT|SerialNumber|UniqueId') 'Sensitive disk identifiers excluded'
Write-Host 'PASS: storage provider conversion fixtures'
