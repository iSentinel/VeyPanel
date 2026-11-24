# Touch coordinate math — read-only stage 0.6

Status: pure geometry and synthetic Windows CI fixtures. **No input forwarding,
pointer injection, network endpoint or display mutation exists.**

The contract takes a tablet viewport in pixels (positive width and height),
the decoded video frame size, the frame's clockwise rotation relative to the
desktop, and one explicitly selected Windows desktop display rectangle.
The frame is rendered with *contain* aspect-ratio fitting and equal letterbox
bars. Touches in bars or outside the view are rejected rather than projected
onto the wrong monitor.

For an accepted viewport point, normalized video coordinates `u,v` are
converted back to unrotated desktop coordinates:

| Frame clockwise | Desktop u | Desktop v |
| --- | --- | --- |
| 0 | u | v |
| 90 | v | 1 - u |
| 180 | 1 - u | 1 - v |
| 270 | 1 - v | u |

Map to pixel indices using the selected desktop rectangle's inclusive
`(width-1,height-1)` extents, with half-away-from-zero rounding. Windows
rectangles have an exclusive right/bottom edge. Negative origins are valid,
but invalid, nonfinite, oversized or overflowing geometries are rejected.
A different display identity, rendering crop, DPI scale, viewport resize or
rotation requires a new validated mapping snapshot. This geometry must **not**
be used to authorize input.

Acceptance gates before any real touch support:
- Fresh capture of the intended target display identity and geometry, plus
  explicit pairing and owner approval for interactive input.
- Matching the actual decoded frame, letterboxing/cropping, rotation, and
  tablet touch coordinates, including negative desktop origins.
- Block clicks on stale, disconnected, hidden, cloned or unmatched targets.
- Physical 0/90/180/270-degree taps, drag/cancel, multi-touch policy and
  sleep/wake acceptance with Lenovo TB-J607Z and Windows Host.
- No Windows injection or display topology writes in this stage.

Windows CI tests use only synthetic rectangles; a PASS does not mean physical
input or Display/Monitor/Hybrid acceptance.

## Android parity

`TouchMath` mirrors `TouchMapping` for the same 17 synthetic vectors,
including negative origins, contain-fit letterbox rejection and 90-degree
transforms. The JVM and Windows CI both assert the fixtures before any
input-forwarding feature can be considered. There is no touch listener,
gesture capture, network transport or OS input injection yet.
