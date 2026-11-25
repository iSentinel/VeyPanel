# VeyPanel engineering, QA and project operating standards

Policy version 1.0 (adopted 2026-11-25). Applies to human and AI contributors.
Adapted from a user-provided portable policy, universal sections 0–17 and
adoption checklist. This document is normative, not an assertion of existing
implementation. The adoption audit tracks incomplete gates and exceptions.
AGENTS.md retains local safety requirements; stricter applicable safety and
approval boundaries take precedence. Never transfer another project's approvals,
credentials, internal provenance, hardware results or dependency profile.

## 1. Workflow and continuity

Inspect the branch, actual HEAD, working tree, AGENTS, ROADMAP, RESUME,
architecture, relevant sources/tests and CI results/logs at each session.
Review relevant upstream changes before changing pins. Select a bounded
roadmap stage with prerequisites, risks and acceptance criteria. Reproduce
defects, add regression tests, implement the smallest suitable change, run
relevant checks and common QA; never weaken assertions. Preserve public
contracts, concurrent edits and history. Reject unexpected concurrent changes.
Keep code, tests, docs, configuration and evidence together. Report progress
and failures in the chat or review; after each stage continue only independent,
unblocked work. No invented evidence, asynchronous progress or authorization.

Checkpoint: actual source revision; requirement; changes; commands, environment
and evidence; CI link/status; limitations, blockers and approvals; next action.

## 2. Code and architecture

English identifiers, useful comments, diagnostics, CLI help and technical
docs; localization separate. Python maintenance tools follow PEP 8; functions
and methods preferably <=40 physical lines (def through end, docstrings
included, decorators excluded). Public classes/functions have useful docstrings,
parameters and returns annotated (self/cls exempt; constructors included).
Use concrete types, bounded inputs, deterministic behavior and resource cleanup.
Separate UI, authorization, telemetry/data path, adapters, validation,
persistence, reporting and orchestration. Reject unknown types, ambiguous
values, invalid ranges and unsupported APIs. Catch expected exceptions, never
silently swallow unexpected failures; use safe diagnostic categories. Bound
memory, file reads, loops, concurrency, retries, timeouts and cancellation.
No untrusted shell interpolation.

C# .NET 10 / ASP.NET Core / WPF: nullable-aware typed contracts, XML docs
for public contracts, IDisposable/IAsyncDisposable, CancellationToken and
bounded async operations; compiler/analyzers and Windows integration.
Java 17 / Android: explicit types, Javadoc for public contracts, bounded
executors, lifecycle cancellation and native lint/fixtures/instrumentation.
JS dashboard: small functions, safe DOM rendering, explicit types/ranges at
boundaries, syntax checks and later lint/browser/accessibility acceptance.
PowerShell: advanced parameter validation, explicit exit/error handling,
bounded process lifetime, help; Bash: explicit shell/pipefail, finite timeouts
and syntax checks. The 40-line design target applies by equivalent method
scope; no claim of automated native length or documentation enforcement yet.

## 3. Quality gate and technical debt

Python source-only AST scan of tracked/staged Python files, without imports.
Stable identity is (path, qualified symbol, rule, detail); preserve duplicates.
All functions including private/nested checked for length; public top-level
functions/classes and public methods of public classes checked for docstrings
and annotations, including constructors. Nested implementation functions and
private scopes are exempt only from public documentation/annotation checks.
Tests are included. Line numbers are informational. Exact baseline is reviewed
migration debt, not a waiver or compliance certificate; reject new and stale
entries, remove resolved identities in the same change. No automatic baseline
regeneration. New exceptions require explicit review. Lint, static typing and
runtime gates remain distinct; native equivalents and full lint are roadmap work.

## 4. Logging and diagnostics

Use appropriate existing platform logging (ILogger for Host, safe Android
logging, standard-library Python for small offline utilities). Do not introduce
Loguru or other runtime dependencies solely for policy adoption. New operational
event interfaces require versioned, allowlisted fields (UTC, level, stage,
status, safe reason, monotonic duration and authorized run identity). Machine
output on stdout, diagnostics on stderr/private logs. Preserve legacy human CLI
formats until explicit migration; no raw variable capture, credentials, private
paths/endpoints or SDK bodies in shared evidence. The explicit private local
enrollment link is user-facing, never general log permission. Test canaries,
invalid fields and failure paths. Bounded private retention/rotation required
where persistent logging is introduced.

## 5. CLI and automation

Support help, documented inputs, stable exit semantics, clear noninteractive
results. Preserve existing exit codes; document migrations separately.
Dry-run is read-only. Installation/update validates platform, target, identity,
resources and concurrency; bounded work, idempotence and rollback. Every
installer build documents prerequisites, dry-run, apply, rollback and uninstall.
Never put credentials in arguments, history, source, artifacts or logs.
Externally trusted SHA-256 is integrity evidence, not authentication.

## 6. UI

Accessible keyboard navigation, responsive geometry, no clipping or overlap,
clear loading/empty/blocked/error/stale/unavailable states. Unknown readings
are null/N/A. Separate preview, plan, approval, execution and result. WPF,
browser and native Android visual/hardware checks are separate from source
tests. If a TUI is introduced, b=back, q=exit, no raw JSON as normal UI.

## 7. QA

Offline default; separate unit, mock, local integration, emulator/upstream
fixture, physical hardware and actual workload/product acceptance. Live lab,
production-like, destructive and fault tests require separate reviewed scope
and approval. Test malformed/boundary/denial/timeout/interruption/concurrency/
restart/recovery cases; preserve deterministic sanitized fixtures. Fail closed
on missing mandatory reports, failed later stages or all-skipped suites.
Maintain stable case catalog with prerequisites, safety class, commands,
expected outcomes, evidence and limits. No mocked measurements or fake
certification. Results: PASS (actually executed scoped check met criteria),
FAIL (sufficient evidence of failed check, identify executor/product),
INCONCLUSIVE (insufficient evidence), BLOCKED (prerequisite/permission),
UNSUPPORTED (assessed scope lacks capability), SKIPPED (reason), NOT_RUN
(not executed). Command exit mappings are separate.

## 8. Evidence and measurement

Separate executor result from product verdict. Bind evidence to actual
checkout/tree, toolchain, dependencies, scope, case/run/attempt IDs, environment,
commands, budgets and elapsed monotonic durations. Versioned JSON/JSONL and
JUnit, clear human summaries, separate raw and derived evidence. Missing values
are not zero. Unique private run dirs, no concurrent mixing or overwriting;
independent required inventories, sizes/hashes, bounded reads, reject links
and unsafe types, detect mutations, verify on reopen. Protect evidence and
accepted artifacts; local hashes do not prove producer identity, truth or
durability. Correlate UTC with clock uncertainty, do not subtract timestamps
from unsynchronized hosts. Define telemetry units (logical/physical bytes,
bits, operations, durations); compare equivalent workloads with adequate
samples and explicit thresholds, never average percentiles. Defect matrix
records ID, expectation, observation, evidence strength and replayable fixture.

## 9. Security

Local-only and least privilege, explicit target identity/ownership and
allowlists. Read-only is not write/destructive authority. Review budgets,
deadlines, emergency stop and recovery before changing lab operations.
Verified TLS, approved CA, no speculative management or certificate bypass.
Uncertain execution remains unresolved; reconcile before retry or cleanup.
No production credentials in CI; private evidence and access control. No
customer data, keys, private endpoints or unreviewed artifacts in public Git.
Preserve licenses/notices and repository visibility. Separate approval for
publication, deployment, destructive operations or visibility change.
Preserve display topology backup/rollback; no unsigned-driver bypass.

## 10. Stateful operations

For package staging/selection/recovery, enrollment and future streaming
control: separate preflight, immutable plan, admission/approval, execution,
collection, reconciliation and reporting. Plan digest is not authorization.
Validate scope, identity, readiness, schema and budgets at each transaction;
persist pending/terminal identities, fence concurrent writers and stop on
uncertain state. Do not blindly retry, resume, delete or adopt orphaned state.
Verify backups/restores and explicit recovery. Distributed workers are not
currently implemented; if introduced, require authenticated enrollment,
bounded freshness, single-use challenges, revocation, durable reservation,
lease/attempt/receipt binding, replay rejection and fencing. Expiry is
uncertainty, not cancellation; no automatic reassign/retry. No consensus,
attestation or nonrepudiation inferred from local records or a MAC.

## 11. CI/CD

One provider-independent QA entrypoint with common result/evidence contract;
GitHub Actions wraps it alongside required native jobs. GitLab/TeamCity
remain unqualified until real execution on those platforms. Isolated
checkouts, pinned toolchains/actions/images, minimal permissions, bounded
timeouts, no shared artifact directories. Mandatory relevant dependency,
lint, doc, debt, regression, build and CLI checks; fail on missing required
reports, retain sanitized failed evidence. Import JUnit where supported;
artifact presence alone is not import qualification. Offline against live
targets; dependency acquisition and advisory metadata network access are
separate scoped jobs. Preserve identities/access/secrets safely in any future
migration. Mutable hosted runner images and action major tags are tracked
migration debt; never claim exact pins where absent.

## 12. Dependencies and upstream

Review direct/transitive pins and hash locks, exact upstream commits and
artifact identity, SBOM, notices, advisory scans and disposition. No automatic
bumps or unreviewed upstream binaries. Separate third-party executables and
honor licenses. Maintain review-only upstream watch inventory (GitHub repo,
HEAD, accessible release identity, role), review at session start and
scheduled observation; status REVIEW/UNCHANGED/ERROR, no incomplete query
reported unchanged. Missing release is not absence of tags. Review changes,
assets, compatibility, safety, license and tests; official protocol/product
docs may supplement verified GitHub references. Do not adopt storage-specific
dependencies or unrelated reference infrastructure.

## 13. Installer, updates and rollback

Verify target identity, supported version/platform, permissions and capacity.
Read-only Doctor is not durability/readiness. Snapshot and hash affected state
with actual restore qualification where relevant; no off-host guarantee from
local copies. Fence writers, test readiness, installed identity and readback,
document tested rollback and uninstall. Refuse incompatible/incomplete state.
Current private package roots require exclusive owner control; explicit
recovery, process coordination, migration and power-loss qualification remain
open. No automatic orphan deletion or lock clearing.

## 14. Release

Immutable candidates/tags/evidence, exact version/source/tree/toolchain/locks/
hashes/signatures/test results/hardware scope/limitations. Compare actual
same-source builds and disclose differences. Record baseline/candidate,
update and rollback. Owner Approval must be explicit and candidate-bound;
sole owner is not independent review, signing or technical qualification.
Separate release, deployment, destructive tests and external publishing
authorization. Development PRs under existing repository workflow are not
production release approval. No release or signing key changes by adoption.

## 15. Documentation

Git canonical English docs alongside changes; prerequisites, usage, expected
outcomes, limitations and evidence. Keep existing docs/architecture.md
canonical rather than duplicate ARCHITECTURE.md. Confluence mapping if adopted:
stable local IDs/parent/title/Markdown source/module coverage, validate
hierarchy and uniqueness offline, no publish without approval. Qualify actual
platform/API, stable remote IDs and versions, parent-first dry-run diff,
conversion/render/link/attachment verification; stop on conflicts. Deletion
and reparenting separately authorized. No publication currently configured.

## 16. Local profile and layout

Keep existing src/, android/, scripts/, tests/, docs/, global.json and native
build layout; config/ for reviewed audit/watch data. Windows .NET SDK 10.0.404,
win-x64 self-contained, Host/Desktop Alpha.10; Android Java 17, Gradle 8.9,
AGP 8.7.3, API 35, min 26, Alpha.18; Python 3.12.10 Windows CI and standard
library maintenance scripts (local 3.13.5 is additional observed environment,
not a supported matrix). Node syntax checks, PowerShell, Bash. No new S3,
SQLite, boto3, Loguru, pytest or infrastructure dependencies imported.
Native package locks and Gradle verification exist with limited scope;
runtime packs, SDK/tool images and release signatures remain qualification
work. Private QA output is not committed. No filesystem mass migration.

## 17. Definition of done

Implemented scoped requirement, executed regression tests and applicable QA,
updated public contracts/docs, safe shared evidence, exact revision and
results recorded. Report partial/BLOCKED/awaiting CI where criteria are
unmet; continue independent safe work, never bypass mandatory checks.
