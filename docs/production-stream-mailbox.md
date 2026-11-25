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

## Pre-allocation limit and upstream provenance review (2026-11-25)

Pinned com.squareup.okhttp3:okhttp:4.12.1 JAR SHA-256 in committed
Gradle verification metadata is
86706f20171c58167b4acca46a66a4039d6b7927543b5ed944b7311c3cb52de0.
Previously captured Maven POM SHA-256 is
d38ed8f1a69f36dd0338a0565c2c26474ee100c9f83d8d9e01af4df77847c339;
POM names Square and SCM github.com/square/okhttp. A GitHub API lookup
for that repository returned full_name lysine-dev/okhttp, and
parent-4.12.1 resolved to unsigned annotated tag
de765a904d46635313382a33d2c1a22032bdc3f7 targeting
f5dc9a0f3a268315f9776e07507f7f97459bb9d3. Candidate reader source SHA-256
c5a9870f1dcd5ded6410f1991fd216bdb62e74c52e60911e4f46e871b247d6ff
and RealWebSocket source SHA-256
8d1c3e93ca9399c0f72fa21122ea3049e260f41511d2453e872ca54009ebf6b4
are recorded separately from Maven artifact identity. The reader candidate
calls readFully(messageFrameBuffer, frameLength) before readUtf8/callback,
and optional inflation precedes delivery. Source-to-binary correspondence
and current repository provenance are unverified; do not infer compromise
or authenticate an unsigned tag. The production dependency remains pinned,
with no update or bypass of strict Gradle verification. Review exact binary
or independently authenticated source before transport replacement.

Experimental BoundedUpgrade now rejects bare CR/LF before parsing header
fields (four additional negative fixtures). This hardening is separate
from production OkHttp, and native CI remains required.

Verified PR #47 merged 37a07f5, eight CI jobs PASS, including actual Windows first-install recovery and Android runtime. Pre-allocation memory, publisher provenance and physical acceptance remain separate.
