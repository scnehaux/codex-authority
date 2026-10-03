# PR #41 Phase 12 exit controlled publication activation

Recorded: 2026-10-03T12:26:55Z. Implementation-local, non-normative.

Enables one short-lived publication attempt for exact Codex PR #41 after its independently merged attestation and promoted credential-free runtime returned PASS.

- Candidate head: `0008d5ac80358e5534917b5f26f3673dca2ae4a3`
- Candidate base: `6d08b695556f19ceff78e50996fa027cb95e862b`
- Authority and publisher source: `755781dd18eaa43dcc6750f55311322bbb7d1abc`
- Permit digest: `662470fc96b77d4778cc829b22b67895d7d150ab6b808354e1e2d0f3181f95d6`
- Evidence SHA-256: `058693efb413cd2765c168ee45eaaabf86812184ed127688fc9536102590d76a`
- Receipt SHA-256: `328ebb007bad6ad829adb66bed3a46c67d36c1e0c1852ecfbae3fa41b788e004`
- Window: `2026-10-03T12:26:40Z` through `2026-10-03T12:41:40Z`

The existing source-bound App check, credential isolation, one-attempt journal, token revocation and provider rules remain required. Disable the activation after this attempt. Governance 1.0 remains NOT READY and architecture admission remains CLOSED.
