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
