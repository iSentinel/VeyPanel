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
