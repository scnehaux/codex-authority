# Codex PR #59: gdc010-baseline publication disarm

Recorded: 2026-11-12 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated App published exact-head success check [131105917904](https://github.com/scnehaux/codex/runs/131105917904) and revoked its installation token. The retained outcome is [the immutable candidate record](../../governance/publications/e11aadd8b1d13d7b40cf0585c316224d56b77b96.json), copied byte for byte from the sole durable journal outcome. The local attempt/outcome and permit/evidence/receipt stay outside Git and are never overwritten or replayed.

Restore disabled state and null activation. No standing publication capability, release, GDC approval or admission is granted.

- Codex [#59](https://github.com/scnehaux/codex/pull/59) squash merged at `d5e197a5adff35672bea351a6a3b1a15e15f1154`.
- Permit digest `ffebf7dfa77b072dc95a03b506b70717893ef7614fec79422b84db9da3319fce`; activation digest `e6e3402172deeb17222ab6de43ab507026b9d76dbd0f5eaa826ee1841dcd6409`.
- Offline preview: `controlled_publication_preview`, `remote_mutations: 0`; one published attempt; `token_revoked: true`.
