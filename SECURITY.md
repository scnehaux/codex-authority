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
and must be scoped to the minimum permissions required.

## Trust rules

Changes must not create a path where `scnehaux/codex` can select the effective
authority revision, auto-deploy authority code, execute candidate code inside the
authority runtime, or obtain authority credentials.

Publishing `Codex Governance Authority` is a privileged capability. It remains
disabled until a controlled live publisher proof and explicit promotion are
reviewed.

## Failure policy

Authentication, candidate identity, source identity, evaluator, evidence, and
provider uncertainty fail closed. They must not be converted into a successful
authority result.
