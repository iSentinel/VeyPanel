# Architecture

Two independent planes:

1. Video plane (planned): Windows Host -> Apollo -> signed SudoVDA virtual display or physical monitor -> Quick Sync H.264/HEVC -> Moonlight/Artemis -> Lenovo. Input returns via the existing streaming protocol. No custom display driver in MVP. Validate supported APIs against pinned upstream sources before coding adapter.
2. Telemetry plane: Windows GetSystemTimes and GlobalMemoryStatusEx -> one-second immutable snapshot -> token-protected REST endpoint -> browser dashboard. Later migrate to authenticated secure WebSocket and native Android UI.

## Safety and known limitations

No remote control endpoints exist. Local HTTP is loopback-only; experimental LAN listener requires explicit IPv4 and TLS PFX. Browser must trust the certificate. Tokens are ephemeral, not per-device; restart revokes all access. No discovery, certificate enrollment, QR, rate limits or audit log yet. Remote clock must remain synchronized within five seconds for stale check. No security audit performed.

CPU utilization is based on interval kernel+user time minus idle time, with Windows kernel time including idle. The current GetSystemTimes approach covers a processor group; multi-group systems need a separate implementation. Memory utilization means physical total minus physical available, not process commit. GPU temperature and NPU capability are unverified; future collectors must return null on missing sensors.

Upstream references: https://github.com/ClassicOldSong/Apollo ; https://github.com/moonlight-stream/moonlight-android ; https://github.com/itkawa/screen-spawner ; https://github.com/LibreHardwareMonitor/LibreHardwareMonitor . Review each license and notices before redistribution; no upstream code copied into this checkpoint.
