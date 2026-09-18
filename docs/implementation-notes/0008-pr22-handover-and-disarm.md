# PR #22 handover and temporary-authority disarm

Recorded: 2026-09-18 (Asia/Jakarta). Implementation-local, non-normative.

## Completed bootstrap observation

The one-candidate bootstrap for Codex PR #22 produced durable evidence, receipt,
and permit from Authority revision `76d7bc3ee858ff6231e595dbeacc7eda0528080f`.
The controlled publisher then emitted check run `105581555853` for exact head
`eaa5b41cd84fcc77fd1ff464120d4be83c57d1cd`.

A public provider read observed the check as `completed/success` from GitHub App
ID `4864946`, slug `scnehaux-codex-authority`, owner `scnehaux`. The publisher
journal records the single POST attempt as `published` and token revocation as
successful. Codex PR #22 then merged through the normal protected path at
`d835991afe6ada47a66d012a3ddc2c4350cd9ff8`.

The repository evidence is `governance/evidence/pr22-bootstrap-publication-001.json`.
It deliberately keeps both completion claims false until post-disarm maintenance
is proven and the remaining applicable enforcement evidence is mapped.

## Permanent runtime promotion

The permanent package is bound to merged Codex source
`d835991afe6ada47a66d012a3ddc2c4350cd9ff8` and the exact five-file package:
- `attested_runtime.py` → `c9a0c3bf2fd3c33be4deb1b1e5fc624d1b0b796a`
- `runtime.py` → `c59911e9c0800c917fed21e6f33f3181c3a61e60`
- `evaluator.py` → `ab2f152c21bd6d6f22df21172c4d027035ff8c11`
- `promotion.json` → `f8f67280baf1c8725f67592d015ff37be2c4a4c3`
- `runtime-promotion.json` → `83658bf5a44d22804d1628074dd8f27a7047d68e`

`governance/attested-handover.json` advances to `runtime-promoted` with execution
enabled but publication still disabled. The permanent reader remains credential-free
and publication remains a separate Authority capability.

`governance/privileged-maintenance.json` changes to `permanent-runtime`, clears the
bootstrap candidate, disables bootstrap, and records the permanent runtime as
`promoted`. `governance/controlled-publication.json` returns to disabled/unbound.

The bootstrap attestation remains append-only historical evidence; disarm does not
delete or rewrite it.

## REC-D-015 — Keep exactly one active authority mode during handover

Status: selected for this handover; post-disarm proof still pending.

The temporary bootstrap and the permanent attested runtime must not remain active
as peer authority modes after the installing candidate has merged. This change
therefore disarms bootstrap and promotes the permanent package in the same reviewed
Authority transition, while also disabling the completed publication activation.

First-principles rationale: a temporary escape path should have the smallest scope
and lifetime possible. Leaving both modes enabled would enlarge the authority
surface, create ambiguous recovery semantics, and make it harder to know which
source actually authorized a later decision.

The alternative is a phased overlap where both modes remain enabled until the new
path has proven liveness. That improves maintenance availability but weakens the
single-authority invariant. This project chooses fail-closed availability risk:
if the permanent path fails after handover, recover by a new reviewed change rather
than leaving a standing bootstrap bypass.

Revisit this decision only if future availability requirements justify a formally
specified dual-control migration protocol. Do not introduce silent overlap.

## Acceptance still required

This handover is not Stage D completion. A subsequent protected Codex maintenance
candidate must be evaluated by the promoted attested runtime with bootstrap
disabled, receive an exact Authority attestation, persist evidence and receipt,
obtain a source-bound App check, and merge normally. Invalid candidates must remain
blocked.

Only after that positive post-disarm proof should the privileged maintenance claim
be considered for advancement. `effective_enforcement_proven` additionally requires
mapping and completing every applicable Phase 10 enforcement obligation.
