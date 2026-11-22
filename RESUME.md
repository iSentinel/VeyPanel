# Resume checkpoint

2026-11-22 — VeyPanel 0.1.0-alpha.6.

## Verified
- Alpha.5 complete storage diagnostic CI 45062430196 passed. WS/WSS, DXGI and previous test evidence remains valid.
- Per-instance disk IO commit acbdc6c777fb5610eaa4bb5d68d227ca4ead8b38 passed CI 45063074951: zero Host warnings/errors, bounded merge, duplicate/missing values and runtime schema. Hosted capability was warming-up; physical per-instance rates not established.
- Asynchronous storage worker commit 7020a3d4431fe31535bf49ca8b144e3d09c6e95b passed full CI 45063224882. Storage scripts packaged, validation and stale handling tested, dashboard integrated. Provider reports are not independent SMART/NVMe verdicts.
- Hardening commit 81c2b97253c98df9497507443969ce4bd98e6c75: UTF-8 output, max 128 rows, runtime bounded attempt and telemetry freshness check. Published-host integration smoke passed; remaining CI in progress in run 45063263774. Complete log not yet available at initial check; do not infer actual counter values.
- Verified package run 45063224882: Desktop + Host https://github.com/iSentinel/VeyPanel/actions/runs/45063224882/artifacts/14770501184; standalone https://github.com/iSentinel/VeyPanel/actions/runs/45063224882/artifacts/14770421339. Unsigned alpha.
- Reviewed thermal provider v0.9.6 vs master contract; see docs/thermal-provider.md. No thermal adapter implemented.

## Next
1. Confirm full hardening CI/logs and actual provider status on runner; add tests that observe a second valid PhysicalDisk sample when available. Keep unavailable and warm-up explicit.
2. Implement CPU/GPU thermal provider after dependency/security review, no automatic driver install or service exposure. Test sensor types and units, timeouts and stale readings.
3. Implement secure device enrollment, scoped revocable tokens, QR, history and Android telemetry client.
4. Physical acceptance: Lenovo TB-J607Z WSS, Intel Arc/Quick Sync, actual storage/thermal sensors, Apollo v0.4.6 pairing and Mirror/Extend at 2000x1200 60 Hz. Keep display writes disabled until recovery watchdog is ready and hardware-tested.

No actual target hardware access, driver installation, display topology changes, live pairing or streaming performed. Browser behavior remains unverified on target. Original source license remains an owner decision.
