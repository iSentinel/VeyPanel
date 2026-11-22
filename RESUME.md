# Resume checkpoint

2026-11-22 — VeyPanel 0.1.0-alpha.5.

## Verified evidence
- Alpha.4 GPU CI 45050942800 passed 6/6 synthetic and ABI tests, build/publish and all previous smoke. Runtime GPU status was warming-up; physical GPU capability not established.
- Alpha.5 WS transport commit 8e13f379b239d30cac3351e18b82cf98b64a435b passed CI 45062181527. First-frame token, exact browser Origin, bounded concurrent sessions, read-only stream, REST fallback.
- WSS/security increment efe6e98ff5650315e901ba737fb520446ba1757f passed CI 45062225593. Verified private-interface authenticated WSS, untrusted TLS rejection, foreign origin, wrong token, advancing samples, reconnect, query rejection and concurrent capacity.
- DXGI increment 5e37be98bbc0e792a003c6c5cc4f063d6f2ff359 passed CI 45062321592 with zero Host build warnings/errors, GPU 8/8, live DXGI inventory ok with two runner adapters. Runtime PDH GPU status warming-up; real engine-to-Intel-Arc mapping remains unverified.
- Storage diagnostic commit 476ef05f1a7e1956ca1e3da4ff7a4c2e98e5eb04: local read-only Windows Storage Provider probe and conversion/privacy fixtures. Fixture step passed in run 45062430196; remaining CI in progress at checkpoint. The actual provider probe was not executed on physical disks. No periodic sensor integration or independent SMART verification.
- Latest verified package run: 45062321592.
- Desktop + Host (unsigned): https://github.com/iSentinel/VeyPanel/actions/runs/45062321592/artifacts/14770545158
- Standalone Host (unsigned): https://github.com/iSentinel/VeyPanel/actions/runs/45062321592/artifacts/14769509854

## Next steps
1. Confirm final storage CI; implement bounded per-disk I/O sampling and separate asynchronous storage reliability collection with capability status, timeout and freshness.
2. Add CPU/GPU temperatures only from validated sensor providers (no inferred values). Design certificate enrollment, QR and per-device revocation before exposing administrative actions.
3. Target acceptance: install only verified Apollo and signed driver with operator permission; check real Lenovo WSS trust, WPF, pairing, Intel Arc engine observation during HEVC streaming, Mirror/Extend 2000x1200 at 60 Hz and safe recovery.
4. Continue Android client and installer. Keep topology writes disabled until watchdog/recovery design and physical acceptance.

Browser REST fallback is implemented but actual browser/Android behavior not yet verified. The one-token alpha model is not per-device enrollment. No driver installation, physical topology mutation or live pairing took place. Original license decision and upstream redistribution review remain open.

Alpha.6: storage fixture CI 45062430196 completed successfully. Implemented per-instance PhysicalDisk PDH wildcard read/write throughput and IOPS using existing bounded native array reader. Instance names are provider labels, not stable hardware IDs; no model correlation inferred. Capture and merge tests pending CI. Next: periodic Storage Provider worker and dashboard.

Alpha.6 storage worker: independent hosted service invokes bundled Windows PowerShell script every 60 seconds after completion, 20-second timeout, bounded output, validated schema and age, stale/missing N/A. No elevation or execution-policy bypass. Runtime provider availability remains hardware/policy-dependent. CI pending.

Alpha.6 worker hardening: explicit UTF-8 stdout, maximum 128 provider rows, bounded completion integration test and deterministic invalid-temperature fixture. First per-disk CI run 45063074951 succeeded. Latest worker CI pending.
