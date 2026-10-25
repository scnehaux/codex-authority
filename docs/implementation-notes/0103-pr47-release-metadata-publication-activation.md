# Codex PR #47: release-metadata-publication-activation

Recorded: 2026-10-26 (Asia/Jakarta). Implementation-local, non-normative.

The exact-head attestation is merged. The independently promoted runtime returned PASS on the ready-for-review candidate; all four candidate checks are successful. This fifteen-minute activation binds the candidate, runtime, exact publisher blobs, canonical permit digest and raw evidence/receipt digests. The isolated publisher venv is ready. After CI and merge, require offline preview, publish once, verify check and token revocation, then disarm. No release, GDC approval or admission is granted.

```json
{
  "authority_service_source_revision": "75f584da8af42a37e132bfc39da4aa2680c9b195",
  "candidate": {
    "base_sha": "86545a1324388fcc0777f7ca1f6ab1bcd2ab5def",
    "head_sha": "f8a145d00a885d8c4d606550d4efa05b19c10846",
    "pull_request": 47,
    "repository": "scnehaux/codex"
  },
  "evidence_sha256": "647ad975fa6b167b29c64650a33c9a4aa9c0b7222554f858ce5c8a718a876f41",
  "expires_at": "2026-10-25T21:05:46Z",
  "mode": "attested-v2",
  "not_before": "2026-10-25T20:50:46Z",
  "permit_digest": "2fd61913d637b89428e0f88339faef264d2ab7c81c787a259861d98bf501fc56",
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
  "publisher_source_revision": "75f584da8af42a37e132bfc39da4aa2680c9b195",
  "receipt_sha256": "bbe43b363b2fcef8f9a0d3842ff48cacfc3f59d530f42c7d1c8a1035f8802d4e",
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
