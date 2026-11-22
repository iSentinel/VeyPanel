# Resume checkpoint

2026-11-22 — 0.1.0-alpha.1, Windows CI verified.

- Initial CI run 45045176828: Host compiled; smoke source failed CS1022.
- Remediation e3111d67d9c3c5139b85a6f69b19e7ffe601e057: removed stray brace; added two arithmetic cases and published-host integration smoke.
- Run 45045388584, job 137278763295: Host built with zero warnings/errors; 8/8 CPU math tests; actual Windows CPU/RAM counters, static assets, token rejection, freshness and repeated sampling PASS. Self-contained Windows x64 artifact 14763099335 uploaded (50,034,191 bytes). This is an unsigned alpha CI artifact, not a release.
- Apollo v0.4.6 source/REST auth review completed. Added read-only preflight source and physical acceptance matrix in docs/apollo-poc.md. No driver installed; preflight not yet run on target.
- The newer commits contain docs/preflight only; their own CI status was not yet confirmed at checkpoint.

Next: validate the local dashboard on physical Windows host, validate certificate trust and HTTPS LAN on Lenovo, run read-only Apollo preflight and verify installer/driver provenance, then implement the authenticated Apollo adapter and test Mirror/Extend. Actual GPU encode/decode, Lenovo display, WPF, Android native app and WebSocket remain pending. Original source license is still an owner decision. Never install a driver or modify display topology without recovery plan.

Evidence: https://github.com/iSentinel/VeyPanel/actions/runs/45045388584
Artifact: https://github.com/iSentinel/VeyPanel/actions/runs/45045388584/artifacts/14763099335
