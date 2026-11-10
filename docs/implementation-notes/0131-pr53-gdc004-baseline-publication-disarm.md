# Codex PR #53: gdc004-baseline publication disarm

Recorded: 2026-11-10 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated App published exact-head success check [129695436778](https://github.com/scnehaux/codex/runs/129695436778) and revoked its installation token. The retained outcome is [the immutable candidate record](../../governance/publications/3e10ea381becb55b7d581a8da14872a98ec94fb0.json), copied byte for byte from the sole durable journal outcome. The local attempt/outcome and permit/evidence/receipt stay outside Git and are never overwritten or replayed.

Restore disabled state and null activation. No standing publication capability, release, GDC approval or admission is granted.

- Codex [#53](https://github.com/scnehaux/codex/pull/53) squash merged at `7ab674aff330eefb3f74e835f966440f8da1153a`.
- Permit digest `d26e65efaeeb2e063e3a908d56d8c01f0cd9234c66f154d8b129ec5c2750aadf`; activation digest `4c6fd7e529e5794c7c8a0780d22bf681881e59329b59bf85fc5342435166e4f7`.
- Offline preview: `controlled_publication_preview`, `remote_mutations: 0`; one published attempt; `token_revoked: true`.
