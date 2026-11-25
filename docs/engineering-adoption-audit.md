# Engineering policy adoption and gap register

Adoption source: user-provided portable policy v1.0, universal sections 0–17
and checklist. Scope intentionally excludes unrelated project profile,
provenance and approvals. Reviewed repository baseline:
012d49c3628789d00acd0d67d75a4e0180990cd6. Existing development workflow only;
no release, visibility, deployment, live lab or external documentation changes.

## Findings and migration

| ID | Policy area | Observed state / gap | Priority and acceptance |
|---|---|---|---|
| ENG-01 | Continuity/DoD | AGENTS/ROADMAP/RESUME exist; historical checkpoints mix candidate and verified notes; architecture outdated | P1 maintain scoped checkpoints, update canonical architecture and security |
| ENG-02 | Python quality | Source-only audit initial 469 findings (345 annotation, 123 docstring, 1 length); 22 resolved in build source evidence and tests, 447 remain | P1 exact debt gate, reduce by module, no added/stale entries; broader lint/types separate |
| ENG-03 | Native code quality | C# nullable/build, Android lint, JVM fixtures and JS syntax exist; no unified native debt/analyzer gate or rendered geometry acceptance | P1 audit native methods/contracts, add reviewed native lint/analysis |
| ENG-04 | Logging/privacy | Existing human CLI and local private enrollment link; no versioned shared event schema or secret-canary suite across components | P0 audit log paths, preserve CLI contracts, add safe event and canary tests |
| ENG-05 | CLI/install | Staging and selection/rollback verified, launcher PR #37 Windows CI PASS but unmerged at audit; recovery branch local; no coordinated lifecycle/uninstall/restore qualification | P1 explicit dry-run and recovery, process/data boundaries, real Windows acceptance |
| ENG-06 | UI | Browser, WPF and Android exist; emulator smoke is not interactive/physical geometry/accessibility acceptance | P1 native lifecycle and rendered UI regression, physical gates remain blocked |
| ENG-07 | QA/catalog | Python unittest, C# smoke, JVM and Android instrumentation exist; no single common QA runner/JUnit contract or stable cross-stack catalog | P1 add scoped common entrypoint, JUnit and catalog; then qualify native result adapters |
| ENG-08 | Evidence | SHA-256 manifests, checkout/toolchain/runtime reports and reproduction evidence exist; incomplete independent inventories, atomic/private publication, file mutation checks and common run records | P0 audit manifest and package safety; preserve distinct authenticity/durability claims |
| ENG-09 | Security | Loopback default, verified TLS, reader grants, DPAPI, Android Keystore, display validate-only; no complete security audit, signing/physical acceptance | P0 review fail-closed trust boundaries, cancellation, secret exposure and physical authorization |
| ENG-10 | Recovery | Atomic selection record and cooperating lock; no qualified crash/power-loss recovery, process lifetime fencing or migration | P0 no automatic lock removal/orphan adoption, explicit recovery and reconciliation |
| ENG-11 | CI portability | GitHub workflows exist, explicit pipefail corrected; major-tag actions, Windows CI lacks job timeout, no qualified GitLab/TeamCity or common JUnit import | P1 pin reviewed action SHAs, bounded jobs, portable wrappers and real target qualification |
| ENG-12 | Supply chain | Host NuGet and Android debug runtime locks, Gradle checksums, scoped SBOM/license/OSV reports; no full build/runtime pack locks or watch inventory | P1 upstream observation, review-only changes, redistribution and advisory disposition |
| ENG-13 | Release | Experimental payload reproduction, portable unsigned ZIP, source evidence; no signed attestation, production signing or qualified release/installer | BLOCKED until explicit candidate approval and technical gates; do not publish releases |
| ENG-14 | Documentation | Canonical Git docs present, no SECURITY.md or stable Confluence hierarchy | P1 refresh architecture/security and local catalog; Confluence conditional, publication disabled |
| ENG-15 | Runtime evidence | PR #36 runtime PASS; post-merge main Android run 45509804749 failed dependency resolution HTTP 429 before instrumentation | BLOCKED for current runtime acceptance; one retry requested, no security bypass or pin changes |

## Explicit adaptations and exceptions

- No S3/storage/controller profile, unrelated approvals or dependencies. Java,
  C#, JS and PowerShell use native equivalents; Python AST gate is scoped only
  to tracked Python source including tests. Existing stdlib utilities remain
  dependency-free; Loguru not added. New structured events are migration work,
  not a blanket exception to confidentiality.
- Legacy debt baseline is an exact migration inventory, not a perpetual
  exception or proof of review of all implementation semantics. No new debt
  without explicit review. Initial inventory generated from actual source;
  first 22 identities removed only after regression tests and comparison.
- Existing human stdout/exit contracts preserved; introduce machine evidence
  in a separate runner. No TUI or distributed worker controller mandated.
- GitHub development PRs continue under existing workflow; no external
  Confluence, production deployment, release or visibility change authorized.
- Hosted image labels and major action tags are temporary migration gaps,
  not accepted release pins. Python local 3.13.5 is observed, Windows CI
  remains pinned 3.12.10; Android native tooling unchanged.
- Hardware, interactive WPF, display topology changes and live input are
  not inferred from hosted CI. No unsafe work to unblock them.

## Evidence and priorities

Initial tracked inventory: 29 Python, 51 C#, 44 Java, 2 JS, 4 PowerShell
scripts, 3 shell scripts (plus PowerShell module). Counts are file inventory,
not semantic audit coverage. AST scan covers all tracked Python files and
new auditor fixtures. Native code, security and UI audit is initial targeted
inspection, not exhaustive verification. PR #37 Windows jobs 45509910174 /
45509902471 PASS; no WPF launch. Latest main runtime failure raw logs identify
Maven HTTP 429; do not classify as application failure. Keep original failed
attempt evidence. Next: common Python QA report and exact baseline gate,
then reduce remaining debt and qualify native and recovery stages.

The adoption change adds the scoped common Python runner, initial suite catalog,
SECURITY.md and current architecture; ordinary Windows and Android CI invoke
the shared Python gate before native build. Windows CI timeout is bounded.
Native JUnit import, all native wrappers and formal doc validation remain open.

### First common CI finding
The initial Windows shared gate failed 1/124 on the raw ZIP backslash
fixture (downloaded JUnit, run 45514689128). Windows ZIP name normalization
masked the intended fixture. The correction validates the original filename
and generates literal raw ZIP backslash/NUL entries portably; 18 exact test
module findings resolved (429 remaining). Corrected CI pending. The bounded
rerun of main Android runtime 45509804749 completed successfully; retain
the first environmental failure in history.

## Verified adoption checkpoint
PR #38 merged as 3cb4477 after ten CI jobs passed. Downloaded Windows
and Android common QA reports confirm 125/125, exact debt baseline 429,
zero new/stale findings and matching source tree. Native and hardware
qualification remain separately scoped.
