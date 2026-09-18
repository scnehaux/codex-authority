# PR #22 controlled publication activation

Recorded: 2026-09-18 (Asia/Jakarta). Implementation-local, non-normative.

## Scope

This change enables one short-lived `candidate-proof` publication activation for
`scnehaux/codex` PR #22 at exact head
`eaa5b41cd84fcc77fd1ff464120d4be83c57d1cd` and base
`0f9dab0091746ac1232174c75ed6330b53dff750`.

The activation is derived only after a successful controlled bootstrap produced
real durable evidence, a linking receipt, and a publication permit. No digest was
pre-bound or guessed.

Exact bindings:

- authority service source: `76d7bc3ee858ff6231e595dbeacc7eda0528080f`
- publisher source: `76d7bc3ee858ff6231e595dbeacc7eda0528080f`
- permit digest: `ddf28dbc0a59fd55af354458948980c6677ca78cc26f020746732104de704d4c`
- evidence SHA-256: `d8b3f5e7e8c789bffd9b658d538f75c8a51d7bb4f42a3c13be406238bab92d26`
- receipt SHA-256: `acbb2351a4cd56c11b284c065c20279e747b39cfcc93f570ef07d28a2e1f9147`

Activation window:

- not before: `2026-09-18T11:19:49Z`
- expires at: `2026-09-18T11:33:49Z`

The full publisher source closure is bound by exact Git blob IDs in the governed
configuration. The App, installation, repository, check context and successful
conclusion remain fixed in code.

## Safety and recovery

This activation does not itself publish. Real execution still requires an export
outside Git, exact repository/SHA operator confirmations, source verification,
receipt/evidence/permit revalidation, fresh qualification observation, exact PR
identity, and the dedicated App key.

The publisher reserves an exclusive durable attempt before credential access and
performs at most one check POST. Ambiguous provider outcomes are reconciled from
the journal and provider observation; they are not blindly retried.

After a successful check and legitimate Codex merge, the activation and bootstrap
must be disabled by reviewed Authority state. The permanent reader is then bound
separately to the merged Codex source before post-disarm maintenance proof.

This operationalizes REC-D-013. It does not advance `effective_enforcement_proven`
and is not a claim of battle-tested operation.
