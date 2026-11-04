# Codex PR #52: gdc003-baseline publication disarm

Recorded: 2026-11-04 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated App published exact-head success check [126605602188](https://github.com/scnehaux/codex/runs/126605602188) and revoked its installation token. The retained outcome is [the immutable candidate record](../../governance/publications/0c992ccdd9a961082d0ff87e4b5635a1a45ce7a0.json), copied byte for byte from the sole durable journal outcome. The local attempt/outcome and permit/evidence/receipt stay outside Git and are never overwritten or replayed.

Restore disabled state and null activation. No standing publication capability, release, GDC approval or admission is granted.

- Codex [#52](https://github.com/scnehaux/codex/pull/52) squash merged at `6e016957eb4ce5d883940d787952a234ff2189cc`.
- Permit digest `65183d447cea8997c702a2e89603947b83d9539efa39b7295617cda7aea61339`; activation digest `cbd4358e649f79c8244ad84c55be098f029adb819b574d0edbb7a54b9645ffea`.
- Offline preview: `controlled_publication_preview`, `remote_mutations: 0`; one published attempt; `token_revoked: true`.
