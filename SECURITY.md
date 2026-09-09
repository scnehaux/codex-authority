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
   require the reviewed CI gate; and
2. a battle-tested repository secret-scanning control must be enabled and
   verified.

The checked-in desired state is recorded in
`governance/repository-protection.json`. Its provider enforcement flag remains
false until external evidence proves the setting is active.

## Failure policy

Authentication, candidate identity, source identity, runtime, evidence, and
provider uncertainty fail closed. They must not be converted into a successful
authority result.
