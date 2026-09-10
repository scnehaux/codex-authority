# GitHub App Authority Publisher

This is the credential-bearing boundary for the fixed `Codex Governance Authority`
check. The checked-in configuration is intentionally **write-disabled**.

The publisher does not evaluate candidate code. It accepts only the strict
`codex-governance-publication-permit` emitted after a durable PASS from the
trusted authority service. The permit fixes the repository, PR, base/head SHAs,
promoted Codex runtime/evaluator revisions, authority-service revision, GitHub
App identity, check context, and successful conclusion.

## Safety model

- Offline preview is the default and performs zero network mutations.
- `config.json` must be privileged-promoted from `disabled` to `proof`
  before `--write` can do anything.
- `proof` mode is bound to one exact candidate SHA and one exact permit digest.
- Authenticated execution requires exported publisher/config/permit copies
  outside every Git checkout.
- The exported publisher source must match the promoted Git blobs exactly.
- The private key must stay outside repositories and the exported publisher kit.
- The GitHub API host, repository, check context, conclusion, App ID, and token
  scope are fixed in code.
- The candidate PR is re-read immediately before publication and must still match
  the exact permit base/head identity.
- The authority check POST is never retried automatically.
- The installation token is revoked after the attempt. A successful proof report
  requires proven revocation.
- No token, PEM, authorization header, or upstream response body is printed.

## Dependencies

Install the pinned dependencies into a dedicated virtual environment:

```text
PyJWT==2.13.0
cryptography==50.0.1
```

## Private-key location

Default locations are outside Git repositories:

- Windows: `%LOCALAPPDATA%\scnehaux-codex-authority\secrets\github-app.pem`
- Linux/macOS: `~/.local/share/scnehaux-codex-authority/secrets/github-app.pem`

On POSIX the publisher requires owner-only permissions (`chmod 600`). On Windows,
restrict the file ACL to the operator account; the script deliberately does not
pretend POSIX mode bits prove Windows ACL security.

## Current slice

Only preview is governed in this slice. Do not edit a local exported config to
turn writes on. A later privileged promotion will pin the reviewed publisher
source revision/blob set, pin the authority-service source revision, and bind one
disposable proof candidate plus its exact permit digest before any credential is used.
Generic live publication is deliberately absent from this standalone tool; it belongs
in a later hosted authority worker where the permit stays inside the trusted process.
