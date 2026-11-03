# Codex PR #51: gdc002-baseline publication disarm

Recorded: 2026-11-03 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated App published exact-head success check [125863102419](https://github.com/scnehaux/codex/runs/125863102419) and revoked its installation token. The retained outcome is [the immutable candidate record](../../governance/publications/19988ad917a07f19aba9d19c41ee0ec5d64e4c63.json), copied byte for byte from the sole durable journal outcome. The local attempt/outcome and permit/evidence/receipt stay outside Git and are never overwritten or replayed.

Restore disabled state and null activation. No standing publication capability, release, GDC approval or admission is granted.

- Codex [#51](https://github.com/scnehaux/codex/pull/51) squash merged at `7ead894fc19fdf72c0160e0cc2bf87420d63966e`.
- Permit digest `a0f04aeb762d8a8bbfcd6abed9c8b109fc3d14a82e54a28a6e362666d2d5e69f`; activation digest `9a4a39559951ef064c04377311bfda646c3ea72bdf3172371d26b2c1164e62a7`.
- Offline preview: `controlled_publication_preview`, `remote_mutations: 0`; one published attempt; `token_revoked: true`.
- Sequence: owner ARB approval record #139 (GDC-002 1.0.0, merged before attestation), attestation #140, activation #141, this disarm. REC-13-003 order held.
