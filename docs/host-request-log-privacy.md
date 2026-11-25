# Host framework request log privacy

Status: candidate, native Windows CI required.

ENG-04: default ASP.NET Core logging providers can render request paths,
query strings and exception messages before authorization. VeyPanel clears
these providers immediately after builder creation. A logging level from
the environment or configuration does not enable a removed provider.
This deliberately removes ordinary framework startup/request diagnostics;
the private owner/reader bootstrap strings and explicit CLI status
messages are unchanged. Future operational logging requires reviewed,
closed-schema events rather than a generic text sink.

The native published-Host smoke uses a new owned loopback process, trace
log levels, synthetic request canaries in path/query/header, invalid and
valid authorization, and graceful managed shutdown. It observes stdout
and stderr without writing raw lines, reports fixed statuses, and requires
the canary not to appear outside the permitted bootstrap. An independent
synthetic observer fixture verifies detection. The actual owner token is
also checked in lines observed after bootstrap. No persistent capture file
is created. Run only on a dedicated test environment without competing Host:

    dotnet run --project tests/VeyPanel.Smoke -c Release -- --request-log-smoke publish

Scope: default framework providers in this Host, not all possible process
output, unhandled runtime exceptions, diagnostic listeners, crash dumps,
reverse proxies or external tracing. Not a general secret-redaction claim.
No actual historical credential leak is asserted. No TLS, grant or
network binding policy is changed. Native CI and broader native logging
review remain mandatory.
