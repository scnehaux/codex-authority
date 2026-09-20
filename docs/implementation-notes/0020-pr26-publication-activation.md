# Codex PR #26 status-closure publication activation

This is one short-lived, exact-candidate publication capability after current
Governance Qualification succeeded and the promoted credential-free runtime
produced durable evidence, receipt and permit. It does not itself close Phase 10.
The scoped acceptance record is separate. Bootstrap remains disabled.

The disabled-config negative test is retained with an explicit disabled fixture;
the checked-in state assertion binds only this exact candidate and bundle.
After publication and normal merge, return the configuration to disabled/unbound.
Do not retry an ambiguous POST; preserve its attempt and outcome journal.

Exact reviewed activation (source objects included in governance configuration):

```json
{
  "mode": "attested-v2",
  "candidate": {
    "repository": "scnehaux/codex",
    "pull_request": 26,
    "base_sha": "107f0dc53e873ef6d24a9f12cd28da7348f79331",
    "head_sha": "07a393a24c29d19de8da703c49e22a1ce30f6b51"
  },
  "authority_service_source_revision": "360d9729310bf2903f4456f5b4464aaac17f873a",
  "publisher_source_revision": "360d9729310bf2903f4456f5b4464aaac17f873a",
  "permit_digest": "51a00232ede8227ef287af873256ca014d8721c83d837a16c4467ed36af7aa93",
  "evidence_sha256": "949d31463a22b75b6fdd9d4db07a496c1d21f06bcae85dd2249740a6e8c52247",
  "receipt_sha256": "f864e570fc91855de79d0f3373cd350624e2603668ed71b5ca01db3ac4e63415",
  "not_before": "2026-09-20T20:19:29Z",
  "expires_at": "2026-09-20T20:33:29Z"
}
```

The prior 5bcff61 candidate was corrected during final diff review before any
activation merge or publication. Its bundle is retained as superseded, not reused.
This exact new head passed qualification and received a new evidence/receipt/permit.
