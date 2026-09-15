# Stage D recommendation and decision ledger

Recorded: 2026-09-15 (Asia/Jakarta). Scope: Codex / Codex Authority maintenance.

This is an implementation-local, non-normative review record. It does not replace
Codex governance, the control registry, PLAN, ROADMAP, or the maintenance contract.
Normative architecture artifacts remain assigned to `scnehaux/codex-architecture`.
No runtime, attestation, promotion, publisher, provider rule, or enforcement claim
is changed by adding or accepting this documentation.

## Documentation direction and decision authority

On 2026-09-15 the project owner requested that recommendations grounded in best
practice, first principles, systems thinking, evolutionary architecture, or
operational experience be communicated and recorded, rather than left in chat.
This note captures that documentation direction and the initial recommendation set.
Approval to record recommendations is not approval to implement every proposal.

For subsequent work, read this ledger with the maintenance lifecycle before
changing the implementation. Communicate each material recommendation, including
corrections to earlier advice, to the project owner. Record its rationale,
applicability, alternatives, costs, plan impact, and validation criteria in the
same change or in an explicitly linked documentation change. Log deferred and
rejected suggestions too; do not silently lose them when the conversation ends.
An urgent safety stop can precede documentation, but not an unrecorded activation.

Use stable recommendation IDs. Keep decision status separate from evidence:

| Decision status | Meaning |
| --- | --- |
| Proposed | Recorded for review; not an implementation authorization. |
| Accepted | An identified authorized decision and its scope are linked. |
| Deferred | Reason, owner, and revisit trigger are recorded. |
| Rejected | Reason and relevant alternatives remain available. |
| Superseded | A replacement ID and the reason for changing direction are linked. |

Evidence is recorded separately as not assessed, source reviewed, locally tested,
CI tested, provider observed, or operationally observed, with exact scope and
links. These are descriptions, not automatic maturity scores. Acceptance does
not imply implementation; a passing test does not imply deployment.

Every entry inherits these initial metadata unless an explicit update overrides
them: **date 2026-09-15; proposer assistant; decision Proposed; decision owner
project owner; implementer/reviewer unassigned; new implementation evidence none;
next review before Stage D activation planning**. The numbered entries describe
review recommendations, including safeguards already present in the baseline.
They do not assert that every recommended safeguard is currently missing.

For later entries or updates, preserve this record shape:

```text
ID and title:
Recorded date and proposer:
Decision status, authorized decision owner, decision reference:
Observation (repository / exact revision / path) or explicit assumption:
Problem and invariant:
Recommendation and applicable review lenses:
Source references and their limits:
Alternatives, including doing nothing:
Benefits, costs, risks, and cross-component effects:
Existing-plan impact and dependencies:
Implementation owner and linked PR / commit:
Acceptance tests and evidence, including counterexamples:
Abort / rollback constraints:
Revisit trigger and supersedes / superseded-by links:
```

Significant adopted architecture changes must follow the existing governed
architecture/decision process when applicable. This lightweight ledger records
recommendations; it is not a second semantic authority or a newly admitted ADR
corpus. Preserve history through Git and dated transition entries; do not rewrite
historical evidence to make a proposal look previously accepted. The decision
recording approach is informed by [S1], without importing an alternative Codex
artifact taxonomy.

## Reviewed baseline and limits

The repository heads observed for this review were:

- Codex Authority: `ba90331fe31b401c613f81aaf3ceea3e11d045a2`, the merge of PR #12.
- Codex: `0f9dab0091746ac1232174c75ed6330b53dff750`, the merge of PR #18.

The existing [maintenance lifecycle][R1] stages a disabled one-candidate bootstrap,
adds the permanent reader in Codex, separately attests and activates one exact
candidate in Authority, records evidence before publication, merges through the
provider rules, and disarms the bootstrap. The [checked-in contract][R2] leaves
the permanent reader unimplemented and both maintenance-path and effective-
enforcement proof claims false.

Those goals remain the baseline. The recommendations below refine implementation,
verification, and operational handover; they do not reorder later Codex phases.
The prior [architecture note][R3] is explicitly non-normative and includes older
stage labels. Use revision-bound facts rather than assuming all prose describes
the same point in time. This review does not constitute a fresh live provider
negative test, deployment, independent human approval, or production audit.

## Review lenses and evidence discipline

**First principles:** derive a recommendation from the protected invariant and
threat model. State assumptions and why the smallest change preserves authority.
A derivation is reasoning, not a borrowed certification.

**Best practice:** identify the specific practice, primary source, and where it
fits this system. A familiar pattern is not automatically the right trade-off.

**Systems thinking:** inspect the complete evaluation-to-merge path, its external
dependencies, failure recovery, and operator behavior. Local component success
must not conceal a system-level deadlock or unsafe retry.

**Evolutionary architecture:** prefer reviewable increments, explicit promotion,
compatibility checks, and testable architectural constraints. [S3] motivates
incremental development and fitness functions; it does not prescribe this
repository's exact files or deployment topology.

**Operational experience:** distinguish a production-informed reference such as
[S4] or [S5] from evidence that this implementation works. Do not label Codex or
Authority "battle-tested" from those references, one successful proof, or a green
CI run. Any such claim needs a defined operating scope, duration, failures,
recovery observations, and evidence. No production maturity claim is made here.

## Initial recommendations

### REC-D-001 — Separate new source, promotion, and effective execution

**Observation and correction.** The current [Codex CI][R4] checks that the
working-tree runtime and evaluator still equal their historical promoted blobs.
The [Authority adapter][R5] independently pins the runtime source. Earlier advice
that a new entrypoint is mandatory was too strong: it is a proposed migration
option, not a requirement in PR #12. Editing a source path at a new revision does
not itself alter the historical Git object or automatically promote that source.

**Recommendation.** Preserve the current promoted execution package during the
bootstrap. Review an additive reader/entrypoint against a deliberate same-path
upgrade with an explicit promotion-contract migration. Prefer the smallest option
that keeps candidate qualification and effective authority separate. Never execute
unpromoted candidate code as the authority for that candidate. Test execution in
ordinary isolated development/CI is a different boundary from privileged execution.

**Trade-off and plan impact.** An additive entrypoint preserves existing pins but
adds packaging and retirement work. A same-path migration reduces duplicate
entrypoints but must reconcile the strict CI contract. Neither option authorizes
auto-promotion. This refines lifecycle steps 2 and 7; selection remains Proposed.

**Acceptance.** Show the old package can still evaluate the installing PR. After
merge, separately review exact new source/dependency identities, execute the
promoted package, and record the handover. No second bootstrap is the intended
outcome, not a guarantee before this migration is validated. Basis: [R1], [R4],
[R5], and our application of [S2]/[S3].

### REC-D-002 — Bind attestation reads to an Authority snapshot

**Recommendation.** Resolve the fixed Authority `main` reference to one exact
commit, then read the candidate attestation at that commit. Keep host, repository,
path family, method, size limits, and redirect policy constrained. Record the
Authority commit, attestation path, and content identity. Prove that the bytes
belong to the path at that commit; a matching digest alone is not proof of approval.
GitHub's content API supports a commit-valued `ref` [S6].

**Alternatives and cost.** Repeated reads from floating `main` are simpler but can
mix revisions. A commit-bound read adds a request and verification. It removes
that particular inconsistency, not every possible race or stale authorization.
Candidate freshness still requires its own checks before publication.

**Plan impact and acceptance.** Reader implementation detail, not a new authority.
Simulate Authority `main` moving during collection, wrong content identity,
redirects, malformed replies, and candidate base/head movement. None may yield an
unearned permit. Basis: [R1], [S6], and complete-mediation reasoning from [S2].

### REC-D-003 — Make the permanent reader's failure contract explicit

**Recommendation.** Verify contract version and exact repository, PR, base, head,
complete sorted unique touched paths, authority identity, scope, decision, and
strictly typed claims. Renames must include previous paths. Reject malformed or
ambiguous data; distinguish an absent approval from transport failure. Neither
absence nor a failed read grants approval. An attestation must never erase a
non-privilege failure or a failed candidate qualification.

**Alternatives and cost.** Permissive parsing and treating every failed read as
"not required" are easier to implement but conceal invalid inputs. Strict parsing
requires deliberate schema evolution and more negative tests. Keep governance
semantics owned by Codex; do not duplicate a permanent evaluator in Authority.

**Plan impact and acceptance.** Preserve [R1]/[R2], with explicit parser behavior.
Test wrong PR/repository/base/head, incomplete and reordered files, renamed paths,
unknown fields/version, wrong types, missing attestation, malformed JSON, failed
qualification, source failure, and the mixture of privilege and other failures.
Test unknown failures fail closed. This is a proposed fitness-function application
of [S2]/[S3], not a claim that those tests have run.

### REC-D-004 — Review compatibility across the complete publication chain

**Observation.** The current adapter checks an exact runtime-result field set [R5].
The publisher proof verifier is bound to the completed historical proof [R6].
Consequently, adding a reader or output field alone is not an end-to-end migration.

**Recommendation.** Inventory the reader, runtime envelope, Authority adapter,
evidence model, permit, publisher expected source revisions, export procedure,
and CI contracts together. Introduce new proof records additively, retaining the
old proof. Review compatibility or explicit version changes before promotion.

**Trade-off.** Broad rewrites enlarge the trusted change; ignoring dependent
contracts leaves a correct reader unusable. Prefer the smallest coherent migration,
not necessarily a single PR. A new entrypoint is not a substitute for this review.

**Plan impact and acceptance.** Clarifies the handover already required by [R1].
An integration test must carry an eligible candidate through the new verified
runtime to a permit accepted by the intended publisher. Wrong schema or source
identity must be rejected. Historical evidence must still verify. Lens: systems
thinking and evolutionary architecture, informed by [S3].

### REC-D-005 — Preserve the evidence chain before issuing capability

**Recommendation.** Verify that a durable record connects the original runtime
verdict, the exact attestation and its Authority revision, the authorized outcome,
and the permit digest. Where that linkage is absent, propose a compatible evidence
extension or bound sidecar. A digest printed only to a terminal is not sufficient
for the intended audit trail. Preserve the pre-authorization failure instead of
rewriting it as an original runtime PASS.

**Trade-off.** Additional evidence improves reconstruction but adds storage and
contract maintenance. Do not invent a signature scheme, external database, or
retention guarantee without a threat/operating requirement. Specify what durable
means for the actual sink and host. Keep credentials out of records.

**Plan impact and acceptance.** Strengthens evidence-before-publication in [R1].
Test evidence-write failures and process interruption; neither may produce a
usable success permit. Reconstruct one decision from retained identities and
records. Proposed before bootstrap use; current end-to-end linkage is not declared
proven by this note. Lens: first principles and systems thinking.

### REC-D-006 — Specify bootstrap exit, abort, and safe recovery

**Recommendation.** Record preconditions, exact candidate binding, operator,
activation observation, publication outcome, merge outcome, permanent promotion,
and disarm evidence. Define abort behavior for changed candidate identity,
qualification regression, interrupted execution, and missing evidence. After
candidate merge or abandonment, do not reuse that bootstrap for other maintenance.

**Trade-off.** Explicit checkpoints cost operational effort but make recovery
inspectable. Record an expiry/revocation decision before any broader use; an
append-only approval log alone does not define revocation. Additional lifecycle
states or expiry fields require a governed contract change, not prose-only edits.

**Plan impact and acceptance.** Elaborates [R1], leaving generic publication disabled.
Recovery should stop publication or restore a previously reviewed safe package,
not remove required checks or reopen a permanent bypass. A rollback to the old
runtime can restore fail-closed behavior without restoring maintenance availability;
record that limitation. Test interrupted activation, abandoned candidates, and
post-disarm rejection. Basis: [R1] and scoped rollout/recovery reasoning from [S5].

### REC-D-007 — Do not equate one candidate with one publication

**Recommendation.** Treat exact-candidate scope, one execution, one issued permit,
and one provider-side write as different properties. Preserve the existing
no-automatic-check-POST-retry behavior described in [R7]. An ambiguous network
failure needs reconciliation, not an assumption that the write failed. If
repeatable/hosted publication is introduced, specify durable deduplication,
concurrency ownership, and same-key/different-intent rejection first.

**Trade-off.** A serialized operator run is smaller but relies on disciplined
reconciliation. Automated replay control adds state and failure modes. Neither
an exact SHA nor a content digest is by itself an exactly-once mechanism. [S4]
informs this recommendation; it does not establish GitHub API idempotency.

**Plan impact and acceptance.** Record the current operating restriction before
live bootstrap use; stronger automation is a separately reviewed increment. Test
duplicate submissions, concurrent attempts, and a write that succeeds remotely
but loses its response. Never claim global exactly-once publication without proof.

### REC-D-008 — Prove both denial and a usable maintenance path

**Recommendation.** Pair negative checks with a positive post-handover proof:
with the bootstrap disabled, a separately attested future protected candidate can
use the promoted permanent reader, while an invalid candidate remains blocked.
A permanently blocked system can be safe against a merge yet unusable to maintain.

**Trade-off and plan impact.** This costs an additional controlled proof but detects
handover deadlocks hidden by unit tests. Map all applicable Phase 10 exit
obligations from [R8]/[R9]; do not assume deletion and non-fast-forward tests alone
complete every enforcement requirement. Keep observed mergeability, an attempted
operation's rejection, and successful authorized execution distinct in evidence.

**Acceptance.** Record exact candidate/source/check identities, the active rule
projection and observation time, and cleanup. Plan destructive tests only in an
explicitly approved disposable scope. Document how its rules correspond to the
default-branch policy and what the test does not prove. Never test deletion or
force updates on the protected production branch merely to gather evidence.
This is systems-level validation informed by [S5], not permission to run live
writes as part of this documentation change.

### REC-D-009 — Reconcile present-state prose without rewriting history

**Observation.** Codex [PLAN][R8] and [ROADMAP][R9] contain snapshots saying no live
ruleset is installed, while the newer Authority [README][R7] records provider
activation and partial proofs. The architecture note [R3] also uses an earlier
stage sequence. The reason those documents lag is not established; it should not
be asserted that every Markdown edit is blocked by privileged validation.

**Recommendation.** Reconcile current-status summaries through reviewed changes,
with observation date, revision, and evidence references. Distinguish desired
configuration, promoted implementation, installed provider state, and observed
behavior. Preserve immutable historical proof and its conservative self-report.

**Trade-off and acceptance.** A new master status database would create duplication;
prefer links to existing authorities. Verify each current-status claim against
its source and flag contradictions. Later automation may check selected summaries,
but this note does not introduce such enforcement. Plan impact: status repair,
not a new strategic roadmap. Lens: systems thinking and evidence traceability.

### REC-D-010 — Keep the trusted core small and evolution demand-driven

**Recommendation.** Keep reusable evaluation semantics in Codex and narrow
execution/evidence/publication orchestration in Authority. Use the same fixtures
and explicit contract tests at the boundary. Do not add a second general policy
engine, multi-repository platform, queue, or continuously hosted worker merely
because these exist in industry examples.

**Trade-off.** The current operator-driven path has availability and throughput
limits; distributed automation increases the trusted surface and operational
burden. Define a revisit trigger such as measured operator toil, required response
time, recovery behavior, or event-delivery requirements. No threshold is invented
or silently adopted here.

**Plan impact and acceptance.** Preserves the responsibility split in [R3]/[R7].
Review dependencies, import surfaces, duplicated policy, and package identities.
Show the Stage D increment solves its specific maintenance need before adding
hosting. Economy of mechanism [S2] and incremental fitness functions [S3] motivate
this recommendation; they do not prove the current code secure.

### REC-D-011 — Record the real administrative trust boundary

**Recommendation.** State who may change Codex candidates, Authority source and
attestations, effective deployment pins, provider rules, and publisher credentials.
Record independent human-review limitations separately from separation of code
and execution. A second repository or an approval-shaped JSON object does not
establish independent administration by itself.

**Trade-off.** Stronger human separation can constrain a small team. Preserve the
existing explicit review bootstrap rather than pretending multiple independent
reviewers already exist. Document residual risk and the governed exit condition;
any permission or review-policy change needs its own approved change.

**Plan impact and acceptance.** Clarifies an existing trust assumption, not a
request to alter access in this PR. Verify the relevant permission boundaries and
test that a candidate-only actor cannot select effective authority or publish the
required App check. Claims must identify what remains trusted, including the
privileged operator and provider. Source pinning and digests alone do not protect
against compromise of those roots. Basis: [R3]/[R7] and separation/least-privilege
reasoning from [S2].

## Adoption and plan-change rules

The next implementation review should resolve REC-D-001 through REC-D-006 and the
operating restriction in REC-D-007 before proposing live activation. REC-D-008
supplies acceptance planning, REC-D-009 supplies status reconciliation, and
REC-D-010/011 constrain scope and trust assumptions. These are review priorities,
not newly installed governance gates or replacements for existing controls.

Any accepted change to trust assumptions, ownership, lifecycle, schema,
compatibility, or phase dependencies needs an explicit plan-impact decision and
updates to the actual authoritative contracts through their normal review path.
Suggestions that are declined or postponed remain here with the explanation and
revisit trigger. Do not lower thresholds, fabricate evidence, or advance proof
flags to make a suggestion appear complete.

## Decision history

| Date | Record | Event | Technical authorization / evidence |
| --- | --- | --- | --- |
| 2026-09-15 | Documentation direction | Project owner requested communication and durable recording of recommendations. | Documentation requested; not blanket technical approval. |
| 2026-09-15 | REC-D-001 | Corrected earlier advice that a new runtime entrypoint is mandatory. | Migration choice remains Proposed. |
| 2026-09-15 | REC-D-009 | Corrected an unsupported causal explanation for stale status documents. | Cause not established; reconciliation Proposed. |
| 2026-09-15 | REC-D-001..011 | Initial recommendation set recorded for implementation review. | No new implementation, activation, or provider proof asserted. |

## Primary references and applicability

External pages were consulted on 2026-09-15. Their exact applicability is explained
in the entries; they are not certifications of this project.

- [S1] Michael Nygard, *Documenting Architecture Decisions* (2011): context,
  decision status, consequences, and retention of superseded decisions.
- [S2] Jerome Saltzer and Michael Schroeder, *Basic Principles of Information
  Protection*: small mechanisms, safe defaults, mediation, and privilege boundaries.
- [S3] *Building Evolutionary Architectures*, authors' site and Thoughtworks book
  overview: incremental change and architectural fitness functions.
- [S4] Malcolm Featonby, Amazon Builders' Library, *Making retries safe with
  idempotent APIs*: production-informed retry ambiguity and request identity.
- [S5] Google SRE Workbook, *Canarying Releases*: scoped evaluation, rollout
  observation, recovery, and limits of test-only confidence. Our controlled
  candidate proofs are an application of bounded rollout, not a claim to run
  Google's production canary system.
- [S6] GitHub REST documentation, *Repository contents*: commit-bound `ref` reads
  and returned content metadata; not proof of an authorization policy.

[S1]: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
[S2]: https://web.mit.edu/saltzer/www/publications/protection/Basic.html
[S3]: https://evolutionaryarchitecture.com/
[S4]: https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/
[S5]: https://sre.google/workbook/canarying-releases/
[S6]: https://docs.github.com/en/rest/repos/contents#get-repository-content

Additional author/publisher overview for [S3]:
https://www.thoughtworks.com/insights/books/building-evolutionaryarchitectures-second-edition

Repository references below are pinned to the reviewed revisions so subsequent
edits do not silently change this review's baseline.

[R1]: https://github.com/scnehaux/codex-authority/blob/ba90331fe31b401c613f81aaf3ceea3e11d045a2/docs/privileged-maintenance.md
[R2]: https://github.com/scnehaux/codex-authority/blob/ba90331fe31b401c613f81aaf3ceea3e11d045a2/governance/privileged-maintenance.json
[R3]: https://github.com/scnehaux/codex-authority/blob/ba90331fe31b401c613f81aaf3ceea3e11d045a2/docs/architecture.md
[R4]: https://github.com/scnehaux/codex/blob/0f9dab0091746ac1232174c75ed6330b53dff750/.github/workflows/governance-evaluator.yml
[R5]: https://github.com/scnehaux/codex-authority/blob/ba90331fe31b401c613f81aaf3ceea3e11d045a2/src/codex_authority/adapters/promoted_runtime.py
[R6]: https://github.com/scnehaux/codex-authority/blob/ba90331fe31b401c613f81aaf3ceea3e11d045a2/scripts/verify_publisher_proof.py
[R7]: https://github.com/scnehaux/codex-authority/blob/ba90331fe31b401c613f81aaf3ceea3e11d045a2/README.md
[R8]: https://github.com/scnehaux/codex/blob/0f9dab0091746ac1232174c75ed6330b53dff750/PLAN.md
[R9]: https://github.com/scnehaux/codex/blob/0f9dab0091746ac1232174c75ed6330b53dff750/ROADMAP.md
