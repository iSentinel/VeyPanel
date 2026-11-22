# Resume checkpoint

2026-11-22 — 0.1.0-alpha.2, Windows CI verified.

Alpha.1: Windows CI run 45045388584 passed 8 CPU math checks and published-host runtime smoke. Subsequent runs 45045444610 and 45045477877 also completed successfully.

Alpha.2:
- Apollo v0.4.6 local inventory adapter with pinned TLS certificate, cookie authentication and interactive credential entry. Run 45046872073 passed nine protocol/certificate mock tests and published-host smoke. Live Apollo compatibility remains pending.
- Read-only GDI desktop source inventory via EnumDisplayDevicesW and EnumDisplaySettingsExW. Run 45046953751 passed native structure layout tests and found one active desktop source on the hosted Windows runner. This is not a complete DisplayConfig topology backup or rollback implementation.
- RFC1918-only HTTPS LAN listener and automated local private-interface integration smoke. Run 45047071449 succeeded: zero build warnings or errors, 8/8 CPU math, 9/9 Apollo tests, Win32 layout/inventory, address-policy check, published-host runtime smoke and real HTTPS tests with a temporary test certificate. Wrong certificate pin, untrusted certificate and wrong/missing API tokens were rejected.
- Latest verified code commit: 71b3f98f766315e6d780c124c80a0bbbb7bb1e6e.
- Windows x64 self-contained CI artifact (unsigned, not a stable release): https://github.com/iSentinel/VeyPanel/actions/runs/45047071449/artifacts/14764520285
- CI evidence: https://github.com/iSentinel/VeyPanel/actions/runs/45047071449

Next: full DisplayConfig read-only active-path capture and recovery design; validate actual Apollo v0.4.6 installer, certificate provenance and API on target, then pair/stream test on Lenovo. Real Lenovo HTTPS trust, Intel Quick Sync, Mirror/Extend, Android client, WPF and topology restore remain pending. No driver or display settings changed. Apollo login can replace existing upstream Web UI session. Original source license remains an owner decision. No third-party binaries redistributed.
