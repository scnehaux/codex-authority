# GitHub App Authority Publisher

This is the credential-bearing boundary for the fixed `Codex Governance Authority`
check. The default checked-in `config.json` is intentionally **write-disabled**.

The publisher does not evaluate candidate code. It accepts only the strict
`codex-governance-publication-permit` emitted after a durable PASS from the
trusted authority service. The permit fixes the repository, PR, base/head SHAs,
promoted Codex runtime/evaluator revisions, authority-service revision, GitHub
App identity, check context, and successful conclusion.

## Safety model

- Offline preview is the default and performs zero network mutations.
- Default `config.json` remains disabled.
- Any candidate proof must be separately governed, bound to one exact candidate
  SHA and one exact permit digest, and removed after use.
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

## Completed candidate proof

The first candidate-scoped proof completed against disposable Codex PR #17 at exact
head `a6ed1def64503ca57c647ce45937f887873aac6f`. The dedicated GitHub App emitted
check run `103547296485` with conclusion `success`, exact candidate/source binding
was preserved, and the installation token was revoked.

The governed proof configuration used for that one candidate has been removed and
PR #17 was closed without merge. The durable provider observation lives in
`governance/evidence/publisher-live-001.json`. This evidence does **not** enable
generic standalone publication and does not prove effective merge enforcement.
Generic live publication remains absent from this standalone tool; that belongs in
a later hosted authority worker where the permit stays inside the trusted process.
