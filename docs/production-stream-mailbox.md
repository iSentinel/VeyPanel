# Production OkHttp telemetry mailbox

Status: candidate; native Android CI required.

ENG-09: the old queue and terminal flag were independent, allowing a callback
to publish after close cleared the queue. Replace with a synchronized one-slot
mailbox. First terminal cause is immutable, late publication refused, a
waiting reader is notified immediately, concurrent reads rejected without
cancelling the admitted reader, and receipt-to-consumption age is bounded
to five seconds using a local monotonic clock. The existing sample UTC
freshness check remains separate. No change to TLS, proxy, redirect, REST
fallback or token policy. Existing fixed 5.5-second wait budget retained.

Pure JVM fixtures cover replacement, stale sample, terminal precedence,
concurrent reader and cancellation; actual TLS instrumentation adds a
closed-stream refusal. Python QA does not qualify these Java changes.

The existing text-length limit runs after OkHttp assembles the message.
Neither this mailbox nor its tests establish a pre-allocation WSS memory
bound. Review the pinned OkHttp reader and experimental bounded transport
before changing production selection; compression, actual user CA trust,
readiness and physical acceptance are separate prerequisites. No automatic
dependency change or TLS bypass. Local monotonic age is not server freshness.
