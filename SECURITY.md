# Security

This repository is a security-sensitive control plane.

## Credentials

Never commit:

- GitHub App private keys;
- installation tokens;
- webhook secrets;
- personal access tokens;
- cloud credentials; or
- copied authorization headers.

Runtime credentials must be injected from an external secret-management boundary
and scoped to the minimum permissions required.

The promoted Codex evaluation runtime remains credential-free. Credential use is
confined to the publisher boundary and begins only after evaluation and durable
evidence have produced a valid publication permit.

## Trust rules

Changes must not create a path where `scnehaux/codex` can select the effective
authority revision, auto-deploy authority code, execute candidate code inside the
authority runtime, or obtain authority credentials.

Authority orchestration must consume a verified promoted Codex runtime envelope.
It must not recreate Codex governance semantics in a parallel evaluator.

A raw evaluation outcome is not a publication capability. Publishing
`Codex Governance Authority` requires a separately validated, success-only
`PublicationPermit` bound to the exact repository, PR, base/head SHAs, promoted
Codex runtime/evaluator revisions, authority-service revision, dedicated GitHub
App ID, fixed check context, and successful conclusion.

## Publisher boundary

The credential-bearing GitHub App publisher is intentionally smaller than the
evaluation runtime and obeys these invariants:

- checked-in write mode is disabled;
- future proof mode is bound to one exact candidate SHA and exact permit digest;
- authenticated publisher/config/permit copies must be exported outside every
  Git checkout;
- the publisher source files must match the promoted Git blobs;
- the private key must be a regular file outside Git repositories and the
  publisher kit;
- `api.github.com`, `scnehaux/codex`, `Codex Governance Authority`, the dedicated
  App ID, and the `success` conclusion are fixed, not caller-selected;
- the installation token is minimally scoped and short lived;
- the PR is re-read immediately before publication and must still match the
  exact permit base/head identity;
- the check POST is never retried automatically after an ambiguous failure; and
- a successful publication report requires installation-token revocation.

The publisher's preview mode is offline and does not read the private key.

## Source identity

The following identities are distinct and must be independently traceable:

- Codex evaluator source revision;
- Codex runtime source revision;
- authority service source revision;
- publisher source revision and publisher Git blob; and
- deployment artifact digest.

Do not overload these as one generic authority revision.

## Repository protection prerequisites

Before any live publisher credential is introduced:

1. `main` must be provider-protected against direct/force/deletion paths and
   require the reviewed CI gates; and
2. a battle-tested repository secret-scanning control must be enabled and
   verified.

Both prerequisites are now governed by live evidence. Their existence does not
by itself enable the publisher.

## Secret scanning

`Secret Scan` uses TruffleHog OSS as an independent, credential-free CI control.
Both the GitHub Action source revision and scanner version are fixed in
`governance/secret-scanning.json`. The workflow:

- runs for pull requests and pushes to `main`;
- runs a weekly full-history scan;
- retains no checkout credentials;
- receives no repository secrets;
- disables scanner self-update; and
- fails on findings and scanner errors.

A successful scan is necessary but not sufficient to activate publisher writes.
Publisher source promotion and controlled live proof remain separate gates.

## Failure policy

Authentication, candidate identity, source identity, runtime, evidence, permit,
publisher, token revocation, secret scanning, and provider uncertainty fail
closed. None may be converted into a successful authority result.
