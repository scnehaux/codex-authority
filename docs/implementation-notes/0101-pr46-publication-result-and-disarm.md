# Codex PR #46 publication result and disarm

Recorded: 2026-10-25 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated App published the exact-candidate success check and revoked the installation token. The reviewed activation is closed by disabled state and null activation; the restored regression proves zero signing or network access while disabled. The durable attempt/outcome and permit/evidence/receipt are retained outside Git, never overwritten or replayed. No Governance 1.0 release or architecture admission is claimed.

- Check: [Codex Governance Authority 120984021092](https://github.com/scnehaux/codex/runs/120984021092)

```json
{
  "activation_digest": "dbede9f9294047208afb193af429bc963e7d198971716eb2bce71b41e96848d6",
  "candidate": {
    "base_sha": "db18d03440afa2097f926314df53749a5d2bd7aa",
    "head_sha": "9638a82b0dc40a6404dfbd5970a32c417810696f",
    "pull_request": 46,
    "repository": "scnehaux/codex"
  },
  "check_post_attempted": true,
  "check_run_id": 120984021092,
  "effective_enforcement_proven": false,
  "kind": "codex-publication-outcome",
  "permit_digest": "2efe141ed45eb3b36403411a548ddf70316b2ee7eadad54a9925fd002d55f9e7",
  "schema_version": 1,
  "status": "published",
  "token_revoked": true
}
```

- Codex PR [#46](https://github.com/scnehaux/codex/pull/46) squash merged at `86545a1324388fcc0777f7ca1f6ab1bcd2ab5def`, after all five exact-head checks were successful.
- Attestation: Authority [#111](https://github.com/scnehaux/codex-authority/pull/111), source `114997f37c12cc2e0cf28b0d3a15d23178b45d19`.
- Activation: Authority [#113](https://github.com/scnehaux/codex-authority/pull/113), merged `1a4c27f795952a30bb95bfed8501cce958baa63b`.
- Offline preview: `controlled_publication_preview`, `remote_mutations: 0`; one published attempt; `token_revoked: true`.
