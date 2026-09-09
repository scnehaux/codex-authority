# Scnehaux Codex Authority

Independent governance authority runtime for `scnehaux/codex`.

This repository owns the trusted execution boundary that will eventually collect
candidate facts, run the promoted governance evaluator, and publish the
`Codex Governance Authority` GitHub Check through the dedicated GitHub App.

## Current state

**Foundation only. Publication is deliberately disabled.**

The repository currently establishes the authority domain model, fail-closed
application boundary, promotion contract, CI, security rules, and architecture.
It does not contain GitHub App credentials, does not publish checks, and is not
yet a production service.

## Trust boundary

- `scnehaux/codex` is the governed candidate/control-plane repository.
- `scnehaux/codex-authority` is independently administered authority source.
- Candidate changes cannot select the effective authority revision.
- Candidate changes cannot auto-deploy authority code.
- Candidate code is never executed by the authority.
- GitHub App credentials and webhook secrets are never committed.
- A successful evaluation is not equivalent to provider enforcement.
- Publication stays disabled until controlled publisher proof exists.
- Effective merge enforcement stays unclaimed until provider-side negative proof exists.

## Architecture

The initial architecture is intentionally small:

```text
GitHub event / operator request
            |
            v
      Authority Service
            |
      +-----+------+
      |            |
      v            v
Candidate      Promoted
collector      evaluator
      |            |
      +-----+------+
            |
            v
     Authority outcome
            |
      [publisher absent]
```

The publisher, webhook ingress, deployment runtime, and durable operational
evidence are introduced in later reviewed slices. See
[`docs/architecture.md`](docs/architecture.md).

## Repository layout

```text
governance/                 authority and promotion contracts
src/codex_authority/        pure domain/application core
scripts/                    repository invariants
tests/                      fail-closed behavior and contract tests
docs/                       architecture and decisions
.github/                    CI and ownership
```

## Local verification

Python 3.13+:

```bash
python -I -m compileall -q src scripts tests
python -I -m unittest discover -s tests -v
python -I scripts/verify_foundation.py
```

No third-party runtime dependency is required by the foundation slice.

## Evolution rule

New capability is added behind explicit ports and promotion gates. In particular,
adding a GitHub publisher does not automatically enable publication, and adding a
deployment target does not automatically make that revision effective.
