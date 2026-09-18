# Permanent privileged-maintenance path proof

Recorded: 2026-09-18 (Asia/Jakarta). Implementation-local, non-normative.

## Proven observation

Codex PR #23 was the first protected maintenance candidate completed after the
bootstrap was disarmed and the permanent attested runtime was promoted.

The candidate changed only a comment in protected
`governance/scm/trust-boundary.yaml`; parsed policy semantics were intentionally
unchanged. Candidate Governance Qualification succeeded before Authority approval.

The promoted permanent runtime at Codex source
`d835991afe6ada47a66d012a3ddc2c4350cd9ff8` consumed the exact committed Authority
attestation for PR #23 while bootstrap remained disabled. It produced durable
version-2 evidence, a receipt, and a success-only publication permit.

The dedicated App then published `Codex Governance Authority` check run
`105585648922` for exact candidate head
`d681a8f311cbb3a0bc69b795639112918e57a85f`; provider observation confirmed App
ID `4864946`, successful conclusion, and the publication journal confirmed token
revocation. PR #23 merged normally as
`362d5c072fe407c915e2307bc455720739b20154`.

Durable repository evidence is stored at
`governance/evidence/permanent-maintenance-proof-001.json` and keeps the exact
candidate, runtime/service/publisher revisions, bundle digests, App observation,
ruleset binding, and merge commit.

## Decision and claims

REC-D-008 positive post-disarm liveness acceptance is now satisfied for the
privileged-maintenance path. REC-D-015 is now operationally adopted: the bootstrap
remained disabled throughout this proof and was not reactivated as fallback.

`privileged_governance_maintenance_path_proven` may therefore advance to `true`
only while the permanent runtime remains promoted and bootstrap remains disabled.
The loaders enforce that state relationship.

The completed candidate-scoped publication activation returns to `disabled` and
unbound immediately after the proof. The App credential remains a separate
publication boundary and is not available to the evaluator.

`effective_enforcement_proven` remains `false`. A working maintenance path is only
one enforcement obligation; the project must first map all applicable Phase 10
exit evidence, including provider-side destructive-rule guarantees where required,
before advancing that broader claim.

## Recovery and future evolution

The old bootstrap attestation and operational journals remain historical evidence
and are not deleted. They do not remain live capabilities. If the permanent path
later fails, recovery requires a new reviewed Authority change rather than an
implicit or standing bootstrap bypass.

This closes Stage D maintenance liveness, not every enforcement proof and not a
claim that the overall system is battle-tested. Operational confidence should
continue to grow through repeated legitimate maintenance, negative drift tests,
and explicit evidence retention rather than by widening bypasses or silently
relaxing source pins.
