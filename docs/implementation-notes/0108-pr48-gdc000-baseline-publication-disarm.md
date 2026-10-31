# Codex PR #48: GDC-000 baseline publication disarm

Recorded: 2026-10-31 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated App published exact-head success check [124511720935](https://github.com/scnehaux/codex/runs/124511720935) and revoked its installation token. The retained outcome is [the immutable candidate record](../../governance/publications/f01908ef03e361b60b5b298c75378d5ee60c53b3.json), copied byte for byte from the sole durable journal outcome. The local attempt/outcome and permit/evidence/receipt stay outside Git and are never overwritten or replayed.

Restore disabled state and null activation. No standing publication capability, release, GDC approval or admission is granted.

- Codex [#48](https://github.com/scnehaux/codex/pull/48) squash merged at `a8ea1e313000883a5186db8d7e0675c6e2ce00f5`.
- Permit digest `e180a3cb9297c6647f1a080a89b447fdd6c40074d0e7ea9bbe748fc88ca05667`; activation digest `b581db0c1da4078d3edfd57b1e495c4339899fc1f176ad7f980c7a7e98f64450`.
- Offline preview: `controlled_publication_preview`, `remote_mutations: 0`; one published attempt; `token_revoked: true`.
