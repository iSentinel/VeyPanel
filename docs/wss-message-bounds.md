# Telemetry WebSocket message bounds

Status: Host outbound cap and experimental Android frame-header gate with JVM fixtures.
The Android production WSS client still uses OkHttp; its onMessage callback limit
is after buffering/decompression and is not a pre-allocation memory guarantee.

The trusted Windows Host refuses to transmit a serialized telemetry payload larger
than 1 MiB. This is an outbound wire cap, not a bound on serialization memory.
The new header gate accepts uncompressed, unmasked, server-to-client text frames,
permitted continuations and bounded control frames. Extended lengths are checked
before a payload read, including canonical encoding and a caller-supplied remaining
aggregate message budget. It does not implement WebSocket transport.

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
