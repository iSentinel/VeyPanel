# VeyPanel test catalog (initial scoped registry)

Stable suite IDs below identify layers, not a count of individual test cases.
Only the Python runner currently emits a common JSON/JUnit contract.
Native report adapters and per-case catalog expansion remain roadmap work.

| ID | Layer / prerequisites | Command or workflow | Acceptance / evidence / limits |
|---|---|---|---|
| QA-PY-01 | Source-only, Git and Python 3.12 | python scripts/code_audit.py | Exact reviewed identities, no new/stale debt; not full lint/type checking |
| QA-PY-02 | Offline Python, Git, fresh private output | python scripts/run_offline_qa.py --output artifacts/qa-unique | All required Python unittest cases execute, audit PASS, summary and JUnit; native/hardware NOT_RUN |
| QA-WIN-01 | Windows x64, pinned .NET SDK, Python, Node | .github/workflows/ci.yml; dotnet run --project tests/VeyPanel.Smoke -c Release | Host smoke, native policy, publish, local HTTPS/WSS, storage/lifecycle; no interactive physical acceptance |
| QA-AND-01 | JDK 17, Gradle 8.9, SDK 35 | .github/workflows/android.yml | JVM fixtures, strict dependency verification, lint, APK integrity, negative signature/permission gates |
| QA-AND-02 | Isolated API 33 emulator | .github/workflows/android-runtime.yml | Actual instrumentation assertions, final result gate; no physical device or Windows Host |
| QA-REPRO-01 | Independent same-checkout runners | android-reproducibility.yml, windows-reproducibility.yml, desktop-reproducibility.yml | Exact comparable scope and hashes; debug signing differences and mutable runner evidence separate |
| QA-PKG-01 | Isolated package fixture/private Windows CI root | staging and selection tests, ci.yml | Dry-run, refusal, exact extracted manifests, selection/rollback; no automatic activation or physical durability |
| QA-SUPPLY-01 | Pinned resolved runtime graph, scoped public advisory access | runtime-advisories.yml and native dependency gates | Scoped SBOM/locks/hash/OSV evidence; not full redistribution/security audit |
| QA-LAB-01 | Explicitly approved Windows + Lenovo lab | docs/android-owner-acceptance.md and roadmap | Actual physical UI, TLS, telemetry/video/input acceptance; NOT_RUN by routine CI |
| QA-FAULT-01 | Separate approval, recovery plan and budget | Future approved lab plan | Physical interruption/recovery and fault acceptance; BLOCKED until prerequisites |

Offline runner example (create the parent directory first; output must be new):

    python scripts/run_offline_qa.py --output artifacts/qa-unique

Exit 0 scoped PASS, 1 execution/report error, 2 failed audit/test gate.
Reports: code-audit.json, python-results.xml, summary.json. A missing report
is incomplete evidence, never PASS. The existing native CI jobs retain
their own checks and exit contracts. Actual CI import of JUnit, full
provider-independent native orchestration and private evidence storage
qualification remain open.

## Required Python case inventory (candidate)

QA-PY-02 now uses the reviewed, versioned config/python-qa-cases.json
registry. The initial 199 identities were independently reconciled with
accepted Windows JUnit from PR #50, then eight new inventory fixtures
were explicitly added. Discovery must match the entire registry, without
missing, extra or duplicate cases, before execution. Every required case
must execute and PASS; a skipped or expected-failure mandatory case fails
the gate. No automatic catalog regeneration in CI. Add or remove identities
only with a reviewed test-scope change and its evidence in the same commit.

case-inventory.json records discovery counts, missing reviewed identities
and execution verdict; unexpected raw identities are not exported in
that report. On discovery mismatch the runner emits an empty actual JUnit,
zero executed tests and a failed gate; it does not synthesize results.
An unreadable/invalid registry is an execution error, not success. Existing
summary/JUnit fields and exit contracts remain, with additive inventory
fields. Native suites, actual CI import, subprocess isolation and deadlines
remain separate. No native or hardware acceptance follows from Python PASS.
