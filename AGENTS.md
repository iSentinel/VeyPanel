# VeyPanel engineering rules

- Read ROADMAP.md and RESUME.md before changing code. Update checkpoints after each verified stage.
- Technical docs in English. Small focused methods, clear exception handling and structured logs; never log tokens or secrets beyond the explicit local enrollment link.
- Only real data; unavailable sensors must be null/N/A, never fake zero. Use UTC sample timestamps and stale detection.
- Local-only by default. No cloud dependency, internet exposure, automatic firewall changes or untrusted drivers.
- Do not alter display topology without saving the prior config and a rollback path. No Secure Boot/test-signing bypass.
- Every release includes tests, build evidence, version, sample commands and known limitations. Hardware PASS only after actual device tests.
- Keep third-party components separated until license and redistribution obligations are reviewed.
