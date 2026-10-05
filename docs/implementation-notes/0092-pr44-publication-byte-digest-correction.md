# PR #44 publication byte-digest correction

Recorded: 2026-10-05 (Asia/Jakarta). Implementation-local, non-normative.

The first offline preview stopped at publication-activation-binding. The merged activation had canonical JSON content digests for evidence and receipt instead of the exact raw-byte digests returned by permit issuance and required by verify_bundle. No publisher credential was used, no publication journal attempt was created, and no check was posted. The blocked preview is preserved locally as ~/pr44/preview.json.

This correction replaces those two fields with exact file SHA-256 values, updates the exact-binding regression, and reviews a fresh 15-minute window. Candidate, permit, runtime, Authority service and publisher source pins are unchanged. A newly exported kit and successful offline preview are required before one write attempt.

```json
{
  "authority_service_source_revision": "11430d73f30ebd2282d966506d9ca1dae885c4f1",
  "candidate": {
    "base_sha": "043c1d51fd621428e59a5988cb383a857e690bd1",
    "head_sha": "2a8a25c763270baaec9e673dcb9c2f1944fad03f",
    "pull_request": 44,
    "repository": "scnehaux/codex"
  },
  "evidence_sha256": "e6aec52bd27f1248c4e3b7020b767c9c6dec6befc097e46f3d10b512a7db4855",
  "expires_at": "2026-10-05T07:52:12Z",
  "mode": "attested-v2",
  "not_before": "2026-10-05T07:37:12Z",
  "permit_digest": "a2e34b47bea44ba0dd391bbd9f714e8b352b3d08c5a1faefc6784f22ded9614d",
  "publisher_source_blobs": {
    "integrations/github-app-publisher/controlled_publisher.py": "b6abd17cab7ca6721de59810ae2f802c14b9a623",
    "integrations/github-app-publisher/publisher_contract.py": "4b2ab8d9a5da6bda794586b43255688d7dc961fe",
    "integrations/github-app-publisher/publisher_transport.py": "038522fe95710dd2e6192ded5e1d61a612eb0206",
    "integrations/github-app-publisher/requirements.txt": "2f756e9cdf32147dcb4112754fd490c7bd90e27b",
    "src/codex_authority/__init__.py": "31549232f3462478b5cb405ed8b5c02486e2a7f2",
    "src/codex_authority/adapters/__init__.py": "6be550d778b8c2ea22f72f625e1821f7e2a2b1b5",
    "src/codex_authority/adapters/attested_runtime.py": "3173a03d9c483a0a6cc573c90c2be668be393f52",
    "src/codex_authority/adapters/promoted_runtime.py": "93811e0dd541a48793eaabb487bea8fb8277be56",
    "src/codex_authority/attested_contract.py": "94457e76ed297936c528f4f959347a55e306d3fb",
    "src/codex_authority/attested_handover.py": "bca72f281b9fb20d89627eddbddcdf21f159ecf6",
    "src/codex_authority/controlled_evidence.py": "08beef826f1a51f41e869c0c51181a858b4f8c1a",
    "src/codex_authority/evidence.py": "516df07c873fc42328b490fe984ac90662d17395",
    "src/codex_authority/model.py": "66baa88d159bea10cf57ec15f411af88f3e283c1",
    "src/codex_authority/policy.py": "7ca36baf7b0f8d45a7db27eb15e027d8f5d20e61",
    "src/codex_authority/ports.py": "786cc0c28557f0f06b52250f1ab48f94e339d4f9",
    "src/codex_authority/privileged.py": "1a29d15a587d5bc5924e610351d3b10d102e1ff8",
    "src/codex_authority/publication.py": "340732d326e90637c6a1486ffd2f77068748da32",
    "src/codex_authority/service.py": "b4825af287dad112b7839616c88ba9a2f906d3b0"
  },
  "publisher_source_revision": "11430d73f30ebd2282d966506d9ca1dae885c4f1",
  "receipt_sha256": "3a6cabf7265caed3bf238654e8b8b2130cb60e286a7829344c5c045db57fc6e7",
  "runtime_package": {
    "blobs": {
      "attested_runtime.py": "c9a0c3bf2fd3c33be4deb1b1e5fc624d1b0b796a",
      "evaluator.py": "ab2f152c21bd6d6f22df21172c4d027035ff8c11",
      "promotion.json": "f8f67280baf1c8725f67592d015ff37be2c4a4c3",
      "runtime-promotion.json": "83658bf5a44d22804d1628074dd8f27a7047d68e",
      "runtime.py": "c59911e9c0800c917fed21e6f33f3181c3a61e60"
    },
    "entrypoint": "attested_runtime.py",
    "repository": "scnehaux/codex",
    "source_revision": "d835991afe6ada47a66d012a3ddc2c4350cd9ff8"
  }
}
```
