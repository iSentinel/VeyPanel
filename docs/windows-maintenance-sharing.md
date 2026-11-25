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

## Handle identity observation candidate

An isolated Windows smoke reads BY_HANDLE_FILE_INFORMATION from an
already opened FileStream. The volume serial and 64-bit file index
identify the held file for the qualified local filesystem scenario.
Reject directories, reparse attributes, unavailable/zero file index
and link counts other than one. This is an observation of the opened
handle, not a canonical path or ACL verification.

The native fixture opens two shared handles and requires matching
identities. Replacement and deletion of the held inert fixture name
must fail; both fixture names and the original handle identity remain
intact. A deliberately created hard-link alias must fail the identity
check; after alias removal the single-link check succeeds. A distinct
replacement file, created while the original still exists, must have
a different observed identity after release and replacement.
Only fresh temporary fixture files are involved.

No persistent identity enrollment, production lease integration or
cross-language identity comparison is implemented. The identifier is
filesystem/volume dependent and may be reused after deletion; it is
not authentication or proof of protection against hostile writers.
The earlier pathname precheck remains susceptible to path races.
Native Windows CI must qualify the exact fixture; unsupported
filesystems fail the test rather than silently passing.
