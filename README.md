# Scnehaux Codex Authority

Independent governance authority runtime for `scnehaux/codex`.

This repository owns the trusted execution and publication boundary that will
eventually run a promoted Codex runtime and publish the
`Codex Governance Authority` GitHub Check through the dedicated GitHub App.

## Current state

**Foundation only. Publication is deliberately disabled.**

The repository currently establishes the authority domain model, fail-closed
application boundary, promotion contract, CI, security rules, and
implementation-local architecture notes. It does not contain GitHub App
credentials, does not publish checks, and is not yet a production service.

## Trust boundary

- `scnehaux/codex` owns governance framework semantics and the promoted runtime.
- `scnehaux/codex-authority` owns trusted execution, evidence, publication, and
  deployment.
- Candidate changes cannot select the effective authority revision.
- Candidate changes cannot auto-deploy authority code.
- Candidate code is never executed by the authority.
- The trusted evaluation runtime remains credential-free.
- GitHub App credentials and webhook secrets are never committed.
- Raw evaluation results are not publication capabilities.
- Publication stays disabled until a controlled publisher proof exists.
- Effective merge enforcement stays unclaimed until provider-side negative
  proof exists.

## Architecture

The hardened foundation keeps the trusted computing base small:

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
      [publisher absent]
```

The authority does **not** reimplement Codex candidate collection or governance
evaluation semantics. A future adapter will wrap the independently promoted
Codex runtime and must verify exact source identities before producing a
`RuntimeDecisionEnvelope`.

The publisher, webhook ingress, deployment runtime, durable operational
evidence, and publication permit are introduced in later reviewed slices.

## Repository layout

```text
governance/                 authority, promotion, and protection contracts
src/codex_authority/        pure authority orchestration and trust-boundary types
scripts/                    repository invariants
tests/                      fail-closed behavior and contract tests
docs/                       implementation-local architecture notes
.github/                    CI and ownership
```

Normative architecture artifacts for Codex and Codex Authority belong in
`scnehaux/codex-architecture`. Documents in this repository are implementation
notes and must not masquerade as Codex ADR artifacts.

## Local verification

Python 3.13+:

```bash
python -I -m compileall -q src scripts tests
python -I -m unittest discover -s tests -v
python -I scripts/verify_foundation.py
test -z "$(git status --porcelain --untracked-files=all)"
```

No third-party runtime dependency is required by the foundation slice.

## Evolution rule

New capability is added behind explicit ports and promotion gates. In
particular, adding a GitHub publisher does not automatically enable publication,
and adding a deployment target does not automatically make that revision
effective.

Before any live publisher credential is introduced, provider-side protection of
`main` and a battle-tested repository secret-scanning control must be proven.
