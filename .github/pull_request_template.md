## Intent

Describe the authority behavior or contract being changed.

## Trust-boundary review

- [ ] Candidate code is not executed.
- [ ] Candidate changes cannot select or auto-deploy the effective authority revision.
- [ ] No credentials, tokens, private keys, webhook secrets, or authorization headers are committed.
- [ ] New failure paths fail closed.
- [ ] Publication/enforcement claims are not advanced without corresponding live evidence.

## Verification

Describe deterministic tests and any required controlled external proof.
