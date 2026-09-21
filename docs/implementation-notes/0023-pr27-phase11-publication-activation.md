# PR #27 Phase 11.1 publication activation

Recorded: 2026-09-21 (Asia/Jakarta). Implementation-local, non-normative.

This change enables one short-lived `attested-v2` publication activation for
Codex PR #27 at exact head `f37a5c7d8e7d8cc6f4aad59f114cf96300b72335`.

The permanent promoted runtime first failed closed on privilege-only blockers.
Authority PR #34 added the exact 27-path privileged attestation. Reevaluation then
produced durable PASS evidence, receipt, and success-only permit.

Bindings:
- Authority/publisher source: `7df6068ff4a0ea0c6ad1219e374894283caaa6c9`
- permit: `3d9e21697a2ae683836f947221204408938918f23eaca419e0a19fc39a836177`
- evidence: `e2e20303d70ac32d157062c60aacf913816b99439167f90496f2d7e01e6baaa9`
- receipt: `dda021204dbf04c98cc13e8e3a12e9a3940dcf884f35b9bdf2e9a9dfc4bb0823`
- window: `2026-09-21T06:45:16Z` to `2026-09-21T06:59:16Z`

Bootstrap remains disabled. The activation grants publication only for this exact
candidate and does not move runtime semantic authority from the legacy registries.
After successful App publication and governed Codex merge, publication must return
to disabled/unbound state through a reviewed Authority change.
