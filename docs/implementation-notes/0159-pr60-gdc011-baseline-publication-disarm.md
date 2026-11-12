# Codex PR #60: gdc011-baseline publication disarm

Recorded: 2026-11-12 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated App published exact-head success check [131133297867](https://github.com/scnehaux/codex/runs/131133297867) and revoked its installation token. The retained outcome is [the immutable candidate record](../../governance/publications/06f4ec41e6f533234931882382982f082f2278ac.json), copied byte for byte from the sole durable journal outcome. The local attempt/outcome and permit/evidence/receipt stay outside Git and are never overwritten or replayed.

Restore disabled state and null activation. No standing publication capability, release, GDC approval or admission is granted.

- Codex [#60](https://github.com/scnehaux/codex/pull/60) squash merged at `2e84573acd574ab7dfc076bc200a30938ab8b9e5`.
- Permit digest `4de3a396e1e2dd103732b91e9f9dfdb4ea944a262cdcc6f11ae7e7a5131f6ab0`; activation digest `c4bee7ed56924462e2eece05affd6e33ae146db97b1e85784a50af83f5d3cf6e`.
- Offline preview: `controlled_publication_preview`, `remote_mutations: 0`; one published attempt; `token_revoked: true`.
