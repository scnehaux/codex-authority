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
confined to the future publisher boundary.

## Trust rules

Changes must not create a path where `scnehaux/codex` can select the effective
authority revision, auto-deploy authority code, execute candidate code inside the
authority runtime, or obtain authority credentials.

Authority orchestration must consume a verified promoted Codex runtime envelope.
It must not recreate Codex governance semantics in a parallel evaluator.

A raw evaluation outcome is not a publication capability. Publishing
`Codex Governance Authority` requires a separately validated publication permit
and a credential-bearing publisher boundary.

## Source identity

The following identities are distinct and must be independently traceable:

- Codex evaluator source revision;
- Codex runtime source revision;
- authority service source revision;
- publisher source revision; and
- deployment artifact digest.

Do not overload these as one generic authority revision.

## Repository protection prerequisites

Before any live publisher credential is introduced:

1. `main` must be provider-protected against direct/force/deletion paths and
   require the reviewed CI gates; and
2. a battle-tested repository secret-scanning control must be enabled and
   verified.

The desired provider projection is recorded in
`governance/github-main-ruleset.json` and the provider-neutral requirement in
`governance/repository-protection.json`. Their enforcement claim remains false
until live provider evidence proves the settings are active.

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

A successful workflow run is necessary but not sufficient to activate the
publisher. The check must also become required by provider-side protection and
that provider state must be evidenced before publisher credentials are used.

## Failure policy

Authentication, candidate identity, source identity, runtime, evidence, secret
scanning, and provider uncertainty fail closed. They must not be converted into
a successful authority result.
