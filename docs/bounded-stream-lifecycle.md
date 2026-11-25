# Experimental bounded WSS lifecycle

Status: candidate, native JVM/Android emulator acceptance pending.

ENG-09 audit: the experimental transport registered raw sockets outside
the cancellation decision, scheduled deadlines independently of shutdown,
and permitted concurrent next() calls against one frame reader. A timer
whose cancellation raced with its callback could close a later read.

The new state object serializes socket attachment, cancellation, reader
admission and operation-specific deadline identity. A socket created after
cancellation is closed rather than orphaned. A second reader is rejected
without closing the admitted reader. A stale timer cannot affect a later
operation. An operation that completed past its monotonic deadline fails
even when the callback was delayed. IO is not performed under the state
lock except for closing the owned socket. Existing TLS endpoint
identification, pre-allocation frame/message limits, timeouts and client
masking are unchanged.

Four deterministic JVM fixtures exercise state transitions without network
access, alongside existing real TLS/emulator tests (untrusted CA,
messages, frame rejection, cancellation and drip-feed deadline). No
production transport switch: MainActivity still uses OkHttp. Its callback
size check is post-allocation; bounded prototype still requires broader
trust, lifecycle and freshness qualification before any integration.
No real hardware or hostile-network robustness claim.

Verified combined acceptance: PR #45 merged 5bb5505, all fourteen CI jobs passed. Native scope only; physical and production acceptance remain separate.

## Trusted wrong-IP SAN acceptance candidate

The existing emulator fixture tests an unknown CA and a valid explicitly
trusted certificate. A second phase uses the same isolated CA and a new
leaf with CN 127.0.0.1 but IP SAN 127.0.0.2, while the client connects to
127.0.0.1. OpenSSL verifies the chain and intended SAN and rejects the
actual target IP. The first-phase checks remain mandatory. HTTPS REST,
production OkHttp WSS and experimental bounded WSS must each reject the
wrong-SAN peer with a TLS-classified failure. The negative server flags
any parsed HTTP request without recording its contents, and the runtime
script requires no such request. This guards against sending the
synthetic Authorization header or WebSocket token to the wrong identity.

Local certificate and observer controls PASS; Android API 33 emulator
acceptance remains required. Fixture CA injection is test-only and does
not establish Android owner-installed user CA behavior, physical device
trust, or end-to-end Activity fallback behavior. Production code, pins,
network binding, trust policy and transport selection are unchanged.

Verified PR #51 merged 73d97b6, all eight CI jobs PASS. Runtime 45542682969 confirmed three trusted wrong-SAN refusals and no parsed HTTP request. This is isolated fixture trust, not physical owner-installed CA acceptance.

## Shared TLS failure classification candidate

Activity WSS handling recognized wrapped TLS failures but REST polling
and Host history handled only direct SSLException; synchronous WSS
construction errors also fell back unconditionally. Share the existing
eight-cause classification across these paths. Recognized TLS or
certificate failures stop the foreground session; ordinary network
failures retain existing retry/HTTPS fallback behavior. No exception
message is inspected or displayed. Existing denial behavior is unchanged.
A bounded JVM fixture checks direct/wrapped errors, normal network errors,
message-only canaries, null, cycles and the existing depth limit.
A TLS cause beyond eight entries is not recognized by this classifier;
this is not comprehensive arbitrary exception graph classification.
Native and Activity-level acceptance remain separate. No trust or
production transport selection change.

Verified PR #52 merged 35bfe9c: eight CI jobs PASS, actual Windows and Android common QA each 207/207 with exact case identities; shared TLS classifier JVM and existing runtime gates passed. Scope remains offline/emulator only.

## Activity terminal TLS candidate

In the isolated negative TLS phase, exercise MainActivity's actual
production WSS constructor and asynchronous reader, using a synthetic
loopback ReaderSession inserted by androidTest reflection only. No
production admission, transport, trust or link parser change. The default
production trust store is used, not the injected fixture CA, so failure
may be unknown CA rather than SAN mismatch; the three separately
trusted-SAN transport checks remain mandatory. Require terminal TLS UI,
one WSS attempt, zero fallbacks/REST errors/fresh samples, disabled
history and cleared session/stream. Recheck after 3.5 seconds to detect
normal poll retries. The negative server request observer remains required.
This is not a test of all possible delayed callbacks, concurrent history
completion or owner-installed CA behavior. Emulator CI required.

Verified PR #53 merged f473688, all eight CI jobs PASS. Downloaded Windows/Android reports each 215/215 with independent validator and manifest verification. Runtime 45543711027 confirmed actual Activity terminal TLS with no fallback/retry and negative fixture no-request gate. Physical trust and concurrent network cancellation remain separate.

## Ordered Activity history/telemetry terminal fencing candidate

The real Activity receives deterministic synthetic callbacks on its UI
thread, without any network I/O, actual credentials or production changes.
Two independent Activity instances exercise terminal telemetry failure with
history pending, and terminal history failure with telemetry pending.
A positive synthetic history snapshot first confirms callback delivery.
The terminal callback must cancel both pending FutureTask fixtures, close
the synthetic feed exactly once, invalidate the generation, clear active
session, live data and history, and disable history refresh. Late sample,
history success and denial callbacks from the old generation must not
alter the terminal state or affect a subsequent same-access session.
The synthetic reconnect tests callback fencing, not credential admission
or an actual connection. The existing real negative TLS phase remains
mandatory. This is ordered interleaving coverage, not concurrent network
cancellation latency or actual socket closure qualification.

Verified PR #54 merged 542eb08, all eight CI jobs PASS. Actual common QA each 219/219, zero unattributed outcomes, manifest/independent verifier PASS. Ordered Activity callback fixture passed; actual concurrent network cancellation not yet qualified.
