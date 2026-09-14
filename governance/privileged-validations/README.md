# Privileged validation attestations

This directory is the independently administered approval surface for protected `scnehaux/codex` governance maintenance.

Attestation JSON files are named by the exact Codex candidate head SHA:

```text
governance/privileged-validations/<40-char-head-sha>.json
```

Each attestation is exact-candidate-bound: repository, PR number, base SHA, head SHA, and the complete sorted changed-file set must match the candidate observed independently by the promoted Codex runtime. The decision is always explicit `pass` for the protected-governance-maintenance scope.

The directory is append-only for JSON records. Existing attestations must never be edited, renamed, or deleted. Superseding a decision requires a new candidate SHA and therefore a new attestation file.

The current Stage D bootstrap remains disabled until a separately reviewed candidate-specific activation binds exactly one Codex PR/head. No credential, GitHub App key, installation token, or candidate-supplied executable content belongs here.
