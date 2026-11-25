# Upstream review-only baseline

Observed 2026-11-25 06:07–06:09 UTC via authenticated GitHub metadata API.
This is the first recorded watch baseline, status REVIEW for every row.
Repository and release identity are observations, not an endorsement,
dependency pin, redistribution permission or release approval.

| Repository | Role | Default branch HEAD | Latest published release / ID | Release commit | Reported license |
|---|---|---|---|---|---|
| ClassicOldSong/Apollo | External streaming host / virtual display | master adc5c5a0bd80831ce495434bb16aee2cd4175fb8 | v0.4.6 / 232074361 | 0cd32abaaa141d262477d039ac447b38fe99c394 | GPL-3.0 |
| moonlight-stream/moonlight-android | External Android client reference | master b48494cb96bff23d8886c4775cc4f39a1075495d | v12.2 / 387680237 | b48494cb96bff23d8886c4775cc4f39a1075495d | GPL-3.0 |
| itkawa/screen-spawner | Display lifecycle reference | main 5951f8090858c226e70ab22c3d615ff91db0f619 | v0.3.2 / 454820983 | 5951f8090858c226e70ab22c3d615ff91db0f619 | GPL-3.0 |
| LibreHardwareMonitor/LibreHardwareMonitor | External thermal provider reference | master 9e2d677cefff5c614ecc38da88fbc447eb478e2a | v0.9.6 / 286366766 | 3d331e3370efb858411f19511373eff65a218701 | MPL-2.0 |

All four repository metadata queries succeeded and reported nonarchived
repositories. The release tag refs were direct commit objects; the commits
endpoint corroborated each exact SHA. Apollo and LibreHardwareMonitor HEAD
differ from their documented release tags; no code delta review is implied.
Latest published release is not necessarily the newest tag or prerelease.
No independent signature, binary, asset, license-text or provenance audit
was performed during this observation. Artemis is named as a possible
external client in README but no exact upstream repository was identified
in the canonical architecture references; its watch entry remains unresolved.

## Candidate follow-up

Screen Spawner v0.3.2 (2026-11-22T23:14:11Z) release notes describe a
GNOME mirror-mode reconnection fix. Add a Windows-specific reconnect
and restore test design before any display topology changes. The upstream
test report is not a VeyPanel hardware result. No code or binary adoption.

## Repeat observation

Use GitHub repository metadata, default branch commit, latest release
metadata and exact tag target:

    gh api repos/OWNER/REPO
    gh api repos/OWNER/REPO/commits/DEFAULT_BRANCH
    gh api repos/OWNER/REPO/releases/latest
    gh api repos/OWNER/REPO/git/ref/tags/TAG
    gh api repos/OWNER/REPO/commits/TAG

For an annotated tag, resolve its object to the commit and corroborate.
Review HEAD, release ID/tag and exact release commit against this baseline.
Use REVIEW for changes, UNCHANGED only when all required observations match,
ERROR for incomplete or failed required queries. Missing latest release
does not prove absence of tags. Do not automatically update pins, adopt
code/assets or install packages. Automated periodic watch and structured
report validation are separate unfinished work.

## Structured comparison candidate

The reviewed baseline is now also represented by
config/upstream-review-baseline.json. The offline classifier accepts a
separately collected JSON observation with the same schema (version 1,
repositories keyed by the four reviewed names, exact seven metadata
fields per complete row). Missing or invalid rows yield ERROR; unknown
repositories, invalid baseline and invalid document schema fail closed.
Compare default branch, HEAD, published release ID/tag, exact release
commit, reported license and archived flag. A changed field yields REVIEW,
and a complete exact match yields UNCHANGED. ERROR dominates REVIEW.
Output includes the SHA-256 of each exact input snapshot and fixed
repository/status/changed-field values, not raw unexpected data.

    python scripts/check_upstream_review.py --baseline config/upstream-review-baseline.json --observed observed.json

Exit 0 means all supplied rows match; 2 means review required; 1 means
invalid or incomplete evidence. These are review statuses, not product
QA or release approval. Input files are read-only, bounded to 64 KiB and
strictly parsed; no network access, dependency mutation or automatic
baseline replacement is performed by this classifier.

A fresh separate GitHub metadata observation of all four repositories
on 2026-11-25 (06:26 UTC) returned four UNCHANGED rows. Baseline SHA-256
fc6ed7746386ce3754c9cbbf715023e1ca4cc1295e38d26762a8a8920bab4344;
observed SHA-256
fb118a69c3c41731bfc2b264d5ea03107d34e515c22fffcb360777637c0d94e0.
The observation used the metadata, default-branch commit, release, tag-ref
and resolved-commit API endpoints. Each tag was a direct commit, and
its SHA matched the resolved commit. The raw observation/report remains
in a unique local directory; no credentials or raw API responses are
committed. The classifier cannot attest input freshness or origin.
Automated live collection, scheduling and independent report verification
remain unfinished.

## Artemis reference resolved

The Apollo upstream README explicitly links Artemis (Moonlight Noir) to
https://github.com/ClassicOldSong/moonlight-android. At 2026-11-25 06:27
UTC the repository reported nonarchived, GPL-3.0, default branch
moonlight-noir, HEAD c5cf27f4dc822db0e863c4691e7a70c74bea977a, latest
published release v20.2.6 (ID 238650766, published 2025-08-08),
direct tag commit 4de0227fb6ae5c9ad9f7cc486aed7c3571f5f62f, corroborated
by the commits endpoint. The reference is resolved; its initial metadata
status is REVIEW. It is not yet included in the four-repository structured
baseline. Extend membership and tests explicitly in a later reviewed
change. No client update, license conclusion or adoption is implied.

## Five-repository membership and report verification candidate

The structured inventory now explicitly includes the previously observed
Artemis metadata (ClassicOldSong/moonlight-android) as a fifth required
repository. This is an explicit membership migration, not a pin update;
the original four entries are unchanged. A four-repository observation
now yields ERROR for the missing Artemis row.

    python scripts/verify_upstream_review.py --baseline config/upstream-review-baseline.json --observed observed.json --report report.json

The read-only verifier bounds and strictly parses all three snapshots,
recomputes the expected report from the two input byte sequences and
requires exact JSON types, fields, ordered rows, statuses and SHA-256
bindings. Exit 0 means the claimed report matches the inputs, including
a correctly reported ERROR; exit 1 means invalid or unavailable evidence.
The verifier shares classification logic with the producer; it is an
independent invocation, not an independently implemented classifier.
It does not verify freshness, source authenticity or upstream safety.

A separate live metadata observation of all five repositories at
2026-11-25 06:39 UTC returned five UNCHANGED rows. Baseline SHA-256
081a6064bb23da17307defd61e17fd3ea274c9a529f8125edab5540fd6cb5ac1;
observed SHA-256
ecf0ad55f3700bb90952ccd06d07451eed54f967b81e808b3cffb54832b03578.
All tag references were direct commit targets corroborated by the
resolved commit endpoint. The actual report passed verification; a
separate modified copy with one missing row was rejected. Eight new
offline regressions cover mandatory Artemis membership and report
recomputation. Automated live collection, freshness and scheduling
remain separate. No dependency or installation changes.

## Public API observation adapter candidate

The offline API normalization boundary accepts five snapshots for one
reviewed repository: repository metadata, default-branch commit, latest
stable release, exact tag reference and resolved release commit. It checks
repository identity, explicit stable-release flags, exact direct tag ref,
corroborating commit SHA and the existing strict seven-field row schema.
An annotated tag is refused until bounded dereferencing is qualified.
The collector must omit failed rows so classification reports ERROR;
it must never substitute baseline values or silently accept a missing release.

The future transport is explicit read-only HTTPS to the fixed GitHub API
origin, with bounded responses, request and run budgets, no redirects,
no automatic retries, sanitized diagnostics and offline transport fixtures.
Snapshots are sequential observations, not an atomic remote transaction;
identity and corroboration checks do not establish freshness or origin
attestation. No scheduled workflow, network collector or baseline updates
are implemented by this adapter.

## Bounded public HTTPS collector candidate

Run explicitly, in a new private directory, without a token:

    python scripts/collect_upstream_review.py > observed.json
    python scripts/check_upstream_review.py --baseline config/upstream-review-baseline.json --observed observed.json

The collector uses fixed api.github.com HTTPS, standard certificate validation,
no redirects/proxy configuration/credentials/retries, five reviewed repositories,
up to 25 sequential GETs, 1 MiB response cap, 12-second worker timeout and
180-second run budget. Process startup/cleanup can add overhead. A worker
contains blocking DNS, TLS and HTTP reads; the parent enforces a timeout.
Output contains only normalized rows, no raw response or credentials. Exit 1
means missing rows or collection failure; classify incomplete observations as
ERROR, never substitute baseline. Rate limits and annotated tags fail closed.
This is public unauthenticated collection; GitHub may impose shared-IP limits.
No freshness attestation, atomic upstream snapshot, scheduled run, automatic
baseline mutation or dependency adoption is implied.

Actual public HTTPS observation from exact detached collector source
1f7aeae182c00c77106072cce5585017865ab657 on 2026-11-25 returned five
UNCHANGED rows; collector/classifier exit 0 and report verifier PASS.
Normalized observation SHA-256:
e3f9a8093e568c51718b6e2bd28886cb1ce520757e61d5919b7ffbcc5449e08f.
Baseline SHA-256:
081a6064bb23da17307defd61e17fd3ea274c9a529f8125edab5540fd6cb5ac1.

## Next freshness evidence design

Keep the existing classifier schema and exit semantics intact. Introduce a
separate versioned collection receipt binding the exact normalized bytes,
reviewed repository membership, collector checkout, start/end UTC, monotonic
elapsed duration and complete/incomplete result. Use an explicit verification
clock and reviewed maximum age/future skew; reject incomplete, inconsistent,
stale or future evidence. Do not equate local timestamps or digests with
remote authenticity, and do not use the receipt as release authorization.
Schedule only after offline receipt, actual collection and CI qualification.

## Local freshness receipt candidate

Schema 1 binds exact normalized observation SHA-256, full Git commit/tree,
canonical start/end UTC, monotonic duration in integer milliseconds and
complete membership. All five rows must validate. Verification takes an
explicit clock and expected source IDs, permits five seconds of future
skew and local UTC/monotonic discrepancy, and rejects observations older
than 24 hours measured from collection start. Duration cap is 185 seconds
(including five seconds of overhead beyond the collector budget). These
are provisional review-monitoring policy bounds, not product authorization.
Incomplete observations can be recorded but never pass freshness validation.
No remote attestation or trusted time source is implied; a party able to
rewrite observations and receipts can recompute hashes. The pure schema
and verifier precede CLI collection integration and scheduling.

## Source-bound watch CLI candidate

From the intended clean tracked Git checkout, create a new private bundle:

    python scripts/run_upstream_watch.py collect --output NEW_DIRECTORY --expected-commit FULL_COMMIT
    python scripts/run_upstream_watch.py verify --directory NEW_DIRECTORY --expected-commit FULL_COMMIT --expected-tree FULL_TREE

The CLI reads the approved baseline and checks actual source identity before
and after collection. It writes four exclusive files (baseline, observation,
report, receipt), refuses existing output directories, and verifies readback
against the current approved baseline and expected source. Exit 0 unchanged,
2 review, 1 error/incomplete. Verification refuses incomplete, stale, extra,
or mismatched evidence. Failed runs can leave a partial directory; do not
reuse it. Use a private owner-controlled parent. Windows directory mode is
not an ACL guarantee. No atomic directory publication, authenticity or remote
clock attestation is implied. Scheduled workflow remains separate.

The first actual source-bound run at 2026-11-25 07:01 UTC completed one
repository, omitted four, returned ERROR and wrote an incomplete receipt;
verification correctly refused it. A separate unauthenticated rate-limit
query returned core remaining 0 of 60. This is a live negative-path
qualification, not a complete freshness PASS. Do not retry until quota
recovers. The collector now terminates the remaining run on HTTP 429 or
403 with explicit quota exhaustion or Retry-After. Other failures retain
existing incomplete-row behavior. No authentication or automatic retries.

## CI evidence admission candidate

    python scripts/run_upstream_watch_ci.py collect --output NEW_ARCHIVE --expected-commit FULL_COMMIT --expected-tree FULL_TREE
    python scripts/run_upstream_watch_ci.py verify --output NEW_ARCHIVE --expected-commit FULL_COMMIT --expected-tree FULL_TREE

The CI wrapper requires the intended source tree before any collection,
creates a unique private root, and verifies the complete bundle before
writing a separate root-level file manifest. It verifies the manifest and
bundle again on readback. An incomplete or inconsistent run is not sealed;
failed directories may contain partial evidence and must not be reused.
The exact accepted archive contains bundle/ with four files and a root
manifest. Exit 0 is unchanged, 2 is review required, 1 is a failed gate.
A valid manifest cannot substitute for receipt or report verification.
No signing, publication, automatic updates or schedule is implied.

## Manual CI workflow candidate

The workflow `.github/workflows/upstream-watch.yml` is manual-dispatch only
and runs only on main. It permits one concurrent watch, does not persist
checkout credentials, bounds runner time, and uses the public HTTPS collector
without an API token. Collection and independent reopening must return the
same allowed exit/status pair. REVIEW is a visible warning and a valid
review-only report; it is not a passing dependency or release decision.
ERROR or contradictory results fail the workflow before artifact upload.
Accepted sealed archives are retained for seven days. The workflow is not
scheduled until a complete real freshness bundle and actual manual workflow
execution have been qualified. Proposed schedule: daily at 06:17 UTC,
subject to quota availability and freshness policy review. Hosted runner
images and action major tags are mutable, as tracked in engineering debt.

## Positive sealed live qualification

On 2026-11-25 at 08:16 UTC, an exact detached checkout of stacked PR #76
synthetic commit 1e4cec6b4b6932bc7925d6d0e40c2f2662ba4d0c (tree
0061c921c795344596b8c718ce4c4c1c27579df8) completed public collection.
All five reviewed repositories were UNCHANGED, receipt complete=true,
monotonic duration 12556 ms, collection/verification exits 0 and independent
manifest verification PASS. Observation SHA-256:
e3f9a8093e568c51718b6e2bd28886cb1ce520757e61d5919b7ffbcc5449e08f.
This qualifies actual local positive collection and sealed readback, not
hosted workflow execution, remote authenticity, or dependency acceptance.

## Offline review action plan candidate

The pure planner recomputes the classifier report from bounded exact input
bytes and rejects incomplete or modified claims. Every reviewed metadata
field maps to explicit review categories (source delta, compatibility,
security, release identity, artifact provenance, license and maintenance
as applicable). Changed repositories also require regression test planning
and owner review. Actions are sorted, deduplicated and bound to the exact
baseline, observation and report SHA-256 digests. UNCHANGED yields no tasks.
The plan always sets adoption_authorized=false and omits raw metadata values.
The planner alone does not establish freshness, source identity or origin;
sealed bundle admission is the next separate integration boundary.
