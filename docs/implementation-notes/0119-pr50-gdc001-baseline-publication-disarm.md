# Codex PR #50: gdc001-baseline publication disarm

Recorded: 2026-11-01 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated App published exact-head success check [124666189317](https://github.com/scnehaux/codex/runs/124666189317) and revoked its installation token. The retained outcome is [the immutable candidate record](../../governance/publications/de7defe07c6aa0c7648e00c2fdcb129d4ecc5d5a.json), copied byte for byte from the sole durable journal outcome. The local attempt/outcome and permit/evidence/receipt stay outside Git and are never overwritten or replayed.

Restore disabled state and null activation. No standing publication capability, release, GDC approval or admission is granted.

- Codex [#50](https://github.com/scnehaux/codex/pull/50) squash merged at `785977e8afc4e2596a2d82c9e0aaf2bdb18e1be1`.
- Permit digest `39f8bd07a44807ab681993e221cd66d2bc9b7dc76ee585ed103eb4edb6ca96a4`; activation digest `b3221c722797867ab0ec9ca76c12b13fe80534bec92c04f3a316a32c830be6e0`.
- Offline preview: `controlled_publication_preview`, `remote_mutations: 0`; one published attempt; `token_revoked: true`.
- Sequence: owner ARB approval record #133 (GDC-001 1.0.0, merged before attestation), attestation #134, activation #135, this disarm. REC-13-003 order held.
