# Read-only, conservative observation. Names are not proof of process ownership.
function Measure-PackageProcessNames {
    [CmdletBinding()]
    param([Parameter(Mandatory)][AllowEmptyCollection()][object[]]$Rows)

    if ($Rows.Count -gt 1024) { throw 'Process observation count exceeds budget' }
    $desktop = 0
    $hostCount = 0
    foreach ($row in $Rows) {
        if ($null -eq $row -or $row.Name -isnot [string]) {
            throw 'Invalid process observation'
        }
        switch ($row.Name) {
            'VeyPanel.Desktop.exe' { $desktop++ }
            'VeyPanel.Host.exe' { $hostCount++ }
            default { throw 'Unexpected process observation' }
        }
    }
    return [ordered]@{
        schema = 1
        scope = 'system-wide-fixed-image-names'
        status = if ($desktop + $hostCount -eq 0) { 'CLEAR_OBSERVATION' } else { 'BLOCKED' }
        desktop_count = $desktop
        host_count = $hostCount
    }
}

function Get-PackageProcessObservation {
    [CmdletBinding()]
    param()

    if (-not $IsWindows) { throw 'Native Windows required' }
    $query = @{
        ClassName = 'Win32_Process'
        Property = 'Name'
        Filter = "Name = 'VeyPanel.Desktop.exe' OR Name = 'VeyPanel.Host.exe'"
        OperationTimeoutSec = 5
        ErrorAction = 'Stop'
    }
    $rows = @(Get-CimInstance @query)
    return Measure-PackageProcessNames -Rows $rows
}

Export-ModuleMember -Function Measure-PackageProcessNames, Get-PackageProcessObservation
