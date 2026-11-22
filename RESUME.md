# Resume checkpoint

2026-11-22 — VeyPanel 0.1.0-alpha.8.

## Verified
- Alpha.7 device API failed runs 45063802814 and 45063875045. Fixed explicit Delegate route registration in beb2d89d6c23689deeae9e2f60f89d3f877ede3f. Full run 45064059968 PASS: create HTTP 201, foreign Origin/Host denied, no token list exposure, reader cannot administer, active WebSocket revocation and REST 401.
- Alpha.8 invitation protocol 9cb4e027ff9a06dd65116bb71ca19d7d9a1e35dc: run 45064325652 PASS. Two-minute invitations, capacity eight, 256-bit secret rotated on first claim, explicit owner code comparison, atomic one-time redemption, expiry/cancel/replay/parallel fixtures.
- Browser owner/reader enrollment pages 0b88c721b57365c4d5533e03fff6b9b0c7c0e76e: run 45064400938 PASS. Real private NIC HTTPS integration tested invite creation, origin-bound URL, packaged page, HTTP denial, claim, no grant before approval, wrong code, approval, replay rejection, authorized telemetry and admin denial. Actual browser interaction pending.
- Local QR b3c46e43573342d5674c9900f2338783e482b829: run 45064630788 full PASS; zero build warnings/errors, generated PNG structure check, HTTPS enrollment and all previous smoke. Pinned Net.Codecrete.QrCodeGenerator 3.2.1 MIT license packaged, no remote QR service. Independent QR decoding/camera acceptance not yet done.
- Grant codec c7772049e9de2372e17f77e355f1848d837249d6: run 45064798561 in progress at checkpoint. Strict bounded serialization only; no persistence/live registry integration.
- Latest verified artifact run 45064630788: Desktop + Host https://github.com/iSentinel/VeyPanel/actions/runs/45064630788/artifacts/14770619245; standalone https://github.com/iSentinel/VeyPanel/actions/runs/45064630788/artifacts/14771210147. Unsigned alpha.

## Next
1. Verify grant codec CI and inspect logs. Implement opt-in Windows-protected durable grant store with fixed per-user path, exclusive process lock, atomic write and fail-closed policy on corruption, permission errors and failed revocation. Test restart, crash and reparse/rollback handling before enabling live persistence.
2. Continue history and Android client (secure credential storage, TLS trust, receiver UI). Actual QR scanner and browser behavior on Lenovo must be verified; LAN HTTPS currently requires standalone Host configuration with trusted cert. GUI managed Host remains loopback-only.
3. Physical acceptance: Lenovo TB-J607Z, Intel Arc, CPU/GPU thermal provider and actual SSD counters, Apollo v0.4.6 pairing/Quick Sync, Mirror/Extend 2000x1200 at 60 Hz; rollback watchdog before topology writes.
4. No actual driver installation, monitor changes, live pairing or physical streaming performed. Original source license remains undecided; third-party QR license separately bundled.


Alpha.9: previous grant codec CI 45064798561 PASS. Added Windows-only CurrentUser DPAPI protected storage primitive with fixed default profile path, restrictive ACL, reparse checks, exclusive file lock, bounded ciphertext and flushed same-directory replacement with pending transaction marker. Tested by isolated reopen, lock, revoke-empty, corruption and pending marker fixtures (CI pending). Not yet wired to live grants. No guarantee against same-account/admin tampering, old valid ciphertext rollback or power-loss filesystem metadata failure.

Alpha.9 runtime integration: standalone VEYPANEL_PERSIST_GRANTS=1 opens protected user store, restores unexpired reader hashes only, serializes issuance and revocation before success, disables all active readers on save failure and returns 503, adds local storage status and revoke-all. Managed mode remains ephemeral. No initial auto-grant in protected LAN mode. Isolated registry reopen and failure injection fixtures; process restart/hardware crash acceptance pending. Failed transaction before marker creation may leave previous disk state; no success reported. Do not automatically restart or restore backups after storage failure.

First DPAPI CI 45065935377 compiled cleanly and passed empty/lock/ciphertext/reopen/empty replacement/corrupt data. Interrupted transaction correctly threw InvalidDataException but fixture did not catch that expected exception. Fixed fixture and Host startup catch. Added isolated published Host smoke (explicit Windows runner, refuses existing store), kill/restart after acknowledged issue/revoke and dirty-marker startup exit 1. No crash during actual disk write or abrupt power-loss test. CI pending.

Alpha.9 history: compact 900-sample/900-second RAM ring, UTC gap/reset semantics, authorization and revocation tests, REST history endpoint and explicit browser refresh chart. No persistent history or export yet. CI pending. Fixed process test cleanup for unexpected startup hang.
