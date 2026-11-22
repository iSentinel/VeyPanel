Set-StrictMode -Version Latest

function Get-ProviderNumber {
    param($Record, [string]$Name, [decimal]$Minimum = 0, [decimal]$Maximum = [decimal][uint64]::MaxValue)
    if ($null -eq $Record) { return $null }
    $property = $Record.PSObject.Properties[$Name]
    if ($null -eq $property -or $null -eq $property.Value) { return $null }
    if ($property.Value -is [string] -and [string]::IsNullOrWhiteSpace($property.Value)) { return $null }
    if ($property.Value -is [bool]) { return $null }
    [decimal]$number = 0
    if (-not [decimal]::TryParse([string]$property.Value, [Globalization.NumberStyles]::Integer,
        [Globalization.CultureInfo]::InvariantCulture, [ref]$number)) { return $null }
    if ($number -lt $Minimum -or $number -gt $Maximum) { return $null }
    return [uint64]$number
}

function Get-ProviderText {
    param($Record, [string]$Name)
    if ($null -eq $Record) { return $null }
    $property = $Record.PSObject.Properties[$Name]
    if ($null -eq $property -or [string]::IsNullOrWhiteSpace([string]$property.Value)) { return $null }
    return [string]$property.Value
}

function ConvertTo-StorageHealthRow {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Disk, $Counters, [bool]$QuerySucceeded)
    $temperature = Get-ProviderNumber $Counters Temperature 1 150
    $wear = Get-ProviderNumber $Counters Wear 0 100
    $hours = Get-ProviderNumber $Counters PowerOnHours
    $read = Get-ProviderNumber $Counters ReadErrorsTotal
    $write = Get-ProviderNumber $Counters WriteErrorsTotal
    $values = @($temperature, $wear, $hours, $read, $write)
    $available = @($values | Where-Object { $null -ne $_ }).Count
    $status = if (-not $QuerySucceeded -or $available -eq 0) { 'unavailable' } elseif ($available -lt 5) { 'partial' } else { 'provider-reported' }
    [pscustomobject]@{
        name = Get-ProviderText $Disk FriendlyName
        model = Get-ProviderText $Disk Model
        mediaType = Get-ProviderText $Disk MediaType
        busType = Get-ProviderText $Disk BusType
        sizeBytes = Get-ProviderNumber $Disk Size 1
        providerHealth = Get-ProviderText $Disk HealthStatus
        counterStatus = $status
        temperatureC = $temperature
        wearPercent = $wear
        powerOnHours = $hours
        readErrorsTotal = $read
        writeErrorsTotal = $write
    }
}

Export-ModuleMember -Function ConvertTo-StorageHealthRow
