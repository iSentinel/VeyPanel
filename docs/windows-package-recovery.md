# Read-only package recovery inspection

Status: candidate; Windows CI pending. Use the trusted Python 3.12
maintenance checkout and the private package selection root.

    python scripts/inspect_package_recovery.py --root C:\VeyPanel-test

Exit codes: 0 means no observed recovery anomaly, 1 means inspection
could not complete, and 2 means manual review is required. The snapshot
checks selection metadata, referenced file trees, a remaining selection
lock, temporary selection files and unreferenced version directories.
An unreferenced directory is not necessarily damaged: it may be an older
retained package. The tool does not adopt, repair, delete, rename or
activate any package and does not remove locks.

A lock may belong to an operation that is still running. Stop maintenance
operations through their normal controls and confirm exclusive access before
further investigation. Do not infer that a lock is stale from its presence,
age or this report. No automatic lock clearing is supported. When the
selection is readable and no lock is present, a verified previous version
may be inspected using the existing rollback dry-run. Its authenticity
must still be bound to an independently trusted original archive before
launch. A corrupt state or an orphan after interrupted first installation
requires separate explicit recovery, not automatic adoption.

The snapshot is advisory and can race with concurrent writers; inspect
only in a private root during a maintenance window. Integrity checks are
not signature authentication. No physical power-loss guarantee, actual
process shutdown, uninstall or interactive WPF acceptance is implied.

## Engineering integration

Public Python APIs and test fixtures meet the exact AST gate. CLI errors use
fixed reason categories, not exception text. This stage is independent of
Launcher execution and retains the private, quiescent root assumption.

Verified combined acceptance: PR #45 merged 5bb5505, all fourteen CI jobs passed. Native scope only; physical and production acceptance remain separate.

## Explicit first-install recovery (candidate)

Only a missing selection.json and exactly one digest-named staged version
in a private, quiescent root are eligible. The original ZIP must be outside
the root, with an independently trusted SHA-256. Preflight verifies every
archive file, the nested Host manifest and matching source evidence, then
binds the staged tree to the original manifest. No existing state, lock,
temporary file, additional version or unexpected root entry is accepted.

    python scripts/recover_first_install.py --root C:\VeyPanel-test --package VeyPanel-win-x64-portable.zip --sha256 EXPECTED_SHA256 --dry-run
    python scripts/recover_first_install.py --root C:\VeyPanel-test --package VeyPanel-win-x64-portable.zip --sha256 EXPECTED_SHA256 --apply --plan-sha256 REVIEWED_PLAN_SHA256

Dry-run writes nothing. The explicit apply re-verifies under the cooperating
lock and checks the root-bound plan digest before atomically writing only
selection.json. It checks readback and tree integrity, does not execute any
binary, delete or adopt other versions, modify payloads or clear old locks.
The plan is not authorization; use only in an explicitly approved private
maintenance window with exclusive owner control. Exit 1 means refusal or
uncertain execution: inspect current state before any retry. Existing or
corrupt metadata, stale locks, multiple retained versions, process fencing
and physical interruption remain separate prerequisites. No authenticated
publisher, hostile-writer resistance or power-loss durability claim.

Twelve offline tests and an isolated real 836-file ZIP recovery passed on
Linux; actual Windows CI stage prepared. The disposable root is retained
for evidence, not an installed or activated product.
