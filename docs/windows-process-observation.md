# Windows maintenance process observation

Status: candidate, native Windows CI required.

Run from the trusted source checkout with PowerShell 7 on Windows:

    pwsh -NoProfile -File scripts/Get-PackageProcessObservation.ps1

The read-only command queries Win32_Process for the fixed image names
VeyPanel.Desktop.exe and VeyPanel.Host.exe across the system. It emits
only a versioned scope, status and counts, not paths, PIDs or command
lines. Exit 0 means CLEAR_OBSERVATION (no matching names at observation),
2 means BLOCKED (one or more matching names), and 1 means unavailable or
invalid observation. Query errors must not be interpreted as zero.
The CIM operation requests a five-second operation timeout; this is not
a proven hard deadline for the entire provider call.

All matching processes are conservatively treated as blockers, including
different installations or users. This is not an ownership check, a
lifetime lock, a complete inventory of renamed or inaccessible processes,
or authorization to terminate any process. Do not use a name or PID alone
to stop a process. No operation is automatically admitted or performed.
Manual exclusive maintenance and subsequent revalidation remain required.

The Windows CI fixture checks empty, matching, invalid and excessive
observations plus private-field exclusion. Existing Host integration
smoke checks BLOCKED while its owned Host is running; a following CI
step requires CLEAR_OBSERVATION after the existing cleanup. The new tool
never stops a process. PowerShell and CIM are not available on the Linux
development server; local Python PASS is not native qualification.

Next: establish an owned lifetime handle or cooperative admission
protocol, account for crashes and concurrent launches, and qualify
safe shutdown and update/uninstall. Do not add destructive operations
until ownership, exclusive maintenance, recovery and approval gates
are separately reviewed.
