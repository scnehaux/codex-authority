# Phase 10 acceptance dossier: decision-ready evidence map

Prepared: 2026-09-21. Implementation-local, non-normative.
State: **Proposed; owner scope decision not recorded.**
Decision thread: [Authority issue #28](https://github.com/scnehaux/codex-authority/issues/28).

## What this increment completes

The evidence package is already integrated by PR #29. This increment connects the
remaining acceptance discussion to eight immutable evidence objects and all ten
unchanged Slice 10.10 obligations. It adds a machine-checked index, not another
runtime policy engine or a new provider experiment. Integration of this dossier
must not close issue #28 or imply acceptance of REC-D-018.

Authority baseline: `c21caa337fc70c44feef9f4920658e641c31a970`.
Codex baseline: `107f0dc53e873ef6d24a9f12cd28da7348f79331`.
The JSON index is [phase10-acceptance-dossier-001.json](../../governance/evidence/phase10-acceptance-dossier-001.json).
Its inventory pins each source path and Git blob at the Authority baseline.
Historical evidence and its original false claims are not rewritten.

## Proposed REC-D-018 decision, not an approval already granted

The recommendation remains to evaluate a composition of:

1. Actual production qualification, independent runtime refusal, App-bound
   negative observations and governed positive maintenance paths.
2. Causally controlled disposable behavior, with the copied rules and repository,
   selector, transport and actor differences explicitly identified.
3. Current production source and configuration observations, separately from the
   behavioral experiments and any later owner acceptance.

This is a proposed evidence-method decision, not a waiver of the ten obligations.
The complete-mirror setup still returned `Invalid integration ids`; no record may
turn that result into PASS. In particular, the original acceptance-plan row for
direct push asks for a complete mirror. Its replacement by composed evidence needs
an explicit owner scope-transfer decision. A generic instruction to continue work,
a green artifact test or a merged documentation PR is not that decision.

First principles: establish that the operation is valid using a positive control,
then identify the control responsible for refusal. Systems thinking: candidate
qualification, trusted evaluation, permit issuance, App publication and provider
merge enforcement are separate boundaries. Evolutionary architecture: reuse those
small verified boundaries rather than expand the production App installation just
to reproduce a test topology. These apply REC-D-016/017 and the REC-D-018 proposal.

Trade-off: the composition does not exercise every interaction in one identical
repository. Current rule layering, privileged access, source identity and bootstrap
applicability therefore need their own preflight. Rejected alternatives are a
synthetic production Authority success, treating unknown outcomes as proof, a
risky production deletion, and presenting two accounts as two independent people.

## Ten-row review map

Evidence identifiers below resolve through the pinned JSON inventory. All rows are
**evidence mapped, not accepted**. The detailed original observations remain in
notes 0015, 0016 and 0017 and their immutable evidence files.

| # | Unchanged obligation | Evidence and remaining scope judgment |
| --- | --- | --- |
| 1 | Direct push to main rejected | `native_git` supplies actual Git rejection on a disposable default branch and an allowed control; `isolated` adds REST control evidence. This is not a Git push against production main or an admitted complete mirror. |
| 2 | Force push rejected | `native_git` and `isolated` supply genuine non-fast-forward denials and allowed controls. Copied rule on another repository/ref; no destructive production attempt. |
| 3 | Default branch deletion rejected | `isolated` distinguishes the REST native default guard from the custom deletion negative/positive pair. `native_git` explicitly leaves native Git default deletion unobserved. |
| 4 | Failing governance qualification cannot merge | `qualification` and `runtime` link the real PR #25 check failure to FAIL, no permit and a normal merge refusal. Two production checks were unmet; `isolated` supplies causal status-control evidence, with separate missing/wrong-source production observations. |
| 5 | Review behavior matches active bootstrap | `isolated` records zero-review squash; `maintenance` supplies a governed positive path. `stale_review` does not establish independent human review. The review exception stays active. |
| 6 | Unresolved thread blocks merge | `isolated` holds the candidate fixed: denial before resolution, allowed squash afterward. Copied isolated PR rule, not all production gates at once. |
| 7 | Stale review handling matches policy | `stale_review` links the actual approval and dismissal to the reviewable new commit. This is account-level behavior; zero required approvals does not mean dismissal blocks merge. |
| 8 | Only allowed merge method accepted | `isolated` records merge/rebase denial while repository settings allow both, followed by same-candidate squash. The PR rule supplies the restriction. |
| 9 | Desired/effective drift is zero | Historical observer evidence is ALIGNED. The current connector re-read source main, the full named ruleset and inherited listing, but not every effective/legacy endpoint; complete final preflight remains required. |
| 10 | Provider configuration cannot redefine neutral semantics | Pinned Codex PLAN/policy anchors, exact-main CI below, `wrong_source` and `maintenance` support distinct semantic and execution boundaries. Provider configuration alone does not prove this. |

The review bootstrap (zero mandatory approvals while independent qualified
reviewers are insufficient) is not the privileged-maintenance bootstrap, which is
already disabled. This dossier neither terminates the review exception nor
reactivates privileged maintenance bootstrap or standing publication.

## Source qualification gap narrowed without rewriting a failed local test

A connector read located the **existing push CI for exact Codex main**
`107f0dc53e873ef6d24a9f12cd28da7348f79331`: Scnehaux Governance run
`35466444121`, Governance Qualification job `105959532913`.
The job and the `Qualify governance control plane` step completed successfully.
The SCM trust, neutral-policy and provider-projection steps also succeeded.
[Exact-main job](https://github.com/scnehaux/codex/actions/runs/35466444121/job/105959532913).

This is newly re-read historical CI, not a new test execution. It supplies an
exact-source qualification reference distinct from the deliberate PR #25 failure.
The earlier operator pytest invocation missing `pygments` remains a failed local
attempt; it is not retroactively relabeled or fixed by another environment's result.
CI success also does not certify the adequacy of this acceptance composition.

## Current read-only recheck and its limits

The GitHub connector re-read Codex main at the baseline, default branch `main`,
active ruleset `23193929`, no bypass actors, App integration `4864946`, zero required
approvals, stale-dismissal and thread-resolution settings, and squash-only PR-rule
merge policy. Repository settings separately allow all three merge methods.
The inherited-inclusive listing returned only ruleset `23193929`.
The three fixture IDs `1377645819`, `1377674304` and `1378442804` were re-read as
archived. These are selected metadata observations, not new cleanup operations.

Desktop Commander reported no connected device during this continuation. The
connector rejected the effective branch-rules endpoint as unsupported; legacy
branch protection was not freshly read through an admin path. The Codex observer
was not rerun. Consequently `complete_live_preflight` remains false. The connector
responses used here did not expose HTTP capture timestamps or request IDs; the
preparation date is not a fabricated provider timestamp and the reads are not an
atomic snapshot. No broader permission or App installation was requested.

## Tests and publication boundary

`tests/test_phase10_acceptance_dossier.py` checks the ten-row index, source names,
exact local Git objects, selected cross-evidence identities, runtime wire checksum,
original missing-review history, cleanup identities and explicit non-claims.
Its Git subprocesses only read eight size-bounded immutable objects using
`cat-file`; there is no network, credential helper or ref mutation. Parsed working
JSON data is compared to the committed data, so checkout line endings do not
rewrite embedded runtime wire bytes or weaken a historical source verifier.

Ten index/mutation tests passed in the ChatGPT sandbox. The seven source-linkage
tests require the actual repository's pinned objects and are delegated to the
unchanged Authority CI. No operator-machine test run or new complete local suite
is claimed. Actual CI outcomes belong in the PR verification comment after they
are observed. Green tests validate this proposed record, not an owner signature.

## Bounded finalization after the owner decision

The next decision is whether the owner accepts REC-D-018's scoped evidence method
and its explicitly stated transfer limits. A rejection keeps the affected rows
open; a method approval alone still does not advance the phase.

After a recorded method decision, re-read current source, runtime/publisher policy,
full applicable provider state and cleanup identities through the authorized
read-only path. Resolve material drift or unavailable observations before making
an acceptance claim. Review each row against its actual evidence and applicability.
Then record a separate, source-bound acceptance result and use the normal governed
PR/check path for any Codex PLAN/ROADMAP or operational-contract finalization.
Do not globally flip historical runtime or packaging self-report flags.

`effective_enforcement_proven` remains false in this increment. Issue #28 stays
open. A future acceptance record should identify the decision actor and record,
accepted scope, evidence/source identities, preflight time and invalidation events.
Changes to policy, App source, runtime, review exception, role or provider behavior
require reassessment; this is not a standing publication permission.

## Primary references

- [Codex PLAN at the source baseline](https://github.com/scnehaux/codex/blob/107f0dc53e873ef6d24a9f12cd28da7348f79331/PLAN.md)
- [Provider-neutral policy at the source baseline](https://github.com/scnehaux/codex/blob/107f0dc53e873ef6d24a9f12cd28da7348f79331/governance/scm/enforcement-policy.yaml)
- [GitHub rule layering](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [GitHub review, status-source and force-push rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)

GitHub documents that applicable rules layer and that checks can be source-bound.
Those mechanism descriptions motivate the separate preflight; they do not certify
this project's evidence transfer or replace the owner decision.
