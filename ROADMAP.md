# Roadmap

- [x] Select product name, target hardware and architecture.
- [x] Write alpha CPU/RAM sampler and local browser dashboard.
- [x] Add source-level CPU arithmetic tests and Windows CI definition.
- [x] Compile on Windows CI; execute tests; validate real counters and unauthorized API responses ([run 45045388584](https://github.com/iSentinel/VeyPanel/actions/runs/45045388584)).
- [x] Implement automated HTTPS LAN integration smoke, RFC1918 listener policy and invalid TLS/token rejection ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45047071449)).
- [ ] Validate HTTPS LAN dashboard on Lenovo (certificate trust, stale samples, reconnect).
- [x] Apollo source baseline review (v0.4.6), API contract, official asset digest and read-only preflight source ([PoC plan](docs/apollo-poc.md)); preflight not executed on target.
- [x] Implement local-only Apollo inventory CLI and certificate pinning; mock tests [CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45046872073), live compatibility pending.
- [ ] Apollo PoC: verify actual installer/publisher/driver catalog, TLS and API on host, Quick Sync; test mirror and extended desktop.
- [x] Implement read-only Windows desktop-source inventory and JSON diagnostic baseline ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45046953751); physical validation pending).
- [x] Implement read-only CCD active-path/mode capture with virtual-mode indices, structural validation and recovery design ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45049611656); hosted capture partial).
- [x] Add CCD target names/device paths and conservative same-session identity eligibility checks ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45049672009)).
- [x] Implement explicit local PIN pairing CLI and five additional mock tests ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45049726317); live pairing pending).
- [x] Implement native validate-only current CCD topology CLI, stable snapshot guard and fixed non-apply flags ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45049793209); native target validation pending).
- [x] Implement initial WPF display diagnostics and tray shell; separate CI artifact ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45049892455); interactive acceptance pending).
- [x] Implement bundled Windows desktop/Host lifecycle, local dashboard controls and managed child tests ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45050593038)).
- [x] Add local Apollo inventory and operator-confirmed PIN pairing in WPF ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45050643363); physical acceptance pending).
- [ ] 0.2: integrate streaming controls in WPF; hardware-tested rollback and live PIN acceptance.
- [x] Add per-interface network throughput and fixed-volume capacity telemetry/UI ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45050707013)).
- [x] Implement system-total Windows PDH disk throughput and IOPS with status validation ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45050803404)).
- [x] Implement experimental per-engine GPU/Video Encode/Decode utilization with mock aggregation and runtime capability schema ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45050942800); physical GPU pending).
- [x] Implement authenticated WebSocket telemetry, bounded sessions, origin checks, browser reconnect and REST fallback ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45062225593)); loopback/HTTPS WSS and capacity tests passed.
- [x] Add DXGI named adapter inventory and LUID-based GPU engine matching with N/A for unmatched metrics ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45062321592)).
- [x] Add local-only Windows Storage Provider reliability diagnostic and conversion/privacy fixtures ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45062430196); actual counters pending).
- [x] Add PhysicalDisk wildcard per-instance throughput/IOPS with bounded merge and dashboard ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45063074951)).
- [x] Integrate independent bounded Storage Provider worker and health dashboard ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45063224882); actual physical counters pending).
- [x] Harden storage provider encoding and bounded completion test ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45063263774)).
- [x] Review LibreHardwareMonitor v0.9.6 thermal sensor contract and security boundaries ([design](docs/thermal-provider.md)); version-specific adapter now implemented below.
- [x] Implement opt-in loopback-only LHM v0.9.6-shaped read adapter, explicit Celsius parsing and thermal dashboard ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45063709265); real provider validation pending).
- [ ] 0.3: validate real GPU/encoder, physical-disk I/O/SMART, network acceptance; CPU/GPU temperature sensors, physical WSS acceptance.
- [x] Implement ephemeral individually revocable read-only device tokens, local owner API and active WS revalidation ([fixed CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45064059968)).
- [x] Implement local owner dashboard issuance/list/revoke UI ([fixed CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45064059968); interactive browser acceptance pending).
- [x] Document one-time QR invitation and durable grant trust model ([design](docs/device-enrollment.md)); no implementation yet.
- [x] Implement two-minute invitation claim, explicit owner verification and atomic one-time reader redemption ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45064325652)).
- [x] Add local invitation owner UI, tablet claim/finish page and real HTTPS enrollment integration test ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45064400938); browser acceptance pending).
- [x] Implement local QR PNG rendering using pinned MIT encoder and package license ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45064630788); independent scan acceptance pending).
- [x] Add bounded strict future grant-store codec and corruption/expiry/privacy fixtures ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45064798561); not wired to runtime).
- [x] Implement Windows DPAPI CurrentUser grant-store primitive, strict directory ACL, exclusive lock and interrupted transaction refusal ([fixed CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45066141473)).
- [x] Wire opt-in standalone DPAPI registry, persistent revoke/revoke-all and failure disabling; reopen and failure fixtures ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45066141473)).
- [x] Add isolated published Host process-restart/revocation/dirty-marker startup integration smoke ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45066141473)).
- [x] Implement bounded 15-minute in-memory history endpoint and historical CPU/RAM/GPU chart ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45066230888); UI acceptance pending).
- [x] Reject unexpected file ACLs and test directory/file ACL tampering and reparse path refusal ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45066313328); symlink fixture capability-dependent).
- [x] Extend history charts with codec/disk and time range, authenticated CSV export ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45067318280); browser acceptance pending).
- [ ] 0.4: physical crash/power-loss acceptance.
- [x] Add initial native Android Monitor-only Java app, strict LAN/TLS policy, REST polling, JVM fixtures and APK CI ([corrected Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45067558759); real device acceptance pending).
- [x] Add native pasted two-step invitation flow and strict enrollment-origin JVM fixtures ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45067632914); live native protocol/device test pending).
- [x] Document Android opt-in credential persistence and QR acceptance gates ([design](docs/android-credential-design.md)).
- [x] Implement opt-in AndroidKeyStore AES-GCM credential store, reconnect saved access and forget UI ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45078027152); actual AndroidKeyStore instrumentation pending).
- [x] Add ordered credential operation callbacks and isolated AndroidKeyStore instrumentation APK ([build CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45078101699); execution pending).
- [x] Add native offline QR invitation scanner, strict parsing with explicit Connect, pinned ZXing dependencies and notices ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45078196387); camera/device acceptance pending).
- [x] Add isolated emulator runtime CI for AndroidKeyStore and synthetic offline QR decode ([instrumentation PASS, shell result gate FAIL](https://github.com/iSentinel/VeyPanel/actions/runs/45078273557); raw-output fix builds; reruns blocked by missing KVM; software fallback added; no camera test).
- [x] Implement native WSS-first monitor, one latest-sample slot, HTTPS REST fallback and bounded retry; fixed URI fixture ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45081890582); live transport pending).
- [x] Add mandatory raw instrumentation reporting and software-emulation fallback when KVM is unavailable ([all instrumentation assertions PASS, shell syntax FAIL](https://github.com/iSentinel/VeyPanel/actions/runs/45082028995); script rewritten and syntax gate added).
- [x] Preserve existing saved access on invalid link and unrelated authorization denial; replace only after successful authorized sample ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45083538812); Activity acceptance pending).
- [x] Add isolated actual native HTTPS/WSS transport fixture with ephemeral IP-SAN TLS, denial and manual REST-after-close checks ([corrected runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45090572041); not Windows Host or Activity end-to-end).
- [x] Confirm actual Android Keystore, synthetic QR and extended telemetry instrumentation with strict final result gate ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45083538875)).
- [ ] 0.5: Android QR camera acceptance, native WSS transport acceptance and native video.
- [x] Verify original 64x64 two-frame AVC via Android MediaCodec in emulator ([Android Build PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45154163226), [runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45154152887); PR #8 merged as c97d3d8). Physical hardware decode acceptance pending.
- [ ] Add read-only Android AVC/HEVC/AV1 decoder capability inventory; CI and physical tablet evidence pending (survey is not decoding acceptance).
- [x] Implement adaptive 1/2/3-column native monitor, collapsible controls, memory/IOPS, network/volumes and age-gated thermal/storage health details ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45081976468); visual tablet acceptance pending).
- [ ] 0.6: Display / Monitor / Hybrid modes; touchscreen coordinates and orientation.
- [x] Add Android foreground observed history (900 points / 15 minutes), CPU/RAM/GPU, codec and disk charts with 1/5/15-minute selection ([build/lint PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45083916217); [history instrumentation PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45083699289); UI acceptance pending).
- [x] Integrate explicit Android Host history refresh, bounded UTC merge, authorization and revocation fixtures ([build PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45090687195), [runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45090682478), PR #1 merged; Activity and actual Host acceptance pending).
- [x] Add local foreground connection diagnostics and disconnected Activity UI smoke ([build PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45091283003), [runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45091277957); PR #2 merged; physical lifecycle acceptance pending).
- [ ] 0.7: overlay, alerts, Host history synchronization and diagnostics.
- [x] Limit Host outbound WSS messages to 1 MiB and prototype bounded Android frame/message decoding ([Windows PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45092513666), [JVM PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45092513667), [runtime regression PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45092508834); PR #3 merged; Android production client still uses OkHttp).
- [x] Prototype bounded WSS upgrade and isolated TLS transport ([JVM PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45093130783), [runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45093126068); PR #4 merged; production transport unchanged).
- [x] Validate bounded WSS control frames, consecutive samples, malformed close and blocked read cancellation ([Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45096636484), [runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45096631311); PR #5 merged as f2b6e7e, isolated TLS only).
- [ ] 0.8: reconnection, sleep/wake and USB network transport.
- [x] Introduce shared Android cancellable telemetry-feed interface, retaining OkHttp default ([Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45153409806), [runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45153400342); PR #9 merged). Bounded production switch remains unaccepted.
- [ ] 0.9: installer, signing, reproducible release, upgrade/uninstall acceptance.
- [ ] 1.0: physical device acceptance and stable release.
- [x] Add isolated cancellable Android bounded WSS stream with platform TLS and pre-read limits; validate against synthetic valid, malformed, stalled and revoked flows ([Android Build PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45150815811), [runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45150808675); PR #6 merged as deb7982). Not selected in production MainActivity.
- [x] Add read-only Android AVC/HEVC/AV1 decoder inventory and guarded local UI ([Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45151764750), [emulator runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45151759925); PR #7 merged as 65338d8). Declared capabilities do not establish hardware decoding.

- [x] Android alpha.16 owner-accessible AVC decoder self-test using original bundled clip, decoder classification and two-run emulator / Activity UI acceptance ([Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45328031303), [runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45328022894); PR #10 merged). Physical Lenovo and sustained decode still pending.
- [x] Pure normalized touch mapping on Windows and Android (letterbox, rotation, negative origins, fail-closed bounds), [Windows CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45328777756), [Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45328777846), [runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45328771479); PR #11 merged. No input forwarding or hardware acceptance.

- [x] Add session/target-identity/freshness gate before any future touch injection ([Windows CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45329353667), PR #12 merged). No real input forwarded.

- [x] Android Surface-output AVC instrumentation with original local clip and frame-available callback ([Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45329953560), [runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45329948361); PR #13 merged as 6034990). Actual tablet display/hardware acceptance pending.

- [x] Android alpha.17 on-device TextureView AVC preview from original local clip, gated on actual decoded output and TextureView callback ([Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45331269259), [runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45331261314); PR #14 merged). Physical Lenovo and Windows streaming acceptance pending.

- [x] Android alpha.18 local AVC preview touch diagnostics (single pointer, fail-closed, no network/injection) ([Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45331898798), [runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45331893810); PR #15 merged). Physical Lenovo touch acceptance still pending.

- [x] 0.9: Verify Android debug APK ZIP/CRC/SHA256 and APK signature with artifact reports ([Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45332888028), [Windows CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45332888086), PR #16 merged). Debug signing is not production release signing.

- [x] 0.9: Verify compiled APK ID/version/min/target SDK and exactly CAMERA+INTERNET permissions ([Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45333601381), [Windows CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45333601475), PR #17 merged). Production signing, reproducible releases and physical acceptance pending.

- [x] 0.9: Verify bundled ZXing/OkHttp license and notice assets survive Android APK publication ([Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45334220672), [Windows CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45334220748); PR #18 merged). Full transitive SBOM/license audit remains open.

- [x] 0.9: Publish resolved Android debug runtime (10 Maven modules) and Windows Host win-x64 NuGet (2 packages) CycloneDX component inventories ([Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45363577089), [Windows CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45363577252), [runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45363566687); PR #19 merged). Full dependency graph, runtime packs, licenses and native locks remain open.

- [x] 0.9: Enforce post-resolution component version/membership baselines in Android and Windows CI ([Android PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45364210959), [Windows PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45364210957); PR #20 merged). Native lockfiles and package hashes remain open.

- [x] 0.9: Enforce Gradle debug runtime native lock and capture actual NuGet win-x64 native lock ([Android CI](https://github.com/iSentinel/VeyPanel/actions/runs/45364765561), [Windows CI](https://github.com/iSentinel/VeyPanel/actions/runs/45364765530), [runtime](https://github.com/iSentinel/VeyPanel/actions/runs/45364754109) PASS; PR #21 merged). NuGet enforcement remains pending.

- [x] 0.9: Enforce native NuGet locked mode for Windows Host with SDK-generated win-x64 lock and package SHA-512 hashes ([Windows CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45370338307), [second CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45370350526); PR #22 merged). SDK/runtime packs and Desktop scope remain open.

- [x] 0.9: Enforce Gradle SHA-256 verification for 395 observed artifact records, reject deliberate incorrect ZXing checksum ([Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45371001724), [Windows CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45371001725), [runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45371079169); PR #23 merged). Upstream provenance review remains open.

- [x] 0.9: Pin observed .NET SDK 10.0.404, JDK 17.0.21+9, Gradle 8.9 and Windows Python 3.12.10; publish actual toolchain evidence ([Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45371848490), [Windows CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45371848232), [runtime PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45371834290); PR #24 merged). SDK image/runtime-pack reproducibility remains separate.


- [x] 0.9: Capture literal license declarations and LICENSE/NOTICE hashes from verified Android/Host runtime packages ([Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45377626137), [Windows CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45377626247); PR #25 merged). Supplemental Maven POM evidence recorded; full redistribution review remains open.

- [x] 0.9: Publish scoped OSV advisory snapshots for reviewed Android/Host runtime coordinates ([OSV CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45378191048), [Android PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45378182940), [Windows PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45378191025); PR #26 merged). Initial 12-package snapshot returned zero matches; full security audit remains open.

- [x] 0.9: Publish and verify exact SHA-256 file manifests for Android, Host and Desktop artifacts ([Android CI](https://github.com/iSentinel/VeyPanel/actions/runs/45378711150), [Windows CI](https://github.com/iSentinel/VeyPanel/actions/runs/45378711008) PASS; PR #27 merged). Downloaded artifacts verified independently: 8/360/834 files. Exact-checkout reproducibility remains pending.

- [x] 0.9: Verify Android exact-checkout reproduction on two independent CI runners ([runtime reproduction PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45403501445); PR #28 merged); both v2 signatures verify, bytes outside signing block identical. Full signed APK equality remains open.

- [x] 0.9: Run independent Windows exact-checkout Host reproduction ([comparison PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45404314553); PR #29 merged). Raw 356/357 identical; normalized 357/357 identical; both Host smoke tests PASS. Normal publication unchanged.

- [x] 0.9: Record and revalidate actual clean tracked Git checkout commit/tree/epoch in ordinary Android, Host and Desktop artifacts ([Android CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45404957532), [Windows CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45404957357); PR #30 merged). Downloaded all three artifact manifests verified; signed attestation remains open.

- [x] 0.9: Adopt verified deterministic Host CI publication settings (ContinuousIntegrationBuild and source-epoch endpoint normalization); both Windows CI runs 45411446910/45411465466 PASS, PR #31 merged. Raw/normalized evidence independently verified. Local publish and signed release reproducibility remain separate.

- [x] 0.9: Run independent same-checkout Desktop bundle reproduction ([CI PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45412111245), PR #32 merged). All 832 experimental bundle files identical; both Host smoke tests PASS. Interactive Desktop acceptance separate.

- [x] 0.9: Publish unsigned portable Windows ZIP, verify Windows extraction and compare exact independent archive SHA-256 ([reproduction PASS](https://github.com/iSentinel/VeyPanel/actions/runs/45412991876), PR #33 merged). Actual downloaded ordinary ZIP verifies 836 files. Installation and signing separate.

- [x] 0.9: Require trusted external SHA-256 and verified nested Host/source identity before dry-run or isolated package staging; both Windows CI 45426452023/45426432998 PASS, PR #34 merged. Real Windows package staging verified 836 files. Activation, upgrade/rollback and uninstall separate.

- [x] 0.9: Verify side-by-side package selection, idempotence, atomic state replacement, interrupted-write refusal and verified rollback. PR #35 merged; Windows CI 45428020239/45427999735 PASS. Activation/launcher and uninstall remain separate.

- [x] 0.9: Correct fail-closed CI report pipelines, require exact CAMERA/INTERNET declarations and reject ambiguous APK entry names. PR #36 merged; all 14 CI jobs PASS, including negative gate outcome assertions and fresh reproduction experiments.

## Engineering policy adoption and compliance migration (2026-11-25)

Canonical policy: [engineering standards](docs/engineering-standards.md).
Gap register: [adoption audit](docs/engineering-adoption-audit.md).
Priorities P0 safety/verification, P1 engineering migration. Do not confuse
scoped local acceptance with full policy compliance.

- [x] ENG-01/02/07/11: Adopt policy, exact Python debt baseline and common Python QA/JUnit. PR #38 merged, 10 CI jobs PASS; downloaded Windows/Android reports confirm 125/125, 429 debt entries, no new/stale identities. Native JUnit adapters and wider compliance remain open.
- [ ] ENG-02: Reduce remaining exact Python debt by focused modules; no new or stale baseline findings. Broader PEP 8 and static type analysis separate.
- [ ] ENG-03: Native C#/Java/JS/PowerShell quality audit and equivalent reviewed debt gates; preserve compiler/lint/runtime checks.
- [ ] ENG-04 (P0): Audit logging/privacy and add closed structured event schema, stdout/stderr and secret-canary regressions.
- [ ] ENG-08/09 (P0): Harden manifest inventory, bounded reads, mutation detection, archive validation and trusted source verification; audit transport cancellation and trust boundaries.
- [ ] ENG-10/05 (P0): Verify launcher PR #37 under adopted gates; inspect recovery branch, explicit reconciliation, process fencing, safe uninstall/backup/restore and installed readiness; no destructive automation.
- [ ] ENG-06: Browser/WPF/Android lifecycle, accessibility and rendered layout tests; physical acceptance only with actual approved devices.
- [ ] ENG-07/11: Expand stable catalog and native JUnit/summary adapters, shared QA prerequisites, doc validation, exact reviewed action SHA pins and CI import; GitLab/TeamCity qualification separate.
- [ ] ENG-12: Review-only upstream inventory/watch, full build/runtime pack pinning, license redistribution and advisory disposition.
- [ ] ENG-14: Validate canonical documentation hierarchy; local Confluence manifest if applicable; external publishing disabled.
- [ ] ENG-13: Candidate-bound release governance, production signing and attestation, actual hardware and update/rollback qualification; separate owner approval.
- [x] ENG-15: Main Android runtime run 45509804749 initial attempt blocked by Maven Central HTTP 429 before instrumentation; one rerun completed PASS. Preserve failed attempt; no dependency or TLS bypass.

- [x] ENG-08/02: Fail closed on unreadable artifact subtrees, bound file/directory and manifest reads, detect observed same-size changes, require exact schema and atomically replace staging manifests. Six new regressions; 34 exact debt identities removed (429 -> 395). Actual prior artifacts verified; PR #39 merged, all ten CI jobs PASS. Trusted quiescent tree assumption remains.

- [x] ENG-08: Resolve PR #39 Windows cross-API stat regression without dropping mutation detection. Exact source reviewed, two new regression fixtures PASS locally; Windows and reproduction CI PASS, PR #39 merged.

- [x] ENG-04: Add optional closed-schema QA JSONL events, bounded monotonic durations, safe reason codes, stdout/stderr separation and canary/exit regressions; PR #40 merged, all four CI jobs PASS. Audit Host token capture and legacy CLI exception messages next; no general redaction claim.

- [x] ENG-04: Remove raw Host smoke temporary logs; owned pipes, exact bootstrap, bounded cleanup, fixed diagnostics. PR #41 merged; all nine combined-source CI jobs PASS, including PowerShell capture and published Host smoke.

- [x] ENG-10/05: Verify Launcher PR #37 with current main including private Host capture and safe QA events; all three exact-source CI jobs PASS, merged 2262808. WPF readiness remains open.

- [x] ENG-04: Integrate reviewed PR #42 framework request privacy with Launcher and require combined native Windows and reproduction CI.
- [x] ENG-09: Integrate reviewed PR #43 bounded WSS lifecycle with PR #44 local preview tap gating; require both JVM fixtures, actual Android emulator and APK reproduction on combined source. Production OkHttp unchanged.
- [x] ENG-10/05: Integrate read-only Recovery candidate 8f456da with Launcher; require real package inspection and manual-review exit/unchanged state in Windows CI. Explicit recovery, process fencing and uninstall remain separate.
- [x] ENG-06: Fence SurfaceTexture destruction versus active codec ownership; prevent stale generation callbacks, test repeated preview and lifecycle cancellation.

- [x] Combined PR #45 merged 5bb5505: all fourteen CI jobs PASS, independently downloaded Windows report 162/162, exact debt 395. Scope does not establish physical acceptance or release readiness.

- [x] ENG-06: Fresh per-preview TextureView target and exclusive worker/framework texture lease; JVM ordered interleaving and repeated Activity preview regressions. PR #46 merged; all eight CI jobs PASS. No remote video/input change.

- [x] ENG-09: Atomically publish the latest production WSS sample, bound its local age, preserve terminal cause and wake cancelled reader. Native JVM, actual TLS instrumentation and APK reproduction mandatory.
- [ ] ENG-09/12: Resolve OkHttp 4.12.1 source-to-binary provenance and pre-allocation memory bound; candidate source reviewed, repository redirect and unsigned tag unresolved. Strict CRLF in experimental upgrade with four negative fixtures. No dependency update or production transport switch.
- [x] ENG-10/05: Explicit plan-bound first-install metadata recovery. Sole staged version, trusted original ZIP, absent selection state, refuse existing locks/temp/extra versions, state readback. Twelve new local tests and isolated real 836-file package PASS; native Windows CI required. Existing corrupt state, process coordination and uninstall remain open.

- [x] PR #47 merged 37a07f5; all eight jobs PASS, actual Windows 174/174, exact debt 395. Experimental strict CRLF accepted; OkHttp provenance and pre-allocation bound remain open.

- [x] ENG-08/10/02: Bound selection state reads, reject duplicate/nonstandard JSON, hash and parse the same manifest bytes, validate state before writing and use safe CLI failure categories. Six new regressions, 66 exact debt identities removed (395 -> 329); real existing roots and prior artifacts verified locally. Windows CI required; quiescent private root assumption remains.

- [x] PR #48 merged: strict bounded selection metadata and one manifest snapshot; ten CI jobs PASS, independently downloaded Windows QA 180/180, exact debt 329.

- [ ] ENG-09/12: Capture exact pinned OkHttp JAR and class hashes with static javap evidence in Android CI; no production transport change.

- [x] PR #49 merged 21ae081, four CI jobs PASS, downloaded Windows QA 187/187 and manifest-verified javap. Actual bytecode confirms readFully and optional inflation before application callback. Provenance and pre-allocation limit mitigation remain open.

- [x] ENG-10/05: Constrained corrupt selection reconciliation: one verified version, bounded malformed metadata, plan binds original bytes, exclusive verified backup before atomic replacement, retain backup/manual review. Twelve local fixtures and actual isolated 836-file package PASS; Windows CI required. Process fencing, backup retention and multi-version reconciliation separate.

- [x] PR #50 merged 788d7a6; both Windows jobs PASS, actual 199/199 common QA, retained-backup recovery step PASS. Multi-version reconciliation and process fencing remain open.

- [x] ENG-09: Qualify trusted wrong-IP SAN denial across HTTPS REST, OkHttp WSS and bounded WSS; preserve positive/unknown-CA runtime gates, require TLS-classified failure and no parsed HTTP request. Certificate and observer controls PASS locally; Android emulator required. User-installed CA and Activity fallback acceptance separate.

- [x] PR #51 merged 73d97b6; eight CI jobs PASS, actual wrong-SAN denial across three Android transports and no parsed HTTP request confirmed. Physical owner CA acceptance remains open.

- [x] ENG-09: Share bounded TLS failure classification across WSS construction/read, REST polling and Host history. Wrapped recognized TLS errors terminal, existing network retry/fallback preserved; JVM fixture and native Android checks required. End-to-end Activity fallback acceptance and owner-installed CA remain open.

- [x] ENG-07/08: Require independent exact Python case registry, fail closed on discovery omissions/duplicates/extra IDs and all non-PASS mandatory outcomes. Initial 199 reviewed Windows IDs plus eight explicit fixtures; actual Windows/Android common QA required. Native report adapters and isolation separate.

- [x] PR #52 merged 35bfe9c; eight CI jobs PASS, actual Windows/Android 207/207 with exact required identities and unchanged debt 329. Activity terminal TLS and independent report verification remain next candidates.

- [x] ENG-07/08: Independently verify common QA JSON/JUnit against required case identities, exact debt and tested Git checkout; manifest successful evidence before CI upload. Eight explicit negative/positive fixtures added (215 required). Native CI required; native report adapters and authenticity separate.

- [x] ENG-09: Isolated actual Activity terminal TLS regression using production trust and synthetic loopback session; require one attempt, zero fallback/retry/samples, cleared active session and disabled history; negative server observer retained. Native emulator required; concurrent history and owner-installed CA separate.

- [x] PR #53 merged f473688; eight CI jobs PASS, actual Windows/Android 215/215 with manifest and independent verification. Runtime confirms terminal Activity TLS, no fallback/retry and no negative fixture HTTP request.

- [x] ENG-09: Qualify both ordered history/telemetry terminal callback interleavings on actual Activity, including pending future cancellation, feed close, generation invalidation, history clear and same-access subsequent session fencing. Synthetic callbacks only; actual emulator CI required. Live concurrent network cancellation remains separate.

- [x] ENG-04/08: Prevent subtest parameter and unreviewed identity export in QA JUnit; attribute to admitted parent, preserve nonpassing priority, count unattributed fixture outcomes and fail closed. Four regressions (219 required); native common QA pending.

- [x] PR #54 merged 542eb08; eight jobs PASS, actual Windows and Android 219/219, manifest and independent verification PASS, zero unattributed outcomes. Ordered Activity callback fencing verified; live network cancellation remains separate.

- [x] ENG-10/05: Explicit verified Desktop executable in native process creation; bound the second installed manifest read and reject growth after tree verification. Eleven Launcher fixtures and actual package dry-run PASS locally; full common QA and native Windows CI required. Lifetime fencing remains separate.

- [x] ENG-10/05: Conservative read-only Windows fixed-image process observation, safe count-only result and explicit blocked/unavailable exit codes; native fixtures and actual owned Host before/after cleanup CI. No process ownership or maintenance authorization claim. Lifetime fencing and Uninstall remain open.

- [x] PR #56 merged e4fb31f; ten CI jobs PASS, native Windows process observation and verified 220/220 common QA. Observation is not lifetime fencing.

- [x] ENG-09: Bound REST body reads before/after every read and EOF, enforce remaining byte budget and interrupt checks; JVM deterministic fixtures and isolated TLS drip-body runtime required. Whole-request absolute deadline and active socket cancellation remain open.

- [x] PR #55 merged 5534f42, exact integrated head 9b89fa8 seven automatic jobs plus manually dispatched Runtime 45546707362 PASS. Actual REST drip deadline and prior runtime gates verified.

- [x] ENG-10/05: Cooperative Desktop session-local admission before WPF window construction; retain UI-thread mutex until exit, refuse competing participating instance. Native contention/foreign-release fixture required. Cross-process, interactive WPF, crash/Host and maintenance fencing remain open.

- [x] ENG-10/05: Extend cooperative Desktop admission native fixture to separate owned smoke processes, release and abandoned-owner reacquisition, with bounded fixture cleanup and unique test names. No WPF or Host activation; native CI required.

- [x] PR #57 merged b6b772d; seven integrated CI jobs PASS, verified Windows 220/220 and native mutex thread/process/abandonment checks. Actual WPF and maintenance exclusion remain open.

- [x] ENG-10/05: Distinguish ready Host from owned process requiring cleanup; refuse Start/dashboard in uncertain cleanup state, keep Stop available, finalize Dispose only after successful cleanup. Extend owned real Host lifecycle smoke with simulated token loss and explicit Stop. Native CI required; actual OS stop failure and WPF acceptance separate.

- [x] ENG-10/05: Qualify actual managed Host graceful exit after isolated owning smoke process exits without Dispose, using private fixture handshake, retained observed handle and bounded waits. No termination by observed PID; subsequent read-only process observation required. Native Windows CI only; general crash and maintenance qualification separate.

- [x] PR #58 merged 1d6e454; seven integrated CI jobs PASS, verified Windows 220/220 and actual owned Host cleanup/owner-exit markers. Actual WPF and exclusive maintenance remain open.

- [x] ENG-10/05: Read-only maintenance inventory plan for exact active/previous archive set and staged trees, reject unknown roots/orphans/locks/tampering; bind original metadata bytes and root identity. Nine local regressions and real single-version 838-file unchanged PASS. Older two-version fixture correctly refused mismatched previous ZIP. Native Windows CI required. No maintenance admission or removal.

- [x] PR #59 merged 81d65ed; three integrated jobs PASS, verified Windows 229/229 and actual recovered package inventory. No maintenance admission.

- [x] ENG-10/05: Explicit plan-bound package-source backup to fresh private destination, exact selection bytes, original pinned ZIPs, bounded exclusive streaming, source recheck and independent receipt binding/manifest verification. Seven new regressions (236 required), real isolated 291091352-byte ZIP backup PASS, source 838 files unchanged. Native Windows CI required; restore, runtime user-data backup and maintenance exclusion separate.

- [x] PR #60 merged 1c5b8e3; three integrated jobs PASS, verified Windows 236/236 and actual isolated backup. No user-data backup or physical durability guarantee.

- [x] ENG-10/05: Restore verified package-source backup into nonexistent private destination with explicit destination-bound plan, stage all pinned versions, preserve exact selection bytes and verify final inventory; seven new regressions (243 required), actual 838-file single-version restore and Launcher dry-run PASS. Native Windows CI required. No activation, overwrite, deletion or exclusive maintenance.

- [x] PR #61 merged d73d5f0; three integrated jobs PASS, verified Windows 243/243 and actual isolated restore. No activation or replacement.

- [x] ENG-10/05: Smoke-only cooperative Windows maintenance sharing lease: multiple runtime read handles versus exclusive maintenance handle, exact sharing-violation busy classification, missing/unsafe path refusal, cross-process contention/release/owner-exit regression. Native CI required. Production file provisioning/ACL/identity, Desktop/Host/Launcher integration and exclusive mutation protocol remain separate.

- [x] PR #62 merged 234ba2e; six integrated CI jobs PASS, Windows 243/243 and native sharing smoke verified. Production admission remains open.

- [x] ENG-08/10: Reject ambiguous portable ZIP and nested Host manifests/source evidence using bounded same-byte strict JSON, exact source evidence schema and extracted manifest validation. Reproduced duplicate-schema acceptance before fix; eight new regressions (251 required), real pinned archive/staging dry-run and prior verified backup PASS. Native CI required; archive payload mutation/hostile writers and full ZIP parser resource limits remain separate.

- [x] PR #65 merged 6c58953, seven CI jobs PASS, independently verified 251/251 Windows QA against actual synthetic merge Git identity.

- [x] ENG-10/05: Prototype Python CreateFileW lease interoperability with C# isolated contender, exact busy-only classification and exception-safe close; four offline adapter regressions, mandatory Windows cross-language smoke. No activation/mutation wiring; stable identity, ACL and cross-session qualification separate.

- [x] PR #63 merged 581c556; four integrated jobs PASS, independently verified Windows 255/255 and actual Python-owned cross-language lease smoke. Production admission remains open.

- [x] ENG-10/05: Smoke-only Windows lease handle identity observation (volume serial/file index, single-link and handle attribute checks); qualify two shared handles, held-name replacement/deletion refusal, hard-link rejection and distinct replacement identity. Native CI required; no persistent identity enrollment, ACL or production wiring.

- [x] PR #64 merged d8ee862; six integrated jobs PASS, independently verified Windows 255/255 and native identity/interop steps. No production lease enrollment or maintenance authorization.

- [x] ENG-10/05: Qualify C#-owned shared/exclusive lease with isolated Python contenders, exact busy/refusal controls, bounded child cleanup and unchanged bytes. Three offline scope regressions (258 required on integrated #63 base). Native Windows CI required.

- [x] PR #66 merged b048ff7; three integrated CI jobs PASS, independently verified Windows 258/258 and both native interop directions plus handle identity steps. No production admission.

- [x] ENG-08: Close JUnit evidence grammar to reviewed suite/case attributes and whitespace-only inter-element content; reject unreviewed XML declarations/instructions. Six new regressions (257 required on main base), real 251-case report accepted, tampered copy refused even after manifest reseal. Native CI required. Hashes and grammar are not evidence authenticity.

- [x] PR #67 merged 4db1f5b; four integrated CI jobs PASS, independently verified Windows 264/264 against exact synthetic Git merge.

- [x] ENG-09/10: Limit managed Host readiness to authenticated response headers (16 KiB, no response drain) and strip inherited persistence alongside LAN/TLS settings. Native isolated withheld-body 200/403 and synthetic environment smoke required. No production endpoint or user process used by the new fixture.

- [x] PR #68 merged 8086173; six integrated CI jobs PASS, independently verified Windows 264/264, native readiness step PASS.

- [x] ENG-12: Initial review-only metadata baseline for four architecture upstream repositories, exact HEAD and release commit identities in docs/upstream-review.md. No dependency adoption.
- [ ] ENG-12: Automate repeat observation and validate REVIEW/UNCHANGED/ERROR evidence, resolve Artemis reference and review relevant upstream code/license deltas.
- [ ] ENG-05/12: Design Windows display mirroring reconnect/restore regression informed by Screen Spawner v0.3.2. Actual topology mutation/hardware approval separate.

- [x] ENG-10/05: Cross-language expected lease handle identity comparison before admission, with Python fixed-width native structure, strict identity values, failure cleanup and native C# comparison/alias/replacement refusal. Six new offline cases (261 required on current main base); native Windows CI required. Persistent trusted enrollment and ACLs remain open.

- [x] PR #69 merged adcc976; four integrated jobs PASS, independently verified Windows 270/270 and actual expected identity/alias/replacement smoke.

- [x] ENG-10/05: Isolated owner-only Windows lease DACL qualification aligned with ProtectedGrantStore policy, exact raw ACE and owner checks on protected directory and held-file descriptor, reject unexpected ACE and unprotected DACL, restore fixture and verify unchanged bytes. Native CI required; no installed ACL changes, cross-user effective access, persistent enrollment or runtime wiring.

- [x] PR #70 merged 2879a47; six integrated CI jobs PASS, independently verified Windows 270/270 and native ACL fixture. Production admission and effective cross-user access remain open.

- [ ] ENG-12: Offline structured upstream evidence classifier with exact reviewed membership and metadata schema, bounded strict JSON, REVIEW/UNCHANGED/ERROR precedence and input digests. Eight new regressions (278 required), separate actual four-repository observation all UNCHANGED. Artemis repository identified and exact metadata recorded separately. Native CI required; live collector, freshness verification, fifth-repository integration and scheduling remain open.

- [ ] ENG-12: Explicitly extend upstream watch membership to Artemis and recompute/verify exact report against bounded source snapshots; eight additional regressions (286 required), real five-repository observation all UNCHANGED, tampered missing-row report refused. Shared classifier logic; independent implementation, origin/freshness and automated live collection remain separate. Native CI required.

- [x] PR #71 merged e2b53b7; three integrated jobs PASS; independently verified Windows/Android QA 278/278, exact main tree matches tested merge tree. Offline classifier accepted; collection/freshness separate.
- [ ] PR #72 retargeted to main after initial four jobs PASS and independently verified Windows/Android QA 286/286 on stacked base. Fresh integrated CI required before acceptance.

- [ ] ENG-12: Offline GitHub API snapshot normalization boundary (repository identity, latest stable release, direct tag ref and corroborating commit); eight regression cases. Live bounded transport, freshness, scheduling and native CI remain separate.

- [x] PR #72 merged fff1cfa; four integrated CI jobs PASS and independently verified Windows/Android 286/286 against exact merge tree. Artemis membership and report recomputation accepted.
- [ ] ENG-12: Fixed-origin public HTTPS metadata collector with bounded worker processes and incomplete-row refusal; eight offline regressions. Live observation, native integration, freshness and scheduling require separate evidence.
- [ ] ENG-12: Collector real public HTTPS qualification: five reviewed repositories UNCHANGED, exact detached source 1f7aeae and report verification PASS; 302 required local QA PASS. Native integrated CI required.
- [ ] ENG-12: Separate versioned freshness receipt, exact observation digest and bounded clock validation; no change to classifier contract or automatic adoption.
- [ ] ENG-12: Implement strict local freshness receipt and pure verification with eight offline regressions (310 required). CLI integration, actual receipt collection and native CI separate.
- [ ] ENG-12: Source-bound watch CLI, fresh exclusive evidence directory and strict bundle verification; eight additional offline cases (318 required). Live qualification and native CI required.
- [ ] ENG-12: Live negative source-bound receipt run: rate limit exhausted, one observed/four missing, collection and verification ERROR as designed. Stop-on-throttle regression added; complete real bundle remains pending quota recovery and native CI.
- [ ] ENG-12: CI admission and manifest seal for complete fresh upstream evidence; eight offline regressions (328 required). Incomplete reports never sealed. Manual workflow and actual live positive qualification separate.
- [ ] ENG-12: Manual main-only upstream watch workflow, bounded concurrency and time, explicit review warning, separate readback and seven-day accepted artifact retention. Scheduled activation requires complete live positive evidence and actual workflow qualification.
