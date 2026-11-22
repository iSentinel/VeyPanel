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

Alpha.3 source: added CCD active-path/mode capture and recovery design, no SetDisplayConfig calls. Eight new tests cover ABI, index decoding, validation, JSON and live query. CI pending. Next: verify tests, implement stable target identity and explicit local pairing. Latest verified artifact remains alpha.2 until CI confirms.

Alpha.3 identity increment: added read-only DisplayConfigGetDeviceInfo source and monitor identifiers, EDID availability, connector metadata and conservative same-session matching policy. Identity failures remain visible, not fabricated. Added ABI and recovery-policy tests. No restore commands or writes. CI pending. Next: verify CI and implement local PIN pairing with explicit operator approval; no topology mutation until real hardware recovery acceptance.

Alpha.3 PIN increment: added explicit local operator-confirmed pairing, validated ASCII PIN/device name, no permission edits or automatic retry; five more Apollo mock tests. Live device acceptance pending. Next: verify all CI, prepare WPF UI and safe topology validation.

Alpha.3 validate-only increment: added --display-validate. Captures current topology twice, checks identity and exact stability, invokes SDC_VALIDATE with fixed flags only, then checks topology again. No apply/save/allow-changes flags or external snapshot import. Two extra policy tests. Native validation on physical host not executed. Next: check all CI, implement WPF/tray UI and collect hardware acceptance before enabling rollback writes.

Alpha.3 desktop increment: WPF read/validate-only two-tab diagnostic UI and tray shell, separate Windows x64 CI artifact. Shares the existing diagnostic source files. No Host lifecycle, stream control or driver changes. Build and interactive acceptance pending. Next: verify all CI and prepare desktop telemetry lifecycle controls; physical hardware acceptance gates remain unchanged.
