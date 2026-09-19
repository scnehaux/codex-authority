# PR #24 status-reconciliation publication activation

Recorded: 2026-09-20 (Asia/Jakarta). Implementation-local, non-normative.

## Scope

This change enables one short-lived `attested-v2` publication activation for
Codex PR #24, a documentation-only Phase 10 status reconciliation candidate.
The permanent runtime evaluated the exact candidate after Governance
Qualification passed and produced durable evidence, receipt, and permit.

Exact bindings:

- candidate base: `362d5c072fe407c915e2307bc455720739b20154`
- candidate head: `3deeb147dc3cff647021357dfedf1fc3faf3bde4`
- authority service source: `854dbb0576473b53c3ef20d0bb5f3cbc6895ece3`
- publisher source: `854dbb0576473b53c3ef20d0bb5f3cbc6895ece3`
- permit digest: `ce6e0d96f83f452a591fa552655ee3242128368354b7c4ce13cf5c07f7fbc015`
- evidence SHA-256: `35a7cbe7e31b733a9eed2ae1b756597291990e23477438573681146a6d51bc01`
- receipt SHA-256: `35e45c7efce43f710eef60a51b23fa358a2ce1ed7e2ada98a6d07d51bab0b215`

Activation window:

- not before: `2026-09-19T20:03:58Z`
- expires at: `2026-09-19T20:17:58Z`

Bootstrap remains disabled and unbound; the permanent runtime remains promoted.
The activation grants only the separate credential-bearing publication capability
for this exact evidenced candidate. It does not alter provider rules or runtime
semantics.

`effective_enforcement_proven` remains `false`. PR #24 explicitly records the
remaining Phase 10 negative-evidence gaps rather than closing them by inference.
After successful App publication and governed merge, this activation must return
to disabled and unbound state through a reviewed Authority change.
