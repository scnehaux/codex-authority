# Scnehaux Codex Authority

Independent governance authority runtime for `scnehaux/codex`.

This repository owns the trusted execution and publication boundary that will
run a promoted Codex runtime and publish the `Codex Governance Authority` GitHub
Check through the dedicated GitHub App.

## Current state

**Stage B publication boundary is staged. Remote publication is still disabled.**

The provider-protection and secret-scanning prerequisites are live and governed.
This slice adds a success-only publication permit plus a credential-isolated
GitHub App publisher implementation, but its checked-in configuration cannot
perform a remote write. Publisher source identity, authority-service source
identity, proof candidate, and live evidence remain unbound until a later
privileged promotion.

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
- Publication stays disabled until a privileged proof promotion pins exact
  authority/publisher source identities and one disposable candidate SHA.
- Effective merge enforcement stays unclaimed until provider-side negative proof
  exists.

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
 GitHub App Publisher [DISABLED]
```

The authority does **not** reimplement Codex candidate collection or governance
evaluation semantics. A future runtime adapter wraps the independently promoted
Codex runtime and verifies exact source identities before producing a
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
test -z "$(git status --porcelain --untracked-files=all)"
```

The authority core has no third-party runtime dependency. The credential-bearing
publisher uses separately pinned `PyJWT` and `cryptography` dependencies only
when a privileged authenticated run is eventually enabled.

## Evolution rule

New capability is added behind explicit promotion gates. Adding publisher source
does not enable publication; proving publication does not activate provider
merge enforcement; and adding a deployment target does not make that revision
effective.

The next privileged slice may pin this reviewed publisher source and the
corresponding authority-service revision, bind one disposable proof candidate and exact permit digest,
export the trusted publisher outside every Git checkout, and perform one
controlled `Codex Governance Authority` check publication.
