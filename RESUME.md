# Resume checkpoint

2026-11-22 — VeyPanel 0.1.0-alpha.7.

## Verified evidence
- Alpha.6 final storage hardening CI 45063263774 passed. Bounded worker attempt and telemetry freshness PASS; Storage Provider capability partial with two runner rows. PhysicalDisk instance status warming-up; real target per-disk rates/health not established.
- Alpha.7 thermal adapter commit 01a2f44c85fcb59d68fe5575d88c31149dd75b79, CI 45063709265 completed successfully: zero warnings/errors, seven thermal tests and runtime capability schema. Optional, fixed loopback GET to v0.9.6-shaped LHM provider, disabled default, no external code/driver bundled. String Celsius schema only, receipt time not actual sensor sampling age, no version handshake. Live Intel temperatures not verified.
- Device registry/API commit 5fd6cf8807647c01f6a8506ef3d9e76daded1e58, run 45063802814: build and fixtures passed, LAN/WS smoke passed, device lifecycle not yet confirmed, full CI in progress at checkpoint. Owner token restricted to local loopback; separate LAN reader grants, hashed in RAM, 24h expiry, 32 active grants, local owner create/list/revoke. WS checks access each send.
- Local owner UI and negative admin Origin/Host tests commit 9955376d504cd1b9a46f6f1e9af9711e32b7af58, run 45063875045: JS syntax passed; full CI in progress; device lifecycle not yet confirmed. Interactive browser acceptance pending.
- Last verified package run 45063709265: Desktop + Host https://github.com/iSentinel/VeyPanel/actions/runs/45063709265/artifacts/14770776736; standalone https://github.com/iSentinel/VeyPanel/actions/runs/45063709265/artifacts/14769899651. Unsigned alpha.

## Next
1. Confirm latest device CI and inspect actual revocation/Origin/Host logs; fix any failures. Test local owner dashboard in real browser and LAN reader on Lenovo.
2. Implement one-time short-lived QR enrollment with local generation and explicit owner approval; see docs/device-enrollment.md. Review encoder provenance/licensing and TLS trust design before bundling. Durable per-device grants and Android secure storage are separate.
3. Continue history, Android telemetry and physical Apollo/Lenovo Mirror/Extend 2000x1200 at 60 Hz; actual Intel Quick Sync and CPU/GPU sensors, SSD counters and rollback are not physically validated.
4. Keep topology mutation disabled until watchdog and hardware acceptance. No driver installation, live pairing, real streaming or monitor changes performed. Original source license still undecided.


Device API CI 45063802814 failed the first HTTP creation assertion, although build, registry fixtures, HTTPS LAN and WS smoke passed. Likely route-handler overload issue; explicitly select Delegate-returning IResult overload and report HTTP status/assertion label without secrets. Fix not yet verified; inspect subsequent CI. Do not ship device authorization as accepted until full lifecycle passes.

Alpha.8: repaired device lifecycle smoke in CI 45064059968 passed; final publish pending at initial check. Added in-memory two-minute, eight-invitation registry, single claim secret rotation, owner code confirmation and atomic one-time redemption. Public claim/finish require exact LAN HTTPS listener, origin or native no-Origin, bounded body/read and concurrency. Owner routes use existing local owner middleware. No QR or browser invitation UI yet. CI pending.

Alpha.8 browser increment: owner panel issue/cancel/approve by typed code, separate HTTPS enroll.html removes secret fragment and prompts explicit claim/check approval; no persistent secret storage. Added JS syntax and real HTTPS integration scenario including replay and local HTTP denial. CI pending. QR encoding and durable storage remain next.

Alpha.8 QR increment: local PNG QR generated from one-time invitation only, via exact NuGet Net.Codecrete.QrCodeGenerator 3.2.1, MIT notice packaged; high/critical NuGet audit warnings fail Host build. Owner issuance response includes PNG, UI clears it on expiry/clear/approve/cancel/pagehide. CI verifies PNG structure only; actual camera decoding and package audit output pending. Existing QR invite URL can be copied as fallback.
