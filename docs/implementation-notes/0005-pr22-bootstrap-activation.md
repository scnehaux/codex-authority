# PR #22 candidate-scoped bootstrap activation

Recorded: 2026-09-18 (Asia/Jakarta). Implementation-local, non-normative.

## Scope and decision

This change activates the already reviewed one-candidate bootstrap only for
`scnehaux/codex` PR #22 at exact head
`eaa5b41cd84fcc77fd1ff464120d4be83c57d1cd`, base
`0f9dab0091746ac1232174c75ed6330b53dff750`, with the complete sorted
three-path changed-file set recorded in the matching append-only attestation.

The activation does not publish a GitHub check, enable generic publication,
promote the candidate runtime, or advance either enforcement proof claim.
`governance/controlled-publication.json` and the attested-runtime handover
remain disabled until actual evidence, receipt, and permit digests exist.

## First-principles and lifecycle rationale

This is the narrow bootstrap described by the existing maintenance lifecycle:
the old promoted runtime remains the evaluator for the installing candidate,
while independent Authority state supplies only exact privilege authorization.
Candidate code does not become authority over itself.

The prior invariant that checked-in bootstrap state is disabled is intentionally
replaced for this temporary slice by a stronger exact-candidate assertion.
The unit test permits only PR #22 and its exact head; it does not make arbitrary
enabled bootstrap state acceptable.

## Exit and recovery conditions

After PR #22 is either merged or abandoned, this bootstrap must be disarmed by a
reviewed Authority change. The attestation remains append-only historical
evidence and must not be edited or deleted.

Before publication, the controlled issuer must run from clean Authority main,
retain the original runtime FAIL plus attestation and policy evidence, and create
a receipt before exporting a permit. A separate short-lived controlled
publication activation must bind the actual evidence, receipt, and permit
digests; guessed future digests are forbidden.

Any candidate drift, failed qualification, non-privilege failure, evidence-write
failure, source mismatch, or publication ambiguity stops the flow. Required
provider checks are never removed or bypassed as recovery.

This applies REC-D-006 and REC-D-013 to the live bootstrap preparation. It is
not a claim of battle-tested operation or Stage D completion.
