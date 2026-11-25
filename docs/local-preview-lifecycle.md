# Local preview tap lifecycle

Status: candidate; JVM and Android emulator CI required.

The synthetic 64x64 local AVC diagnostic accepts coordinates only after
the existing decoder/TextureView completion gate. A single-pointer DOWN
must precede UP; pointer changes, movement beyond platform touch slop,
cancellation, nonfinite coordinates and preview loss invalidate the tap.
Historical move samples are checked. No remote input is forwarded.
The Activity clears previous touch state when paused, when the texture is
lost, or when another diagnostic starts; failed previews are hidden.
The Surface wrapper is created inside the worker so an interrupted queued
job cannot leave an allocated wrapper that never reaches its finally block.

Remaining limits: TextureView destruction versus active codec ownership
requires separate coordination, and reused-texture callbacks do not carry
a decoder generation. This is not proof of decoded pixel correctness,
physical input behavior, remote video or Windows input injection.

Verified combined acceptance: PR #45 merged 5bb5505, all fourteen CI jobs passed. Native scope only; physical and production acceptance remain separate.

## Texture ownership candidate

Each new preview replaces the TextureView and binds callbacks to its own
target. The worker acquires a one-use lease before creating the Surface;
a texture destroyed before acquisition is not used. During active decode,
the destruction callback returns false and transfers release responsibility
to the worker, which releases the Surface after codec cleanup and posts
texture release to the UI queue. If decode already finished, the framework
retains release responsibility. Stale view callbacks cannot affect the
new target. JVM ordered-interleaving fixtures and repeated Activity
preview test added. Native CI remains mandatory. This is not proof of
codec native call deadlines, pixel correctness, or physical GPU lifecycle.

Verified texture ownership: PR #46 merged cc88ceb, all eight jobs PASS, including repeated Activity preview and independent APK comparison. Initial Maven 429 retained in RESUME; physical GPU acceptance remains open.
