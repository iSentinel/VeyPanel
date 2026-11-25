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
