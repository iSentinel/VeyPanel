# Resume checkpoint

2026-11-22 — VeyPanel 0.1.0-alpha.3.

## Verified
- Alpha.2 host, CPU/RAM, Apollo inventory, GDI inventory and HTTPS LAN CI: run 45047071449.
- Alpha.3 active CCD topology capture: run 45049611656; target identity and conservative eligibility: run 45049672009; explicit PIN and mock tests: run 45049726317.
- Validate-only command and guards: run 45049793209 completed successfully (8/8 CPU math, 14/14 Apollo mocks, 12/12 CCD tests, host and HTTPS LAN smoke). Hosted CCD query returned partial, 1 path/2 modes; this is not target topology acceptance. Native SDC_VALIDATE on physical PC remains untested.
- Verified alpha.3 host artifact: https://github.com/iSentinel/VeyPanel/actions/runs/45049793209/artifacts/14765157246 (unsigned).
- Latest program commit 06de9cb03ad9550c3cc5e991da4916d727906e0a adds WPF desktop diagnostics and tray shell. CI in progress at checkpoint: https://github.com/iSentinel/VeyPanel/actions/runs/45049892455. Interactive acceptance pending regardless of CI.

## Next steps
1. Check WPF CI; fix any build problems and verify artifacts; run physical desktop GUI acceptance.
2. Implement desktop telemetry Host lifecycle and local dashboard controls; keep credentials and tokens out of logs. Add bounded shutdown/reconnection.
3. Validate actual Apollo installer, signed driver, certificate and API on physical Windows host; pair Lenovo with explicit permission. Test 2000x1200, 60 Hz and Intel Quick Sync.
4. Design and test independent rollback watchdog in controlled hardware environment before implementing any topology apply/restore. Current validation accepts fresh native paths only and never applies/saves settings.
5. Continue roadmap telemetry sensors, WebSocket and Android client.

No production driver install, device pairing, monitor setting changes or real streaming performed. Real Lenovo/Intel Arc acceptance remains pending. Source license remains an owner decision; no upstream binaries redistributed.

Alpha.4: previous WPF CI 45049892455 PASS, GUI physical acceptance pending. Added bundled Host process management, fixed loopback managed mode, stdin-owned shutdown, readiness verification, start/stop/open controls and lifecycle tests. New CI pending. No topology mutation or live pairing. Next: verify alpha.4 CI, add GUI Apollo controls and diagnostics; actual hardware acceptance remains pending.

Alpha.4 Apollo GUI: added certificate-pinned local inspection and single operator-confirmed PIN pairing. No password/PIN persistence, no automatic permission or stream changes. UI compile and actual GUI/device acceptance pending. Next: check CI and add read-only extended telemetry; hardware gates remain open.

Alpha.4 resource increment: per-interface byte rates via IP statistics and monotonic deltas, logical fixed-volume capacity refreshed at five seconds, null status handling and web panel, rate arithmetic and runtime schema checks. Actual SSD SMART/I/O and GPU sensors remain pending. Latest CI pending.

Alpha.4 disk increment: native Windows PDH PhysicalDisk(_Total) English counters for read/write throughput and IOPS. Two-sample warm-up, explicit unavailable status, bounded query reopen, ABI/normalization and published runtime schema tests. No per-disk mapping/SMART/temperature. Latest CI pending. Next: verify CI, then implement GPU engine telemetry and WebSocket independently of physical streaming acceptance.

Alpha.4 GPU increment: added Windows x64 PDH GPU Engine wildcard sampling, localized path lookup, bounded buffer parsing, conservative per-engine aggregation and explicit Video Encode/Decode N/A. Six new tests; actual Intel Arc counters and adapter mapping remain unverified. Latest CI pending. Next: confirm CI and implement WebSocket telemetry with REST fallback.
