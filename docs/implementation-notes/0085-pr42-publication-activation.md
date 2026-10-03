# PR #42 Phase 13 planning controlled publication activation

Recorded: 2026-10-04 (Asia/Jakarta). Implementation-local, non-normative.

After Codex PR #42's Phase 13 planning commit was rebased onto merged Phase 12 closure, all four candidate checks succeeded. Authority PR #96 independently recorded the exact two-path attestation. The promoted credential-free runtime returned PASS and recorded the source-bound evidence, receipt and permit below.

```json
{
  "mode": "attested-v2",
  "candidate": {
    "repository": "scnehaux/codex",
    "pull_request": 42,
    "base_sha": "a57460d8eca6da44e1388f698546c6301541dada",
    "head_sha": "cae9230814ba770911703f1a15a218b44fc9b255"
  },
  "runtime_package": {
    "repository": "scnehaux/codex",
    "source_revision": "d835991afe6ada47a66d012a3ddc2c4350cd9ff8",
    "entrypoint": "attested_runtime.py",
    "blobs": {
      "attested_runtime.py": "c9a0c3bf2fd3c33be4deb1b1e5fc624d1b0b796a",
      "runtime.py": "c59911e9c0800c917fed21e6f33f3181c3a61e60",
      "evaluator.py": "ab2f152c21bd6d6f22df21172c4d027035ff8c11",
      "promotion.json": "f8f67280baf1c8725f67592d015ff37be2c4a4c3",
      "runtime-promotion.json": "83658bf5a44d22804d1628074dd8f27a7047d68e"
    }
  },
  "authority_service_source_revision": "3ef3eac455e3533c06f9c43b2cd16b779af01560",
  "publisher_source_revision": "3ef3eac455e3533c06f9c43b2cd16b779af01560",
  "publisher_source_blobs": {
    "src/codex_authority/__init__.py": "31549232f3462478b5cb405ed8b5c02486e2a7f2",
    "src/codex_authority/model.py": "66baa88d159bea10cf57ec15f411af88f3e283c1",
    "src/codex_authority/ports.py": "786cc0c28557f0f06b52250f1ab48f94e339d4f9",
    "src/codex_authority/policy.py": "7ca36baf7b0f8d45a7db27eb15e027d8f5d20e61",
    "src/codex_authority/service.py": "b4825af287dad112b7839616c88ba9a2f906d3b0",
    "src/codex_authority/publication.py": "340732d326e90637c6a1486ffd2f77068748da32",
    "src/codex_authority/evidence.py": "516df07c873fc42328b490fe984ac90662d17395",
    "src/codex_authority/privileged.py": "1a29d15a587d5bc5924e610351d3b10d102e1ff8",
    "src/codex_authority/attested_contract.py": "94457e76ed297936c528f4f959347a55e306d3fb",
    "src/codex_authority/attested_handover.py": "bca72f281b9fb20d89627eddbddcdf21f159ecf6",
    "src/codex_authority/controlled_evidence.py": "08beef826f1a51f41e869c0c51181a858b4f8c1a",
    "src/codex_authority/adapters/__init__.py": "6be550d778b8c2ea22f72f625e1821f7e2a2b1b5",
    "src/codex_authority/adapters/promoted_runtime.py": "93811e0dd541a48793eaabb487bea8fb8277be56",
    "src/codex_authority/adapters/attested_runtime.py": "3173a03d9c483a0a6cc573c90c2be668be393f52",
    "integrations/github-app-publisher/controlled_publisher.py": "b6abd17cab7ca6721de59810ae2f802c14b9a623",
    "integrations/github-app-publisher/publisher_contract.py": "4b2ab8d9a5da6bda794586b43255688d7dc961fe",
    "integrations/github-app-publisher/publisher_transport.py": "038522fe95710dd2e6192ded5e1d61a612eb0206",
    "integrations/github-app-publisher/requirements.txt": "2f756e9cdf32147dcb4112754fd490c7bd90e27b"
  },
  "permit_digest": "0e4870ba14feecfdc6feebde460db85e2debdc8630a3f9c2b8ba6038ac7e22e4",
  "evidence_sha256": "886f83d85a72c099789cb119279ae8d9a7ce88ddf6becfa421e305b003f349dc",
  "receipt_sha256": "e01dc22727258a3c679976db6592f59951b8f33cbfe5321047cdecd978f4729a",
  "not_before": "2026-10-03T18:18:16Z",
  "expires_at": "2026-10-03T18:33:16Z"
}
```

This enables one short-lived designated publisher attempt. App-source verification, qualification freshness, exact PR identity, source pin checks, durable journal and token revocation remain required. Disable publication after the attempt. Recommendations remain awaiting owner decisions; Governance 1.0 remains NOT READY and architecture admission CLOSED.
