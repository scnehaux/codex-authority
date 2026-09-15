# Scnehaux Codex Authority

Independent governance authority runtime for `scnehaux/codex`.

This repository owns the trusted execution and publication boundary that will
run a promoted Codex runtime and publish the `Codex Governance Authority` GitHub
Check through the dedicated GitHub App.

## Current state

**Stage C provider activation is live; missing-authority merge denial and wrong-source authority rejection are proven. Stage D privileged maintenance is staged but disabled. Effective enforcement remains explicitly unclaimed.**

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

Stage D now defines the independently administered privileged-validation boundary
needed for protected Codex governance maintenance. Exact candidate attestations
live under `governance/privileged-validations/` and bind repository, PR, base/head
SHAs, and the complete sorted changed-file set. The one-candidate bootstrap is
strictly disabled in checked-in governance and may only resolve the two existing
privilege-gate failures; it cannot override qualification, identity, source, or
candidate-drift failures. The permanent Codex public-read-only attestation reader
is not implemented yet, so the maintenance path is not claimed proven.

This is deliberately still a partial enforcement proof. Delete/non-fast-forward
enforcement and the end-to-end privileged-maintenance path remain unproven.
Protected Codex mutations therefore remain fail-closed until the separately
evidenced bootstrap installs the permanent reader and is disarmed again.

No GitHub App private key, installation token, webhook secret, or other credential
belongs in this repository.

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
- Effective enforcement remains unclaimed until destructive provider rules and the
  privileged maintenance path are independently evidenced.

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

The next slice must preserve the active ruleset while using one exact attested
Codex candidate to install the permanent public-read-only attestation reader, then
disarm the bootstrap. Destructive provider rules are proven separately on a
disposable branch. Only after those facts are durable should
`effective_enforcement_proven` advance.

## Recommendation and decision records

The [Stage D recommendation and decision ledger](docs/implementation-notes/0002-stage-d-recommendation-ledger.md)
records material recommendations, their primary references, trade-offs, plan
impact, validation criteria, and decision history. Read it alongside the
[privileged-maintenance lifecycle](docs/privileged-maintenance.md) before preparing
the next slice. Recommendations remain separate from accepted decisions and
implementation evidence; documentation alone never promotes a runtime, enables
publication, or changes governance claims.
