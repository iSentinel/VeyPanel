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

Verified PR #56 merged e4fb31f; ten jobs PASS. Windows run 45545383687 confirms fixtures, BLOCKED while owned Host runs and CLEAR_OBSERVATION after cleanup. No lifetime lock claim.

## Cooperative Desktop session admission candidate

Desktop acquires the fixed Local\VeyPanel.Desktop.Interactive.v1 named
mutex before constructing MainWindow or its tray/Host controller. A
competing participating instance exits with code 2, startup failure
with code 1. There is no automatic activation of the existing window.
The UI thread retains ownership until application exit; a foreign thread
cannot release the lease. Windows abandonment transfers ownership to
the new acquiring thread; it does not establish prior Host cleanup or
authorize recovery. No PID lookup, termination, deletion or global
maintenance lock is introduced.

The native smoke uses an isolated unique Local mutex and separate
threads to check refusal, nonowner release rejection, continued owner
admission and acquisition after release. It does not launch the WPF
window or prove cross-process, cross-user/session or crash recovery
behavior. Old binaries and noncooperating programs do not participate.
The existing process observation remains advisory. Next qualify
cross-process admission, actual WPF startup/exit and retained Host
ownership before designing an exclusive maintenance protocol.

### Isolated cross-process and abandonment qualification (candidate)

The native smoke additionally starts only its own smoke executable
(or the same dotnet host with the smoke assembly) using an argument list.
The child accepts only a unique fixture GUID name and a fixed mode.
Require exit 2 while the parent owns the mutex and exit 0 after release.
A separate fixture retains a non-owning handle, then has the child exit
without disposing its owned mutex; require acquisition by the parent
and refusal of another child. The ten-second child exit budget and
bounded cleanup concern only owned synthetic smoke processes.
No WPF window, production mutex, Host process or installed package is
used by this test. Actual CI remains required. Same-thread recursive
mutex behavior is not a general admission API guarantee; App acquires
once on its UI thread. No proof of prior Host exit follows from abandonment.

Verified PR #57 merged b6b772d, seven integrated CI jobs PASS, native thread/process contention and abandonment fixture PASS. Actual WPF activation and maintenance exclusion remain unqualified.

## Owned Host cleanup-required state (candidate)

A failed owned Host stop clears its dashboard token before exit is
confirmed. Previously the ready-state boolean made this appear stopped
and disabled Stop in Desktop. Distinguish Stopped, Ready and
CleanupRequired under the existing controller gate. A retained live
process without readiness, or an unavailable owned-process observation,
requires explicit Stop; Start and dashboard are denied. Keep the Stop
button enabled and report the state. Failed Dispose does not finalize
the controller, so the window can request explicit cleanup again.
No changes to existing graceful stop/owned-child escalation timeouts.

The existing isolated real Host lifecycle smoke simulates only the
cleared-token state, using test reflection on its own controller after
readiness. Verify cleanup status, rejected Start without replacement,
denied dashboard and existing explicit Stop/restart. This is not an
injected OS stop failure, actual WPF button acceptance, crash recovery,
or cross-session/exclusive maintenance qualification.

## Managed Host owner-exit fixture (candidate)

The existing managed Host waits for stdin EOF and requests graceful
application stop. Add an isolated Windows smoke owner process which
starts the real published Host through HostController, reports only a
private pipe identity to the supervisor, then exits without Dispose
after an explicit fixture handshake. The supervisor holds an observed
process handle before the owner exits and checks image path/start time
against that private identity. Require successful owner exit, bounded
Host exit with code zero, and subsequent fixed-name clear observation.
No PID or private pipe identity is printed to shared evidence. On failure
only the directly started smoke owner may be terminated; the observed
Host is never killed by PID. This tests owner disappearance and stdin EOF
in an isolated runner, not arbitrary power failure, live user processes,
a general process ownership proof, or system-wide maintenance exclusion.

Verified PR #58 merged 1d6e454; seven integrated CI jobs PASS. Native owned Host cleanup-required and isolated owner disappearance smoke passed. Actual WPF and exclusive maintenance remain open.
