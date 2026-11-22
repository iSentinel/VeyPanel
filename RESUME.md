# Resume checkpoint

2026-11-22 — 0.1.0-alpha.1, Windows CI remediation.

CI run 45045176828: Host build PASS, zero warnings/errors. Smoke project failed CS1022 (extra closing brace). Corrected the test source and added Windows runtime integration smoke for the published host (static assets, token rejection, actual CPU/RAM counters, freshness and continued sampling). Next CI must confirm results before any PASS claim for runtime or package.

No Lenovo/Intel Arc hardware validation, LAN TLS verification or Apollo installation has occurred. Continue with read-only Apollo discovery, then a pinned upstream integration and physical-device PoC. No driver changes or redistribution until review. Original code license remains an owner decision.

Evidence: https://github.com/iSentinel/VeyPanel/actions/runs/45045176828
