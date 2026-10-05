# PR #44 blocked publisher attempt and disarm

Recorded: 2026-10-05 (Asia/Jakarta). Implementation-local, non-normative.

The corrected offline preview succeeded. The subsequent attempt was blocked before any check POST because the system isolated Python lacked PyJWT and cryptography. No installation token was issued by that dependency failure. The attempt and outcome are retained at ~/pub44-corrected/publication-state; they are not removed or reused. The default publisher venv independently passed exact dependency-version checks and zero-network signing preflight. The PR was marked ready for review before any fresh activation. This change closes the failed activation before fresh permit issuance.

```json
{
  "activation_digest": "d33a28d64eb84b43a2872b6b424621500b5641468651fc8b612ee9a86848ab83",
  "candidate": {
    "base_sha": "043c1d51fd621428e59a5988cb383a857e690bd1",
    "head_sha": "2a8a25c763270baaec9e673dcb9c2f1944fad03f",
    "pull_request": 44,
    "repository": "scnehaux/codex"
  },
  "check_post_attempted": false,
  "check_run_id": null,
  "effective_enforcement_proven": false,
  "kind": "codex-publication-outcome",
  "permit_digest": "a2e34b47bea44ba0dd391bbd9f714e8b352b3d08c5a1faefc6784f22ded9614d",
  "schema_version": 1,
  "status": "blocked_before_check_post",
  "token_revoked": false
}
```

This change sets state disabled and activation null and restores the checked-in disabled regression. Slice 13.2 stays ACTIVE; Governance 1.0 release and architecture admission are not claimed.
