# Read-only Windows maintenance inventory

Status: candidate; native CI required.

Use a trusted private, quiescent installation root and externally trusted
archives retained outside that root. Supply the exact expected SHA-256 for
each retained version, including the previous version when present.

    python scripts/plan_windows_maintenance.py --root C:\VeyPanel-test --archive ACTIVE_SHA256 C:\archives\active.zip

For two versions append a second --archive PREVIOUS_SHA256 ZIP pair.
Only the selection file and exactly its referenced version directories
are accepted. Locks, backups, unknown root entries, orphan directories,
malformed state, missing archives, mismatched hashes and modified files
require manual review. The tool reuses full staged-tree and trusted ZIP
verification. The plan digest binds exact selection bytes, root identity
and verified records; paths are not included in the output.

The result INVENTORY_VERIFIED means only successful read-only inventory.
process_state remains NOT_CHECKED, maintenance_admitted and removed are
always false. There is no apply mode, no deletion and no process action.
The advisory writer-lock checks are not a held lease or an atomic snapshot;
hostile writers, runtime admission, ACLs, backup restoration, and exclusive
maintenance remain separate gates. The plan digest is not authorization.

Local: nine explicit inert regressions PASS, real isolated single-version
installation verified with 838 files unchanged. The older two-version
fixture was correctly refused: its previous ZIP pathname currently
contains the active archive bytes, not the recorded previous digest.
Do not rewrite that selection or treat the missing archive as verified.
Two-version positive coverage currently uses inert fixture archives.
Native CI requires a real single-version recovered package inventory.

Verified PR #59 merged 81d65ed, three integrated CI jobs PASS; Windows 229/229 and real recovered package inventory independently checked. No maintenance exclusion claim.

## Verified package-source backup candidate

Use only a private, pre-existing destination parent with suitable ACLs
and sufficient space. Copy exact selection metadata and the original
externally pinned archives, not arbitrary installed/user data. Dry-run
does not create the destination. Apply requires the prior plan digest
and a fresh destination outside the installation root.

    python scripts/backup_windows_selection.py copy --root C:\VeyPanel-test --destination C:\backups\new --archive EXPECTED_SHA256 C:\archives\package.zip
    python scripts/backup_windows_selection.py copy --root C:\VeyPanel-test --destination C:\backups\new --archive EXPECTED_SHA256 C:\archives\package.zip --apply --plan-sha256 REVIEWED_PLAN_SHA256
    python scripts/backup_windows_selection.py verify --directory C:\backups\new --plan-sha256 REVIEWED_PLAN_SHA256

Retain the plan digest separately. Copy uses exclusive new files,
bounded streaming, digest/readback checks and source inventory recheck.
The receipt binds the original selection bytes, source inventory plan
and destination digest; independent verification recomputes the binding
and checks exact membership, original archive SHA and nested manifest.
A receipt alone is insufficient: always run verification. Failed or
partial output is retained for manual review, never overwritten or
automatically deleted. A failed final readback must not be treated as
success even if a receipt exists. A verified copy may be relocated into
another trusted private directory; the receipt binds the original plan,
not the current path.

This is a package-source backup, not a full user-data backup. It does
not capture runtime settings or grants, establish ACL protection on
Windows, guarantee physical power-loss durability or a hostile-writer
snapshot, or authorize maintenance. No restore/apply-to-installation,
uninstall, deletion or process action is implemented. Source and backup
may share a physical device; no independent failure-domain claim.
Seven inert fixtures and actual single-version 291091352-byte archive
copy verified locally, all 838 source inventory files unchanged.
Native CI uses only the isolated recovered package. Restore into a
new empty root and real two-version backup remain separate gates.

Verified PR #60 merged 1c5b8e3; three integrated CI jobs PASS, Windows 236/236 and real isolated backup independently verified. No physical durability or user-data backup claim.

## Restore into a fresh directory candidate

Use the separately retained verified backup plan digest, a private
existing destination parent and a new, nonexistent target. Dry-run
verifies the backup and binds the destination and parent identity.
Apply requires that exact reviewed restore plan.

    python scripts/restore_windows_selection.py --directory C:\backups\new --backup-plan-sha256 BACKUP_PLAN_SHA256 --destination C:\VeyPanel-restored
    python scripts/restore_windows_selection.py --directory C:\backups\new --backup-plan-sha256 BACKUP_PLAN_SHA256 --destination C:\VeyPanel-restored --apply --plan-sha256 RESTORE_PLAN_SHA256

Only exact backup records and digest-derived ZIP names are accepted.
Stage each version using the existing package preflight, verify the
complete extracted tree against the original archive, recheck the
backup, and create selection metadata exclusively after all versions
pass. Verify exact metadata readback and the final inventory.
No activation, overwrite, replacement of existing installation or
maintenance admission is implemented. On failure preserve the
incomplete root for manual review; existing staging may remove its
own failed newly extracted version. An interrupted final metadata
write can leave incomplete state, and final readback failure is not
success. Do not automatically retry, activate or clean up a failed root.
Trusted quiescent private paths and adequate capacity are prerequisites,
not an atomic hostile-writer snapshot, ACL or power-loss guarantee.

Seven local regression cases include exact two-version inert restoration,
existing destination refusal, wrong plan, source change and partial
extraction without published selection. Actual single-version restore
from the 291091352-byte archived backup matched all 838 source inventory
files, with source and backup unchanged and Launcher dry-run PASS.
Native Windows CI uses the isolated recovered package and separately
retained backup plan from the previous step. Actual WPF launch,
real two-version archives, runtime settings and uninstall remain open.

Verified PR #61 merged d73d5f0; three integrated jobs PASS, Windows 243/243 and actual isolated backup/restore. No activation or existing-root replacement.
