# Architecture

## Current alpha architecture

- Windows Host (.NET 10 / ASP.NET Core): read-only sampled telemetry,
  local HTTP dashboard and optional explicitly configured LAN HTTPS.
  REST, authenticated WSS, history/CSV, bounded device grants and local
  two-step enrollment are implemented. Standalone DPAPI persistence is opt-in.
- Windows Desktop (WPF): local tray/diagnostics and bundled Host lifecycle.
  Apollo inventory and owner-confirmed pairing are experimental; interactive
  Windows acceptance remains open.
- Native Android (Java 17): monitor, WSS-first/REST fallback, QR and optional
  Keystore access, local history and diagnostics. Local AVC preview, decoder
  survey and touch probe are not network video or input forwarding. The
  bounded transport prototype is not the production OkHttp transport.
- Video plane (planned): Windows Host -> reviewed Apollo / signed virtual
  display or physical monitor -> H.264/HEVC -> tablet. No custom driver in
  MVP, no display mutation or live input without approved scope and rollback.
- Build and package tooling: Python standard library, PowerShell, native
  Gradle/NuGet and GitHub CI. Unsigned portable ZIP, staging and metadata
  selection/rollback are separate from process activation and release signing.

## Safety and known limitations

See SECURITY.md and the engineering adoption audit. Local HTTP is loopback
only; LAN requires explicit IPv4 and trusted TLS. Owner operations remain
local, reader grants are scoped and revocable. Physical WPF/tablet,
network video/input, durable recovery and full security acceptance remain
open. The architecture describes implemented components, not hardware
qualification.

CPU utilization is based on interval kernel+user time minus idle time, with Windows kernel time including idle. The current GetSystemTimes approach covers a processor group; multi-group systems need a separate implementation. Memory utilization means physical total minus physical available, not process commit. GPU temperature and NPU capability are unverified; future collectors must return null on missing sensors.

Upstream references: https://github.com/ClassicOldSong/Apollo ; https://github.com/moonlight-stream/moonlight-android ; https://github.com/itkawa/screen-spawner ; https://github.com/LibreHardwareMonitor/LibreHardwareMonitor . Review each license and notices before redistribution; no upstream code copied into this checkpoint.
