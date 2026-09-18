# PR #23 permanent-path attestation

Recorded: 2026-09-18 (Asia/Jakarta). Implementation-local, non-normative.

## Purpose

This record prepares the first post-disarm privileged-validation attestation for
`scnehaux/codex` PR #23. The candidate is intentionally minimal: one comment-only
change to protected `governance/scm/trust-boundary.yaml`; parsed policy semantics
are unchanged.

Exact candidate binding:

- repository: `scnehaux/codex`
- pull request: `23`
- base: `d835991afe6ada47a66d012a3ddc2c4350cd9ff8`
- head: `d681a8f311cbb3a0bc69b795639112918e57a85f`
- changed files: `governance/scm/trust-boundary.yaml`

The attestation is append-only and grants only the existing
`protected-governance-maintenance` privilege scope.

## Boundary

Bootstrap remains disabled and unbound. Controlled publication remains disabled.
The promoted permanent attested runtime is the only evaluation path intended for
this proof. No candidate code executes in Authority and no evaluation credential
is introduced.

The attestation PR must not merge until the candidate's `Governance Qualification`
for this exact head is observed successful. Any candidate push invalidates this
record and requires a new head-bound attestation.

After the attestation merges, the permanent runtime must be exported from exact
merged Codex revision `d835991afe6ada47a66d012a3ddc2c4350cd9ff8`, produce
version-2 evidence and receipt, and obtain a separately reviewed short-lived
publication activation bound to the real output digests.

A successful merge of PR #23 through the source-bound App check is the acceptance
observation for post-disarm maintenance liveness. Invalid or drifted candidates
must remain fail-closed.
