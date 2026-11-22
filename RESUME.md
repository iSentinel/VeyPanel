# Resume checkpoint

2026-11-22 — VeyPanel 0.1.0-alpha.4.

## Verified evidence
- Alpha.3 WPF and Host build completed successfully in run 45049892455.
- Managed Host lifecycle (run 45050593038): authenticated readiness, idempotent start/stop, port collision, token rotation, disposal. Bundled desktop artifact compiled and published. Interactive WPF acceptance remains pending.
- Apollo GUI inventory and explicit PIN pairing build (run 45050643363). Existing mock protocol tests passed; no live Apollo pairing or streaming.
- Network interface throughput and fixed-volume capacity (run 45050707013): integration schema and rate math passed.
- Native PDH PhysicalDisk(_Total) throughput/IOPS (run 45050803404): build, all existing smoke tests, local and HTTPS LAN integration, managed lifecycle and desktop publish passed. Runtime disk capability reported ok. No physical SSD mapping or SMART acceptance.
- Latest fully verified code commit: 61566580ab80799f1206e11fc9f83146cd07fbf1.
- Verified bundled Desktop/Host (unsigned): https://github.com/iSentinel/VeyPanel/actions/runs/45050803404/artifacts/14765336763
- Verified standalone Host (unsigned): https://github.com/iSentinel/VeyPanel/actions/runs/45050803404/artifacts/14765207177

## Latest source
Commit 51c5616b58fb1483c01256dc7eb709268ff80915 adds experimental Windows x64 GPU Engine PDH sampler, language-neutral path lookup, bounded buffer parsing, per-engine aggregation and Video Encode/Decode metrics. Six additional synthetic/ABI tests and runtime capability schema. CI in progress at checkpoint: https://github.com/iSentinel/VeyPanel/actions/runs/45050942800. Target GPU capability, named adapter mapping and actual encoder usage are not verified.

## Next steps
1. Verify final GPU CI and artifacts; fix any failures. Build a WebSocket telemetry channel with authentication, origin checks, bounded sessions and REST fallback.
2. Continue GPU adapter mapping, temperatures, storage I/O/SMART and sensor capability detection; actual Intel Arc and Lenovo remain physical acceptance gates.
3. Verify actual Apollo v0.4.6 installer, certificate, signed driver and API on physical Windows host; pair Lenovo and test Mirror/Extend, 2000x1200 at 60 Hz, Quick Sync and permissions.
4. Before display mutation, implement and hardware-test an independent rollback watchdog. CCD native capture was partial on hosted runner; validate-only flags and guards passed tests, not actual target SDC_VALIDATE acceptance.
5. Continue device enrollment, Android client and installer.

No actual driver installation, production pairing, monitor topology changes or streaming took place. GUI launch and operation on target Windows, GPU telemetry on Intel Arc, browser HTTPS trust on Lenovo and physical recovery remain unverified. License decision for original source remains pending; no upstream binaries redistributed.

Alpha.5: GPU CI 45050942800 completed successfully (6/6 synthetic/ABI tests; runtime GPU status warming-up). Added /api/v1/telemetry/ws, first-frame token auth, origin allowlist, eight slots including pending auth, five-second auth timeout, bounded send, read-only session, browser reconnect/REST fallback and loopback integration tests. CI pending; actual WSS on Lenovo remains unverified. Next: verify CI, extend WSS testing and sensor mapping.

Alpha.5 transport testing increment: added same-listener CSP connect-src, secure WebSocket test on real private NIC with temporary trusted-by-pin CI certificate, untrusted WSS rejection, query prohibition and eight authenticated socket capacity check. CI pending. Browser compatibility and Lenovo certificate trust remain physical tests.

Alpha.5 DXGI increment: enumerates DXGI 1.1 adapter names/vendor/device/capacity, matches PDH LUID groups to named adapters, preserves unmatched observations and null readings. Refresh every ten seconds; no raw LUIDs serialized. ABI and mapping tests plus live inventory smoke added. Target Intel Arc matching and loaded video engine acceptance pending.
