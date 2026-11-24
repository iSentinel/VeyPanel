# Android video decoder capability survey

Status: read-only Android alpha.15 candidate, CI/hardware acceptance pending.

The native UI exposes an explicit on-demand inspection of regular decoders for
AVC, HEVC and AV1 using Android MediaCodecList. Codec entries identify the
codec and MIME type and query declarative size/rate support at 720p60,
1080p60 and 2560x1600@60. Hardware acceleration classification uses
MediaCodecInfo.isHardwareAccelerated() on API 29+ and N/A on older systems.

No MediaCodec instance is created; no video data, stream or personal identifiers
are collected, and no external network or display topology is modified.
Results are kept in foreground UI memory. Results may list aliases or software
codecs; declared support is NOT demonstrated decoding performance.

Acceptance requires Lenovo TB-J607Z physical evidence: Android API level,
available codecs, actual hardware acceleration, 60 Hz sustained decode,
render latency, resolution, rotation, color, thermal behavior and reconnect.
The Windows capture/Quick Sync/APOLLO path is not established by this survey.

API references: Android MediaCodecList, MediaCodecInfo and VideoCapabilities
in the official Android SDK documentation.

## Original AVC decode fixture

The instrumentation APK contains an original red 64x64, two-frame AVC Baseline
MP4 generated from FFmpeg's `color` source. The `VideoDecodeSmoke` test uses
MediaExtractor and Android MediaCodec with byte-buffer output. It requires both
input access units to be submitted, at least one decoded output buffer, and
end-of-stream within eight seconds. It always releases the codec and extractor.

This is an emulator *actual decoding* smoke, not hardware-accelerated decode,
sustained 60 FPS throughput, display latency, hardware encoder interoperability
or physical Lenovo acceptance. No third-party video material is included.

Fixture SHA-256: f5817649d60c70b99db2c54cffcacf0bbe23c5384515165b9b1e71f4d8bb81a6.

## Native Surface output smoke (test-only)

The next instrumentation gate configures MediaCodec with a local Android
`Surface` backed by a `SurfaceTexture`. It feeds the original two-frame
AVC asset, requires end-of-stream and at least one released rendered frame,
then waits for an Android frame-available callback. The surface is never
attached to a remote monitor or external network and is fully released.

The test does not prove that a frame reached the tablet display, was read
from the GPU, met a latency deadline, or used hardware acceleration.
Those are separate physical device acceptance criteria.
