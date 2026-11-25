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
