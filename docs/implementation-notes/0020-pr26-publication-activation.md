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
    "head_sha": "5bcff612189cf36fb66d771259f6964c3667884b"
  },
  "authority_service_source_revision": "360d9729310bf2903f4456f5b4464aaac17f873a",
  "publisher_source_revision": "360d9729310bf2903f4456f5b4464aaac17f873a",
  "permit_digest": "84d3f4749e1204661e417cf034dc514ec1128369b57b66d620a3448cbd15cab3",
  "evidence_sha256": "abd7eb679d2b15c5e8c903e0d0a50e4a95e941a7ae0a0c85c796798609ae639c",
  "receipt_sha256": "369fd2935407cce0e49181f4657b81dfc71e835c3f5ddb84e8f0691d16fda0c3",
  "not_before": "2026-09-20T20:16:12Z",
  "expires_at": "2026-09-20T20:30:12Z"
}
```
