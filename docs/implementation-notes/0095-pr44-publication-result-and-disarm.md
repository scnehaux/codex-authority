# PR #44 publication result and disarm

Recorded: 2026-10-05 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated GitHub App published a success check on the exact still-open Codex PR #44 head. Installation-token revocation is proven. The PR is ready for review; this disarm does not merge Codex or withdraw its immutable check. The successful preview and publisher report are retained at ~/pr44-renewed, and the durable attempt/outcome at ~/pub44-final/publication-state.

- Check: [Codex Governance Authority 111666125699](https://github.com/scnehaux/codex/runs/111666125699)
- App ID: `4864946`; conclusion: `success`
- Attestation: Authority PR #102, merge `11430d73f30ebd2282d966506d9ca1dae885c4f1`
- Fresh activation: Authority PR #106, merge `afe61a63b7f4672b5b2660555ca37e5fa120030a`
- Authority/publisher source: `71c29e808492f494ac5f0fa18a19537db49922da`
- Evidence SHA-256: `29a4080ad4cfebe76add3fddd0f781c829e831ca0ecfc3c42d75ca43cfdb3beb`
- Receipt SHA-256: `a42ea1f33b51d76e70ce8ee41254817585d4802a36dd74df22b0de3843e51a42`

```json
{
  "activation_digest": "6415923961d4231e396721b8385b7313201537f2567cf963f98d2b98677f80c7",
  "candidate": {
    "base_sha": "043c1d51fd621428e59a5988cb383a857e690bd1",
    "head_sha": "2a8a25c763270baaec9e673dcb9c2f1944fad03f",
    "pull_request": 44,
    "repository": "scnehaux/codex"
  },
  "check_post_attempted": true,
  "check_run_id": 111666125699,
  "effective_enforcement_proven": false,
  "kind": "codex-publication-outcome",
  "permit_digest": "de06691d54924b7325f629de10aa235acdaef0977dfd6c0897de995d6ced638d",
  "schema_version": 1,
  "status": "published",
  "token_revoked": true
}
```

This change sets state disabled and activation null and restores the checked-in disabled regression. Slice 13.2 stays ACTIVE; Governance 1.0 release and architecture admission are not claimed.
