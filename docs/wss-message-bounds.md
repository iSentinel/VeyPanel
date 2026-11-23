# Telemetry WebSocket message bounds

Status: Host outbound cap and experimental Android frame-header gate and bounded message assembler with JVM fixtures.
The Android production WSS client still uses OkHttp; its onMessage callback limit
is after buffering/decompression and is not a pre-allocation memory guarantee.

The trusted Windows Host refuses to transmit a serialized telemetry payload larger
than 1 MiB. This is an outbound wire cap, not a bound on serialization memory.
The new header gate accepts uncompressed, unmasked, server-to-client text frames,
permitted continuations and bounded control frames. Extended lengths are checked
before a payload read, including canonical encoding and a caller-supplied remaining
aggregate message budget. The assembler retains a bounded message, rejects malformed UTF-8, limits frames per message to 256 and dispatches control frames. Neither component implements full WebSocket transport or its time/close validation.

Integration requirements:
- Preserve OS TLS trust, IP hostname verification and same fixed private origin.
- Use a reviewed bounded transport or a separately reviewed complete implementation;
  enforce header and aggregate byte limits before allocation, reject extensions
  unless safe decompression is separately established, and cap frames/time per message.
- Validate upgrade status/headers, accept-key, UTF-8, close frames, control handling,
  client masking, deadlines and cancellation; no tokens in URL or logs.
- Add actual TLS oversized-header, fragmented aggregate, malformed UTF-8, close,
  ping/pong and cancellation fixtures before replacing the current client.
- Keep REST fallback, deny invalid TLS, and retain device revocation semantics.

## Isolated TLS prototype

PR #4 adds bounded HTTP Upgrade, RFC accept-key verification, extension refusal,
masked client auth/control frames, and an instrumentation-only TLS socket.
The test exchange uses HTTPS endpoint identification, an explicit fixture trust
factory (or default trust for negative checks), 3 s socket timeout and an
8 s overall close watchdog. It checks a valid sample and oversized header
without receiving the advertised payload. Production remains unchanged.
Close status validation, full ping/pong, continuous deadline/cancellation and
production user CA acceptance remain open.
