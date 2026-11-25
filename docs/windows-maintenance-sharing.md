# Cooperative Windows maintenance sharing lease prototype

Status: candidate; smoke-only, native Windows CI required.

A provisioned private regular file can be opened with FileAccess.Read and
FileShare.Read by multiple cooperating runtime participants. A maintenance
participant requests FileAccess.ReadWrite with FileShare.None. Windows file
sharing must reject the exclusive open while any runtime handle exists,
and reject new runtime/exclusive opens while maintenance owns its handle.
Only Win32 sharing violation (32) is classified as busy. All other errors
fail closed. The prototype never creates, truncates or writes the file,
and rejects missing, directory and reparse paths/ancestors.

The unique inert smoke file lives under a newly created temporary
directory. Separate smoke processes verify shared admission, maintenance
refusal until the last shared handle closes, exclusive refusal of both
contender types, admission after release and reacquisition after an
isolated owner exits without Dispose. Child waits and cleanup are bounded,
only directly started synthetic children are stopped. The fixture checks
unchanged file bytes and refusal of a missing lease. No product process
is started by the new smoke.

This is deliberately not linked into Desktop, Host, Launcher or the Python
maintenance tools. It is not an authorization or a security boundary.
A production design must provision and retain one canonical stable file
outside version trees, establish ACL and identity across processes and
sessions, prevent replacement/aliasing, integrate runtime admission before
startup and hold the lease until actual process cleanup. An exclusive
maintenance lease must then span all mutations and independent inventory
checks, and coexist with selection locks in a fixed order. Old binaries
and unrelated programs do not participate; existing process observation
and manual exclusive maintenance remain necessary. The path checks are
not an atomic defense against hostile concurrent path mutation.

No uninstall, removal, activation, privilege change, production install
or filesystem fault injection is introduced. Native Windows compilation
and execution are required before claiming even the prototype qualified.

Verified PR #62 merged 234ba2e: six integrated jobs PASS, Windows 243/243 and native sharing fixture PASS. This remains a smoke-only prototype.

## Python/C# sharing interoperability candidate

The Python standard-library adapter uses CreateFileW with OPEN_EXISTING,
GENERIC_READ/FileShare.Read for a runtime participant and
GENERIC_READ|GENERIC_WRITE/no sharing for maintenance. Only Win32
ERROR_SHARING_VIOLATION (32) yields a busy result; access denied, missing
files and all other errors fail closed. The context manager closes an
acquired handle even if its caller raises; a failed close is an error.
It does not write, create or truncate the lease file.

Four offline regression fixtures mock the native API to check access and
share flags, busy-only classification, exception cleanup and refusal of
missing or directory paths. Native Windows CI starts the trusted C#
smoke assembly as a bounded child of the Python fixture. The Python
parent holds a shared lease while a C# runtime contender succeeds and
maintenance is refused, then an exclusive lease while both contenders
are refused. After release both contenders succeed and fixture bytes
must remain unchanged. This complements the already qualified C#-only
fixture; it does not exercise production Desktop/Host or reverse
ownership by a C# parent with a Python child.

The adapter is not connected to any mutation or activation operation.
Path checks are advisory under the private, quiescent fixture assumption;
stable file identity, hard-link/reparse races, ACLs, cross-user/session
scope, actual process admission and global maintenance exclusion remain
open. This is not an authorization or security boundary. Native Windows
CI is required before claiming interoperability.

## Reverse ownership interoperability candidate

The new native smoke keeps the C# shared or exclusive FileStream open
while directly starting a trusted Python interpreter with a fixed
contender script. Uncontended controls, shared admission, exclusive
refusal, release and unchanged bytes are required. Only exact exit 2
is busy; unavailable or invalid is a failure. Bounded child cleanup
only affects directly started inert fixtures. TEMP/TMP are aligned,
and the Python scope check resolves the parent, not the held leaf;
the existing Python lease adapter checks the regular leaf before open.
Three offline scope regressions cover fixed scope, wrong names and
nested/traversal paths. Native Windows is required. No runtime wiring,
ACL or production maintenance authorization.
