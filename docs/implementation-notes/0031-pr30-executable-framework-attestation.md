# PR #30 Slice 11.4 privileged attestation

Recorded: 2026-09-22 (Asia/Jakarta). Implementation-local, non-normative.

This attestation authorizes only Codex PR #30 at exact base
`c26a80d791be2c65b3b4c628435a1e4ee1fdc4c4` and exact head
`a4e8454588aed0a6393774141d09593c61298e0e`, with the complete sorted
25-path candidate manifest.

The candidate introduces the deterministic `FrameworkCompiler` and immutable
`ExecutableFramework` as the single runtime composition root for governed
framework semantics.

The candidate preserves the compiled semantic identity
`6f7e79c82aea1342d7f8eed9d2181383bb52b349f30af3cdf7ea3c609cf14980`
while changing authored contract activation to `executable-framework`.
Artifact and relationship fragment views remain compatibility projections only.

This record does not override qualification, source identity, candidate drift or
any non-privilege failure. Candidate code is not executed by Authority and
evaluation remains credential-free. Privileged bootstrap remains disabled.

After this attestation merges, only a fresh permanent-runtime PASS for this exact
head may produce evidence, receipt and permit. Publication remains a separate,
short-lived, digest-bound capability. Slice 11.4 does not claim later Phase 11
schema-boundary, ingestion, snapshot, extension-pack or compatibility work.
