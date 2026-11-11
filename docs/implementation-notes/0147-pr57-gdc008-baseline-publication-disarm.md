# Codex PR #57: gdc008-baseline publication disarm

Recorded: 2026-11-11 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated App published exact-head success check [130581070166](https://github.com/scnehaux/codex/runs/130581070166) and revoked its installation token. The retained outcome is [the immutable candidate record](../../governance/publications/2d3b1a5f8cc2db9012db3b9be938cd543898a73b.json), copied byte for byte from the sole durable journal outcome. The local attempt/outcome and permit/evidence/receipt stay outside Git and are never overwritten or replayed.

Restore disabled state and null activation. No standing publication capability, release, GDC approval or admission is granted.

- Codex [#57](https://github.com/scnehaux/codex/pull/57) squash merged at `879dffb7f64c4e088c06a9da0043562105d23692`.
- Permit digest `6b1df16442b20623ca89255bee3aecffb834fa5754a4450a4341d8716d200e19`; activation digest `74c369a5c2ae59fe035c75221cae337fccca232a601281757ba5dfd3aadff187`.
- Offline preview: `controlled_publication_preview`, `remote_mutations: 0`; one published attempt; `token_revoked: true`.
