# Privileged Codex governance maintenance

Stage D adds an independently administered approval boundary for protected changes in `scnehaux/codex`. It does not make the authority repository a second governance engine and it does not allow a candidate to choose its own authority.

## Permanent target

A protected Codex pull request is first evaluated by the already promoted, credential-free Codex runtime. Candidate identity, base/head SHAs, touched paths, and `Governance Qualification` provenance continue to come from fixed GitHub read-only endpoints. When that runtime fails only because privileged validation is missing, a separately reviewed attestation on `scnehaux/codex-authority/main` may authorize that exact candidate.

The attestation binds repository, PR number, base SHA, head SHA, and the complete sorted changed-file set. A later permanent Codex runtime slice will read that record from the public authority repository through a fixed read-only boundary and verify the exact binding before treating privileged validation as satisfied.

## Bootstrap constraint

The permanent reader cannot be introduced by silently weakening the current fail-closed runtime. The first protected Codex change therefore needs a one-candidate bootstrap controlled by `governance/privileged-maintenance.json`.

The bootstrap is disabled by default. When separately activated for one exact PR/head it may resolve only these existing privilege-gate failures:

- `privileged-validation-missing`
- `runtime-critical-mutation-requires-privileged-validation`

Any candidate qualification failure, identity mismatch, source mismatch, unexpected runtime result, or changed-file drift remains non-overridable. The bootstrap does not execute candidate code and evaluation remains credential-free.

A bootstrap PASS is still not a GitHub write capability. Durable authority evidence must be recorded first, then the existing success-only publication permit boundary is used. Remote check publication remains a separate candidate-scoped GitHub App proof step with exact source, permit, repository, PR, and head bindings.

## Lifecycle

1. Stage the disabled privileged-maintenance contract and bootstrap implementation in Authority.
2. Create the Codex candidate that implements the permanent public-read-only attestation path.
3. Review the exact candidate and merge an exact-head attestation plus candidate-specific bootstrap activation into Authority.
4. Run the bootstrap externally from clean Authority main against the exported promoted Codex runtime; record evidence and issue one publication permit.
5. Publish the valid `Codex Governance Authority` check through the existing candidate-scoped GitHub App publisher boundary.
6. Merge the protected Codex candidate through the active provider ruleset.
7. Disarm the bootstrap and record the proof. Future protected maintenance uses the permanent attestation reader, not the bootstrap.

Until that lifecycle completes, `privileged_governance_maintenance_path_proven` and `effective_enforcement_proven` remain false.

## Recommendation and decision traceability

Read the [Stage D recommendation and decision ledger](implementation-notes/0002-stage-d-recommendation-ledger.md)
when preparing the next implementation slice. It records the project owner's
request to communicate and retain material recommendations, their primary sources,
alternatives, plan impact, acceptance criteria, and subsequent decision history.
Proposed recommendations are not implementation authorization or proof. This
implementation-local note does not replace the lifecycle or governed contracts
above, and recording a recommendation does not activate the bootstrap.
