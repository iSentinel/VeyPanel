# Roadmap

- [x] Select product name, target hardware and architecture.
- [x] Write alpha CPU/RAM sampler and local browser dashboard.
- [x] Add source-level CPU arithmetic tests and Windows CI definition.
- [x] Compile on Windows CI; execute tests; validate real counters and unauthorized API responses ([run 45045388584](https://github.com/iSentinel/VeyPanel/actions/runs/45045388584)).
- [ ] Validate HTTPS LAN dashboard on Lenovo (certificate trust, stale samples, reconnect).
- [x] Apollo source baseline review (v0.4.6), API contract, official asset digest and read-only preflight source ([PoC plan](docs/apollo-poc.md)); preflight not executed on target.
- [x] Implement local-only Apollo inventory CLI and certificate pinning; mock tests written, CI and live compatibility pending.
- [ ] Apollo PoC: verify actual installer/publisher/driver catalog, TLS and API on host, Quick Sync; test mirror and extended desktop.
- [ ] 0.2: WPF tray host, display enumeration, safe topology capture/restore, PIN pairing.
- [ ] 0.3: GPU/encoder, SSD, network; sensor capability discovery and N/A semantics; WebSocket.
- [ ] 0.4: secure device enrollment, per-device revocation, QR, history.
- [ ] 0.5: Android client, native video and telemetry.
- [ ] 0.6: Display / Monitor / Hybrid modes; touchscreen coordinates and orientation.
- [ ] 0.7: overlay, alerts, history and diagnostics.
- [ ] 0.8: reconnection, sleep/wake and USB network transport.
- [ ] 0.9: installer, signing, reproducible release, upgrade/uninstall acceptance.
- [ ] 1.0: physical device acceptance and stable release.
