# Codex PR #55: gdc006-baseline publication disarm

Recorded: 2026-11-11 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated App published exact-head success check [130464125887](https://github.com/scnehaux/codex/runs/130464125887) and revoked its installation token. The retained outcome is [the immutable candidate record](../../governance/publications/9b5876dc90fe15173e63835b6e0a0ccfeb6b8b05.json), copied byte for byte from the sole durable journal outcome. The local attempt/outcome and permit/evidence/receipt stay outside Git and are never overwritten or replayed.

Restore disabled state and null activation. No standing publication capability, release, GDC approval or admission is granted.

- Codex [#55](https://github.com/scnehaux/codex/pull/55) squash merged at `6e8236b8e715dc3296f86831644c50932b33539d`.
- Permit digest `1ef5e2cc7a40dc129f24ce5a258eb46712c199fec4e8049b3bea944f19cdbeba`; activation digest `3e8623b36002a2f8e8e22e74aaaec8ec5edfeb6078cb7dcef175a674256519ea`.
- Offline preview: `controlled_publication_preview`, `remote_mutations: 0`; one published attempt; `token_revoked: true`.
