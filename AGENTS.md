# VeyPanel engineering rules

The canonical policy is [docs/engineering-standards.md](docs/engineering-standards.md).
Read it before changing code. Its adoption audit and migration register are
[docs/engineering-adoption-audit.md](docs/engineering-adoption-audit.md).
Existing local rules below remain mandatory; neither file grants release,
deployment, destructive operation, external publication or hardware approval.

- Inspect HEAD, branch, tracked/untracked changes, AGENTS, ROADMAP, RESUME,
  relevant architecture, sources, tests and actual CI before changes.
- Work in focused reviewed commits; reproduce defects, add regression tests,
  run relevant native and common QA gates, record actual evidence and limitations.
  Continue independent work without bypassing a blocked gate.
- English code, diagnostics, help and technical documentation. Small focused
  typed methods, useful comments and documentation; exact debt reduction, not
  silent baseline regeneration. Preserve public contracts.
- Only real data; unavailable sensors must be null/N/A, never fake zero.
  Use UTC sample timestamps, stale detection and monotonic local durations.
- Local-only by default. No cloud dependency, internet exposure, automatic
  firewall changes, untrusted drivers or TLS bypass. Keep tokens and private
  data out of shared output; the explicit local enrollment link is a private
  user-facing secret, not a logging exception.
- Do not alter display topology without prior configuration and rollback.
  No Secure Boot/test-signing bypass. No live input or fault injection without
  reviewed scope and separate approval.
- Every release requires exact version/source, tests, artifact hashes, build
  evidence, sample dry-run/install commands, rollback/uninstall and limitations.
  Hardware PASS only after actual device tests. No release or deployment
  authorization inferred from adoption or successful CI.
- Keep third-party components separate until licenses and redistribution
  obligations are reviewed. No automatic dependency bumps.
- Run the source audit and Python offline QA entrypoint in addition to
  Windows/Android native checks. A scoped PASS is not full compliance.
- Keep ROADMAP and RESUME current after each stage; record source, command,
  environment, result, CI link, blockers, approvals and next independent action.
