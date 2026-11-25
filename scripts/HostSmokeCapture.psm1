# Read only the exact owner bootstrap line; never emit arbitrary Host output.
function Read-HostAccessToken {
    [CmdletBinding()]
    param([Parameter(Mandatory)][System.IO.StreamReader]$Reader)
    $clock = [System.Diagnostics.Stopwatch]::StartNew()
    for ($i = 0; $i -lt 64; $i++) {
        $remaining = [TimeSpan]::FromSeconds(30) - $clock.Elapsed
        if ($remaining -le [TimeSpan]::Zero) { break }
        $line = $Reader.ReadLineAsync().WaitAsync($remaining).GetAwaiter().GetResult()
        if ($null -eq $line) { break }
        $match = [regex]::Match($line, '^Local dashboard: http://127\.0\.0\.1:47860/#token=([A-F0-9]{64})$')
        if ($match.Success) { return $match.Groups[1].Value }
    }
    throw 'Owner bootstrap line unavailable'
}
Export-ModuleMember -Function Read-HostAccessToken
