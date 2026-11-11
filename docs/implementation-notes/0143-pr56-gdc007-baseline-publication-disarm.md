# Codex PR #56: gdc007-baseline publication disarm

Recorded: 2026-11-11 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated App published exact-head success check [130486999326](https://github.com/scnehaux/codex/runs/130486999326) and revoked its installation token. The retained outcome is [the immutable candidate record](../../governance/publications/ab724e243dbc2c4e91729a15384c985a269f07e7.json), copied byte for byte from the sole durable journal outcome. The local attempt/outcome and permit/evidence/receipt stay outside Git and are never overwritten or replayed.

Restore disabled state and null activation. No standing publication capability, release, GDC approval or admission is granted.

- Codex [#56](https://github.com/scnehaux/codex/pull/56) squash merged at `9c5f45dc218cf8ab8b96db95d42ba62eb688858a`.
- Permit digest `e93c9ca668e8e1f9078db4d82513d0e2f8c94a3d420004c34495488a73f35577`; activation digest `29568f55fade5d0fa9b6915b02efce3426f96d63140caedcda18043a3201ad62`.
- Offline preview: `controlled_publication_preview`, `remote_mutations: 0`; one published attempt; `token_revoked: true`.
