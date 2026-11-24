# Build source evidence

Status: PR #30 merged, Android and Windows CI PASS; downloaded artifacts verified. Record deterministic, factual source metadata with the
ordinary Android, Host and Desktop artifacts. Before compilation the
workflow reads actual Git HEAD, tree ID, source commit UTC epoch and
tracked cleanliness, requiring the actual checkout to match GITHUB_SHA.
Before publication it repeats the checks and verifies the source evidence
is unchanged. Generated untracked outputs are intentionally allowed.

The resulting build-source.json is covered by the file manifest. PR
checkout may be a synthetic merge commit, unlike the API's PR headSha.
Compare the recorded git_commit and git_tree rather than assuming matching
PR head IDs indicate exact source equality.

Local example from a clean tracked checkout:

    python3 -m unittest discover -s scripts -p test_build_source_evidence.py -v
    python3 scripts/build_source_evidence.py build-source.json --expected-sha "$(git rev-parse HEAD)"
    python3 scripts/build_source_evidence.py build-source.json --expected-sha "$(git rev-parse HEAD)" --verify

This evidence records Git state at two points. It is not a signed
attestation, sandbox enforcement, proof that every compiler input was
tracked, or proof of byte-identical builds. No secrets or device data
are collected.

Verified PR #30 artifacts from runs 45404957532 and 45404957357 record identical actual checkout 7c4d5a67940fbbc97144500b0d72d334dd93d3de and tree c8df57d8256d3b2c2afa87f0e411b4dcac632fef.
