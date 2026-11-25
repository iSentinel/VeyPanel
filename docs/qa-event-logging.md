# Scoped offline QA event logging

Status: candidate; local Python tests PASS. This is a first ENG-04
increment, not a comprehensive secret-redaction or Host logging solution.

    python scripts/run_offline_qa.py --output artifacts/qa-unique --log-events

Create the private parent directory first; the output directory must be new.
The existing stdout summary and exit codes are unchanged (0 PASS, 1
execution/report error, 2 failed gate). Opt-in events are JSONL on stderr.
The closed schema has schema, timestamp_utc, level, event, stage, status,
reason and duration_seconds. Stage/status pairs are allowlisted; duration is
bounded, finite, nonnegative and derived from local monotonic time. UTC is
for correlation only. No arbitrary message, path, credentials or exception
content is accepted by this event API. Failure results still fail the gate.

Events describe the Python offline scope only. A safe event schema does not
sanitize other subprocess output, arbitrary test output or existing CLI
diagnostics. Evidence must still be reviewed before sharing. Keep stdout
and stderr separate; no global logging sinks are modified.

## Targeted audit follow-up

- Host Program.cs emits private loopback owner and optional LAN reader URLs.
  These are intended for local enrollment; they must never be captured in
  shared logs. Review HostController, Test-Host and evidence collection for
  accidental capture, with synthetic secret canaries.
- ApolloInspectCommand.cs reports exception type rather than raw exception
  text; inventory output is user-facing and needs a field-level privacy review.
- Several legacy Python CLIs print raw exception messages (manifest, source
  evidence, advisory/license evidence, ZIP and package tools). Preserve the
  documented human/exit contracts while migrating to safe reason codes; no
  blanket replacement or raw path disclosure.
- Review Android exception propagation, UI diagnostics, credential storage
  and transport failures separately; grep inspection is not a complete audit.
- Persistent operational event rotation, retention and native event adapters
  remain open. No claim of comprehensive secret sanitization.
