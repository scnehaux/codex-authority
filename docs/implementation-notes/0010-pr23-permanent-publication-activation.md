# PR #23 permanent-path publication activation

Recorded: 2026-09-18 (Asia/Jakarta). Implementation-local, non-normative.

## Scope

This change enables one short-lived `attested-v2` publication activation for the
first post-disarm protected maintenance candidate, Codex PR #23.

The permanent runtime already produced durable version-2 evidence, a linking
receipt, and a permit while bootstrap remained disabled.

Exact bindings:

- candidate base: `d835991afe6ada47a66d012a3ddc2c4350cd9ff8`
- candidate head: `d681a8f311cbb3a0bc69b795639112918e57a85f`
- authority service source: `586b6e589ac941fec84a5f74328ad72ab7b039c9`
- publisher source: `586b6e589ac941fec84a5f74328ad72ab7b039c9`
- permit digest: `bd6c7f8afb76554a4afb7a1920dcebb660a66f373bea313cea27371f02d7972d`
- evidence SHA-256: `995b9a9c3781647ca9286fc8c969629ecbfccb4e891bc3f83a02d643ed92f37d`
- receipt SHA-256: `5f23e6421ba1a2f3bfb3bb2de657adc8d6c303e065b13697330932ebc0901535`

Activation window:

- not before: `2026-09-18T11:36:03Z`
- expires at: `2026-09-18T11:50:03Z`

Bootstrap remains disabled and unbound. `governance/attested-handover.json` remains
bound to merged permanent runtime source `d835991...`; this activation grants only
the separate credential-bearing publication capability for the exact evidenced
candidate.

The publisher must revalidate the full v2 runtime result, Authority attestation,
qualification identity, evidence/receipt/permit links, exact open PR identity,
and complete publisher source closure before key access and the single check POST.

A successful source-bound check followed by normal PR #23 merge is the required
positive post-disarm liveness observation. Afterward this activation must return
to disabled, and the maintenance-path claim may be advanced only with durable
provider evidence of that success.

`effective_enforcement_proven` remains outside this activation and requires the
remaining applicable Phase 10 evidence.
