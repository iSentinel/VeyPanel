# CPU/GPU thermal sensor provider investigation

Reviewed LibreHardwareMonitor v0.9.6 and the upstream master branch on 2026-11-22. Upstream license MPL-2.0; dependency/redistribution and hardware-access driver review remain required. No third-party code, executables or drivers bundled.

- Tagged implementation: https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/blob/v0.9.6/LibreHardwareMonitor/Utilities/HttpServer.cs
- Upstream master implementation: https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/blob/master/LibreHardwareMonitor.Windows.Forms/Utilities/HttpServer.cs
- Release: https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases/tag/v0.9.6

The v0.9.6 data.json tree contains SensorId, Type and formatted RawValue (string), whereas the reviewed master implementation uses numeric raw readings. Do not write a parser assuming the same representation. The tagged sensor GET operation returns result, value, min, max and format. The service also has control-write/reset operations; it must not be exposed automatically as an unauthenticated LAN service.

## Planned implementation
- Compare a separately installed, supported local library/provider adapter with an explicitly enabled loopback-only read interface. Prefer no new network listener and no automatic driver install or privilege elevation. Do not open a firewall port or disable provider authentication.
- Pin the provider contract and verify hardware/sensor types and units. Preserve provider sensor names and distinguish package, core and GPU/hotspot; no cross-adapter mapping by guessed name. Only actual numeric Celsius values with valid bounds are shown; unavailable readings stay null.
- Collect independently with bounded time, output and memory, explicit status and timestamps. Do not expose raw provider identifiers, process details or arbitrary provider commands to clients.
- Test fixtures for numeric/string schema difference, malformed and missing readings, stale data, and bounded failure. Require physical Intel Core Ultra 5 125H/Intel Arc validation against a known independent reference before declaring sensor accuracy.

Initial adapter implemented for the v0.9.6-shaped tree: explicitly enabled, fixed 127.0.0.1:8085 GET only, no proxy/redirect, rejects non-Celsius and non-string RawValue. Hardware IDs used internally for classification only. No version handshake in tagged data.json; real compatibility and sample freshness remain unverified. Do not disable authentication or expose a LAN listener. No bundled LHM binary or driver. ACPI zone temperature must not be relabeled as CPU package temperature.
