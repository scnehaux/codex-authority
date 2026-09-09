## Intent

Describe the authority behavior or contract being changed.

## Trust-boundary review

- [ ] Candidate code is not executed.
- [ ] Candidate changes cannot select or auto-deploy effective authority code.
- [ ] Codex governance semantics are consumed from a promoted runtime rather than reimplemented.
- [ ] Codex evaluator/runtime, authority service, publisher, and deployment identities stay explicit.
- [ ] No credentials, tokens, private keys, webhook secrets, or authorization headers are committed.
- [ ] Raw authority outcomes are not treated as publication capabilities.
- [ ] New failure paths fail closed.
- [ ] Publication/enforcement claims are not advanced without corresponding live evidence.
- [ ] Normative architecture changes are tracked in `scnehaux/codex-architecture`, not local pseudo-ADRs.

## Verification

Describe deterministic tests and any required controlled external proof.
