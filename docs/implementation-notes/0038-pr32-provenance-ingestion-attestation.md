# PR #32 Slice 11.6 privileged attestation

Recorded: 2026-09-24 (Asia/Jakarta). Implementation-local, non-normative.

This record authorizes only Codex PR #32 at exact base
`bfea97e841616a2880e28d2cfa177712209520f6` and exact head
`fa733509974b048c587e9066690cfa7267313b77`, with its complete sorted
18-path candidate manifest. It follows the operator's instruction to continue
submission and the established protected Authority PR path. No separate human
review, broad owner design approval, or standing publication authority is claimed.

The reviewed scope adds immutable Git repository/source provenance and preserves
source bindings through candidate assembly. Exact commit blobs, raw-byte SHA-256,
namespace, paths, ignore policy, Git replacement/environment isolation, malformed
inputs and provenance mismatches are covered by the candidate tests. Repository
identity and namespace are caller bindings, not authenticated remote ownership.

Independent clean-checkout qualification passed 1075 tests with 98.59% total
coverage and at least 95% per file, with all canonical gates and actual-base and
Genesis committed-delta checks. GitHub Governance Qualification check
`107343701998` succeeded on the exact candidate head.

The promoted permanent runtime `d835991afe6ada47a66d012a3ddc2c4350cd9ff8`
was exported from exact verified Git blobs and executed by clean Authority main
`fbadadd78d7a353dfc2b4d62d90628c56e50e5bc`. It independently collected the
candidate and qualification facts, then failed only with
`runtime-critical-mutation-requires-privileged-validation` because this candidate's
attestation was absent. The original negative evidence is retained locally; its
runtime-result SHA-256 is
`f848b7b66e5a722de3c5bb48f5b7b1baefcc8c5f717a65c7ca457612f833552c`.

This append-only record does not override qualification, candidate/source identity,
changed-file drift, or any non-privilege failure. Candidate code is not executed by
Authority. Evaluation remains credential-free and privileged bootstrap remains
disabled. This PR does not enable publication or promote a runtime.

A fresh permanent-runtime PASS after this record is merged must precede durable
evidence, receipt and permit, separately gated short-lived publication, and normal
Codex merge. ValidatedRepositorySnapshot remains Slice 11.7. Canonical knowledge
and architecture admission remain closed; Governance 1.0 is not claimed.
