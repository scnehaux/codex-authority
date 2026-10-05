# Codex PR #45: runtime-authority-publication-disarm

Recorded: 2026-10-05 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated App published the exact-candidate success check and revoked its installation token. The reviewed activation is closed by disabled state and null activation; the disabled regression again proves zero signing or network access. Durable local attempt/outcome and permit/evidence/receipt are retained, never overwritten or replayed. Governance 1.0 release and architecture admission remain unclaimed.

- Check: [Codex Governance Authority 111729656469](https://github.com/scnehaux/codex/runs/111729656469)

- Codex [PR #45](https://github.com/scnehaux/codex/pull/45) squash-merged as `db18d03440afa2097f926314df53749a5d2bd7aa` after all five exact-head checks succeeded.
- Attestation: [Authority #108](https://github.com/scnehaux/codex-authority/pull/108), merge `0cadc6281024324a38009f16b1f3510c055b71ab`.
- Activation: [Authority #109](https://github.com/scnehaux/codex-authority/pull/109), merge `e2c01b05dedc7ecf8ae5eaf769f6a787e8b99a2c`.
- Authority/publisher source: `0cadc6281024324a38009f16b1f3510c055b71ab`.
- Evidence raw SHA-256: `fe25f9967f6a3316c5a235abef0e5df865d64b49d660d436967e794cabcfc6e6`.
- Receipt raw SHA-256: `3398c5e97917ee6e592b9c5bdaa43586c69b634df48eb987ab443e21a4f1ab8a`.

The Slice 13.3 implementation is governed and merged. REC-13-001 through REC-13-003 remain awaiting owner decisions; no approval was inferred from preparing this candidate.

```json
{
  "activation_digest": "8bb8fec49e257e4117c1d42ca6c3d68a0a77c17559a1a86baa2b76c71f4e8cb5",
  "candidate": {
    "base_sha": "4abb77f9aa84db31dac37fc10b3cfbcb507f2570",
    "head_sha": "8e2b8c088e484c0acc75255e2ebf95011b0fded4",
    "pull_request": 45,
    "repository": "scnehaux/codex"
  },
  "check_post_attempted": true,
  "check_run_id": 111729656469,
  "effective_enforcement_proven": false,
  "kind": "codex-publication-outcome",
  "permit_digest": "b0c377d9ae85af5eb375b35c920d6495543db795ab431209d5a441bac11fba2d",
  "schema_version": 1,
  "status": "published",
  "token_revoked": true
}
```
