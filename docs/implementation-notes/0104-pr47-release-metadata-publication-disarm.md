# Codex PR #47: release-metadata-publication-disarm

Recorded: 2026-10-26 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated App published exact-head success check [121288035795](https://github.com/scnehaux/codex/runs/121288035795) and revoked its installation token. The canonical retained outcome is [the immutable candidate record](../../governance/publications/f8a145d00a885d8c4d606550d4efa05b19c10846.json), copied byte-for-byte from the sole durable journal outcome. The local attempt/outcome and permit/evidence/receipt are retained outside Git and never overwritten or replayed. This structured outcome supports future release-metadata binding; it is not a Governance 1.0 manifest or GDC approval.

Restore disabled state and null activation; the regression again proves zero signing and network access. Admission stays closed and all pending roots remain visible. No standing publication capability or release is granted.

- Codex [#47](https://github.com/scnehaux/codex/pull/47) squash merged at `0582d15b4c77dbc3c7eab8314a22c4db6a1c6c49` after all five exact-head checks succeeded.
- Attestation: Authority [#116](https://github.com/scnehaux/codex-authority/pull/116), source `75f584da8af42a37e132bfc39da4aa2680c9b195`.
- Activation: Authority [#117](https://github.com/scnehaux/codex-authority/pull/117), merged `15f9255a12d104ee16d859a86136d009ff6392c5`.
- Offline preview: `controlled_publication_preview`, `remote_mutations: 0`; one published attempt; `token_revoked: true`.
