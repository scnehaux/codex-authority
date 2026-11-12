# Codex PR #58: gdc009-baseline publication disarm

Recorded: 2026-11-12 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated App published exact-head success check [131046587442](https://github.com/scnehaux/codex/runs/131046587442) and revoked its installation token. The retained outcome is [the immutable candidate record](../../governance/publications/229289b07077dfa4a60049e17e4da3fc2d4253e2.json), copied byte for byte from the sole durable journal outcome. The local attempt/outcome and permit/evidence/receipt stay outside Git and are never overwritten or replayed.

Restore disabled state and null activation. No standing publication capability, release, GDC approval or admission is granted.

- Codex [#58](https://github.com/scnehaux/codex/pull/58) squash merged at `75da9af4415ef9b4f930995e1047a241d32fc952`.
- Permit digest `b3723cd8ec3b6e343e94e517daa6c53744aa81ec8af4881e9da93b319488bf90`; activation digest `0c5d14c2b7203ed83e6adf0ae4b4d939b0927450f929e6c069ede9790a1f481e`.
- Offline preview: `controlled_publication_preview`, `remote_mutations: 0`; one published attempt; `token_revoked: true`.
