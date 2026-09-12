# Scnehaux Codex Authority

Independent governance authority runtime for `scnehaux/codex`.

This repository owns the trusted execution and publication boundary that will
run a promoted Codex runtime and publish the `Codex Governance Authority` GitHub
Check through the dedicated GitHub App.

## Current state

**Stage B candidate-scoped live publication proof is captured and disarmed. Generic publication remains disabled.**

Provider protection and secret scanning are live and governed. The credential-free
runtime adapter produced durable PASS evidence for disposable Codex PR #17 and a
success-only `PublicationPermit`. The separately governed proof configuration then
bound that exact candidate head, permit digest, authority-service revision,
publisher revision, and publisher Git blobs.

The controlled external publisher successfully emitted `Codex Governance Authority`
check run `103547296485` through the dedicated GitHub App on the exact candidate
head. The installation token was revoked, the provider observation is recorded in
`governance/evidence/publisher-live-001.json`, the candidate PR was closed without
merge, and the candidate-scoped proof configuration has been removed. The default
publisher configuration remains write-disabled. Effective merge enforcement is
still explicitly unclaimed.

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
- Effective merge enforcement stays unclaimed until provider-side activation and
  negative proof complete.

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
governance/                         authority, promotion, protection, publisher contracts
src/codex_authority/                pure authority orchestration and permit types
integrations/github-app-publisher/  isolated GitHub App publication boundary
scripts/                            repository/security invariants
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
test -z "$(git status --porcelain --untracked-files=all)"
```

The authority core has no third-party runtime dependency. The credential-bearing
publisher uses separately pinned `PyJWT` and `cryptography` dependencies only
for an explicit authenticated publication run.

## Evolution rule

New capability is added behind explicit promotion gates. Adding publisher source
does not enable generic publication; proving publication does not activate provider
merge enforcement; and adding a deployment target does not make that revision
effective.

The completed publisher proof is now evidence for the next Codex activation slice.
That later slice must independently bind the authority revision and publisher
evidence, project the external authority check into provider protection, and prove
merge denial when the authority check is absent before effective enforcement can
be claimed.
