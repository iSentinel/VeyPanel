# Side-by-side Windows package selection

Status: PR #35 merged; both Windows CI runs passed. Python 3.12 and trusted source checkout
required. Use an existing private dedicated directory owned by the current
user. All package and root access must be under exclusive owner control.

A verified package is staged at versions/<package SHA-256>. A single
selection.json records active and previous package and manifest digests.
State replacement uses a temporary file, flush, fsync and os.replace.
Before use, the selected manifest digest and full tree are verified. The
same selected digest is idempotent; a different package is staged without
overwriting any existing version. Rollback verifies the previous version
and swaps the two records. It can roll back a damaged active tree.
Neither operation runs an executable, stops a process, creates a shortcut,
registers a service or migrates application data. The selection is metadata
only until a separate launcher consumes it.

    python scripts/windows_package_selection.py --root C:\VeyPanel-test select VeyPanel-win-x64-portable.zip --sha256 EXPECTED_SHA256 --dry-run
    python scripts/windows_package_selection.py --root C:\VeyPanel-test select VeyPanel-win-x64-portable.zip --sha256 EXPECTED_SHA256 --apply
    python scripts/windows_package_selection.py --root C:\VeyPanel-test status
    python scripts/windows_package_selection.py --root C:\VeyPanel-test rollback --dry-run
    python scripts/windows_package_selection.py --root C:\VeyPanel-test rollback --apply

Obtain the digest independently from a trusted channel. Dry-run is the
default and is an advisory read-only check; apply repeats validation under
the writer lock. This is not signed provenance or access-control enforcement.
The lock serializes cooperating writers. A terminated operation can leave
.selection-lock, temporary state or an unreferenced version. Do not remove
the lock until confirming no operation is running. Inspect orphaned files
manually; existing versions are never automatically reused or removed.
Atomic state replacement is not proof of persistence across power loss.
The root, package and state must be protected from other writers; hostile
same-user concurrent mutation is outside this stage.

Local evidence: thirteen synthetic fixtures include write-failure injection,
tampered previous refusal and rollback from damaged active. The two actual
previously downloaded Windows packages were selected A -> B -> A without
launching either, preserving both source archives and version directories.
Windows CI exercises real package first selection and idempotence and runs
the synthetic update/rollback and failure fixtures. Actual process lifecycle,
activation, data migration, crash recovery and uninstall remain separate.
