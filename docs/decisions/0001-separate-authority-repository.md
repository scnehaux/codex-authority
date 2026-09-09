# ADR-0001: Separate the external authority repository

- Status: Accepted
- Date: 2026-09-09

## Context

`scnehaux/codex` defines governance policy and is also the candidate repository
whose pull requests must be evaluated. If the effective authority runtime and
deployment path were controlled by the same candidate revision being evaluated,
the trust relationship would be circular.

## Decision

The effective governance authority is developed and promoted from
`scnehaux/codex-authority`, an independently administered repository.

`scnehaux/codex` may declare the expected authority identity and consume the
resulting Check, but it cannot select or auto-deploy the effective authority
revision.

Authority credentials are runtime secrets and are not stored in either
repository.

## Consequences

### Positive

- Candidate and authority source have an explicit trust boundary.
- Authority revisions can be promoted independently of candidate changes.
- GitHub App credentials can be isolated with the authority deployment.
- Future hosting, scaling, and provider adapters can evolve without expanding the candidate repository's trusted computing base.

### Costs

- Two repositories must maintain compatible contracts.
- Promotion needs explicit cross-repository evidence.
- Operational deployment becomes a separate responsibility.

These costs are intentional because they remove circular authority and make the
enforcement chain auditable.
