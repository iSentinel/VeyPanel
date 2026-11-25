# Host smoke process privacy

Status: candidate; Windows CI required.

ENG-04 targeted audit: the published Host smoke previously redirected raw
stdout/stderr to temporary files, including the ephemeral owner bootstrap
URL. Deletion in finally did not guarantee removal after interruption.
The smoke now uses child-owned anonymous pipes; only the exact owner
bootstrap line is returned to the private caller. Other output is discarded
and no raw child log file is created. LAN, certificate and persistence
variables are removed from the child environment only. Existing standalone
loopback assertions remain mandatory, with an explicit readiness check.
Owned process cleanup and stream drain waits are bounded. Raw HTTP/child
errors are not printed; fixed assertion labels remain available.

Run on a dedicated Windows test runner with no competing Host:

    pwsh -File scripts/Test-HostSmokeCapture.ps1
    pwsh -File scripts/Test-Host.ps1 -PublishDirectory publish

The synthetic fixture rejects malformed lines and checks that only the
expected token is returned; neither fixture token is printed. Published
Host integration and reproduction workflows exercise the actual smoke.
This is not secure erasure, process memory protection, a general log
redactor or a hostile child process sandbox. ReadLineAsync assumes the
trusted owned Host and its bounded ordinary output. The interactive owner
URL remains a deliberately private user-facing secret. Review framework
request logging and native diagnostic capture separately; no comprehensive
privacy acceptance or actual leak in an existing public log is asserted.
