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

- [ ] 0.9: Run independent Windows exact-checkout Host reproduction with raw and experimental timestamp-normalized inventories, smoke tests and exact normalized file comparison; CI pending. Normal publication unchanged.
