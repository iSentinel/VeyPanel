# Android Host history synchronization

Status: codec and isolated runtime fixtures; not connected to the native UI yet.

The existing same-origin authenticated GET /api/v1/history returns timestampUtc,
windowSeconds=900, and up to 900 sorted numeric samples. Each point has seven
nullable CPU/RAM/GPU, codec, and disk-throughput metrics. The Android decoder
rejects stale snapshots, incorrect windows, duplicate/out-of-order points,
points outside the snapshot window, excessive counts, and malformed metrics.
Missing data stays N/A; no credentials or hardware identifiers are stored.

Next integration gate:
- Request a single explicit refresh after a fresh authorized live sample, using the
  existing private HTTPS origin and Bearer reader. Never accept redirects.
- Limit decoded response bytes and wall-clock read budget before JSON allocation.
- Merge in UTC order with observed live points, preferring live at identical
  timestamps; retain 900 points/900 seconds and label the Host data source.
- Bind every refresh to the existing foreground generation and reader session.
  Cancel/ignore stale callbacks and clear both history sources on pause, reader
  switch, Forget, disconnect, or terminal authorization failure.
- HTTPS 401/403 follows existing matching-reader credential invalidation;
  transport errors retain local observed data and display refresh unavailable.
- Add targeted merge, cancellation, revocation and live Host integration tests.
  No device or Windows Host end-to-end PASS is implied by isolated fixtures.
