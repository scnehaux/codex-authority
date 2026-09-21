# Scnehaux Codex Authority

Independent governance authority runtime for `scnehaux/codex`.

This repository owns the trusted execution and publication boundary that will
run a promoted Codex runtime and publish the `Codex Governance Authority` GitHub
Check through the dedicated GitHub App.

## Current state

**Phase 10 is DONE for the declared GitHub reference-provider scope under owner-approved REC-D-018. Phase 11 Slice 11.1 is now merged through Codex PR #27: the versioned declarative framework contract mirror, strict loader, and equivalence gate are installed. This completion change disarms its publication activation; privileged bootstrap stays disabled. Runtime semantic authority remains legacy Python until Slices 11.2/11.3, with compiler cutover deferred to 11.4.**

The earlier candidate-scoped publisher proof is captured and disarmed. The
credential-free runtime adapter produced durable PASS evidence for disposable Codex
PR #17, a success-only `PublicationPermit`, and the dedicated GitHub App emitted
`Codex Governance Authority` check run `103547296485` on the exact candidate head.
That proof configuration was then removed and the default publisher configuration
remains write-disabled.

Codex provider ruleset `main-governance` is now active as repository ruleset
`23193929` on the default branch with no bypass actors. It requires both
`Governance Qualification` and `Codex Governance Authority`; the external authority
context is bound to GitHub App integration ID `4864946`.

A ready, non-draft disposable Codex PR #20 completed every normal candidate check
successfully while intentionally receiving no `Codex Governance Authority` check.
GitHub reported the PR as conflict-free (`mergeable: true`) but provider blocked
(`mergeable_state: blocked`). There were no reviews or review threads and the PR
was closed without merge. The observation is recorded in
`governance/evidence/provider-enforcement-001.json`.

A second ready, non-draft disposable Codex PR #21 then completed every normal
candidate check successfully. An operator-owned commit status named exactly
`Codex Governance Authority` was published as `success` on the exact candidate
head, but it was created by user `anshacerbia2` rather than the dedicated authority
GitHub App. GitHub still reported `mergeable_state: blocked`, proving that a
same-name success from the wrong source cannot satisfy the rule bound to integration
ID `4864946`. The PR was closed without merge and the observation is recorded in
`governance/evidence/provider-wrong-source-001.json`.

Codex PR #22 installed the permanent attestation reader. Authority separately
promoted its merged source `d835991afe6ada47a66d012a3ddc2c4350cd9ff8` and disarmed
the bootstrap. Codex PR #23 then completed protected maintenance through that
permanent reader with bootstrap disabled; see the
[post-disarm proof](docs/implementation-notes/0011-permanent-maintenance-proof-complete.md)
and `governance/evidence/permanent-maintenance-proof-001.json`.

Codex PR #24 subsequently reconciled PLAN/ROADMAP through the same promoted
runtime and dedicated-App publication boundary. Its
[completion record](docs/implementation-notes/0013-pr24-status-reconciliation-complete.md)
retains the evidence and publication cleanup. No standing controlled-publication
activation is enabled. Exact attestations remain append-only and candidate-bound.

The maintenance-path claim is true under its existing promoted/disarmed invariants.
[Disposable provider observations](docs/implementation-notes/0015-provider-negative-observations.md)
now record isolated direct-update, non-fast-forward, deletion, unresolved-thread,
merge-method, and failing-check controls with positive comparisons. The fixture
repository was archived; production rules and main were unchanged.

A subsequent [stale-review experiment](docs/implementation-notes/0016-stale-review-observation.md)
observed review `5258210954` from the authorized non-author account change from
APPROVED to DISMISSED after a new reviewable commit, without manual dismissal.
The fixture was closed/archived and its temporary Write grant removed. This proves
the isolated account-based mechanism, not independently controlled human reviewers
or a merge-blocking requirement under the current zero-approval bootstrap.

The complete mirror was rejected because GitHub did not admit the Authority App
integration ID in the earlier fixture. Its installation scope was not widened.
The owner-approved scoped acceptance explicitly maps the limited fixture evidence to production.
Those earlier records remain historical. The current scoped assessment is recorded in
[note 0019](docs/implementation-notes/0019-phase10-scoped-acceptance.md) and
`governance/evidence/phase10-acceptance-001.json`; it does not claim full-mirror equivalence. The
[acceptance plan](docs/implementation-notes/0014-provider-negative-acceptance-plan.md)
is preserved as the original test plan; configuration parity or isolated control
success alone did not close the phase. The later owner decision, scoped acceptance
and governed status merge are recorded separately.

No GitHub App private key, installation token, webhook secret, or other credential
belongs in this repository.

The [qualification and native-Git evidence package](docs/implementation-notes/0017-offline-provider-evidence-package.md)
adds selected captures for the real Codex PR #25 qualification failure and native
Git control observations, with 30 offline integrity tests. Its manifest records
the original packaging-time state; the linked integration follow-up and PR record
separately track repository integration. No runtime, provider policy or acceptance
claim is advanced by adding these historical evidence files.

## Trust boundary

- `scnehaux/codex` owns governance framework semantics and the promoted runtime.
- `scnehaux/codex-authority` owns trusted execution, evidence, publication, and
  deployment.
- Candidate changes cannot select the effective authority revision.
- Candidate changes cannot auto-deploy authority code.
- Candidate code is never executed by the authority.
- The trusted evaluation runtime remains credential-free.
- GitHub App credentials and webhook secrets are never committed.
- A raw evaluation result is not a publication capability.
- Only an evidenced PASS with exact candidate/source identity may become a
  `PublicationPermit`.
- The credential-bearing publisher accepts only that narrow permit and re-checks
  the exact open PR/base/head identity immediately before publication.
- The default publisher remains disabled; the completed candidate proof is a
  historical evidence record, not a reusable publication capability.
- Privileged attestations are independently administered and exact-candidate-bound;
  existing JSON records are immutable and new approvals are additive.
- Provider ruleset activation does not by itself prove every enforcement concern.
- System-level enforcement acceptance is source- and scope-bound by the ten-row
  assessment; maintenance proof or component self-reports alone cannot replace it.

## Architecture

```text
GitHub event / operator request
            |
            v
      Authority Service
            |
            v
  Promoted Codex Runtime
        Adapter Port
            |
            v
 Verified Runtime Envelope
            |
            +---- privilege-only failure ----+
            |                                |
            |                                v
            |                    Exact Authority Attestation
            |                    bootstrap: DISABLED by default
            |                                |
            +--------------- verified -------+
            |
            v
      Evidence Record
            |
            v
   Publication Permit Gate
            |
            v
      PublicationPermit
            |
            v
 GitHub App Publisher
   default: DISABLED
   candidate proof: COMPLETED + DISARMED
            |
            v
 GitHub main-governance ruleset
   ACTIVE / no bypass
```

The diagram retains the historical bootstrap adapter path for context; bootstrap
is disabled. In the promoted permanent path, attestation reading occurs inside the
Codex attested runtime and the version-2 result retains its original verdict.

The authority does **not** reimplement Codex candidate collection or governance
evaluation semantics. The runtime adapter wraps the independently promoted Codex
runtime and verifies exact source identities before producing a
`RuntimeDecisionEnvelope`.

The publisher is a separate, smaller credential-bearing boundary. It does not
receive credentials during evaluation, does not execute candidate code, does not
accept caller-selected repository/context/conclusion, and does not automatically
retry the authority-check POST.

## Repository layout

```text
governance/                         authority, promotion, protection, publisher and privileged-maintenance contracts
src/codex_authority/                pure authority orchestration, permit, and privileged-boundary types
integrations/github-app-publisher/  isolated GitHub App publication boundary
scripts/                            repository/security invariants and controlled issuers
tests/                              fail-closed behavior and contract tests
docs/                               implementation-local architecture notes
.github/                            CI and ownership
```

Normative architecture artifacts for Codex and Codex Authority belong in
`scnehaux/codex-architecture`. Documents in this repository are implementation
notes and must not masquerade as Codex ADR artifacts.

## Local verification

Python 3.13+:

```bash
python -I -m compileall -q src scripts tests integrations/github-app-publisher
python -I -m unittest discover -s tests -v
python -I scripts/verify_foundation.py
python -I scripts/verify_publisher.py
python -I scripts/verify_publisher_proof.py
python -I scripts/verify_privileged_maintenance.py
python -I scripts/verify_privileged_attestation_history.py
test -z "$(git status --porcelain --untracked-files=all)"
```

The authority core has no third-party runtime dependency. The credential-bearing
publisher uses separately pinned `PyJWT` and `cryptography` dependencies only
for an explicit authenticated publication run.

## Evolution rule

New capability is added behind explicit promotion gates. Adding publisher source
does not enable generic publication; proving publication does not by itself prove
provider enforcement; activating provider enforcement does not invent a trusted
path for privileged governance mutation; and staging a privileged bootstrap does
not prove or enable the permanent maintenance path.

The next planned Codex slice is 11.1, Declarative Framework Contract. Preserve
the active production ruleset, the permanent maintenance boundary and existing
semantics. Scoped Phase 10 acceptance does not certify later phases, a full mirror,
independent human review or future provider behavior. Relevant changes require
reassessment; publication always needs a new exact-candidate authorization.

## Recommendation and decision records

The [Stage D recommendation and decision ledger](docs/implementation-notes/0002-stage-d-recommendation-ledger.md)
records material recommendations, their primary references, trade-offs, plan
impact, validation criteria, and decision history. Read it alongside the
[privileged-maintenance lifecycle](docs/privileged-maintenance.md) before preparing
the next slice. Recommendations remain separate from accepted decisions and
implementation evidence; documentation alone never promotes a runtime, enables
publication, or changes governance claims.

The [provider-negative acceptance plan](docs/implementation-notes/0014-provider-negative-acceptance-plan.md)
records REC-D-016/017, admin admission, fixture equivalence limits, the ten-row
acceptance matrix, and cleanup. Its planner emits payloads only, not live evidence.

The [live disposable observation record](docs/implementation-notes/0015-provider-negative-observations.md)
executes REC-D-016/017 with scoped API evidence, positive controls, archived cleanup,
and explicit mirror-admission and non-author-reviewer limits.

The [stale-review follow-up](docs/implementation-notes/0016-stale-review-observation.md)
records the later actual approval/dismissal transition, temporary-access cleanup,
and the distinction between account identity, independent review, and full acceptance.

The [scoped acceptance record](docs/implementation-notes/0019-phase10-scoped-acceptance.md)
owns the source-bound system assessment. Historical component false flags do not
constitute a current global status. The [completion record](docs/implementation-notes/0021-phase10-completion.md)
links actual Codex PR #26 merge, source-bound publication, post-merge ALIGNED
observation and the reviewed disarm. The review bootstrap remains active;
Governance 1.0 and later phases are not declared ready.
