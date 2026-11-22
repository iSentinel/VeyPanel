# Resume checkpoint

2026-11-22 — 0.1.0-alpha.2 development.

Alpha.1: Windows CI run 45045388584 passed 8 CPU math checks and published-host runtime smoke; subsequent runs 45045444610 and 45045477877 also completed successfully. Artifact for prior validated revision: https://github.com/iSentinel/VeyPanel/actions/runs/45045388584/artifacts/14763099335

Alpha.2: local Apollo adapter source implements pinned TLS certificate, cookie login, app and paired-client inventory, and interactive credentials. New mock protocol/certificate tests are written; CI and actual Apollo compatibility not yet verified at this checkpoint. No configuration writes/driver install/remote admin endpoint. Login can replace existing upstream Web UI session. See docs/apollo-poc.md.

Added GDI desktop-source inventory CLI using EnumDisplayDevicesW and EnumDisplaySettingsExW; this is a diagnostic baseline only, not a complete active-path backup or rollback implementation. Layout/runtime smoke tests added. No new display configuration writes.

Next: confirm CI; validate real Apollo v0.4.6 installer, certificate provenance and API on target, implement full DisplayConfig topology capture and recovery, then pair/stream test on Lenovo. Physical LAN TLS dashboard and Quick Sync acceptance remain pending. Original source license remains an owner decision.
