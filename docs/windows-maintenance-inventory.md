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
