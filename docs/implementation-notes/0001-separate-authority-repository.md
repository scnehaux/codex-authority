# Implementation Note 0001: Separate the authority repository

- Status: bootstrap reference
- Scope: implementation-local, non-normative
- Date: 2026-09-09

This is intentionally **not** a Codex ADR artifact.

Normative architectural decisions for Codex and Codex Authority belong in
`scnehaux/codex-architecture` and must use the Codex ADR contract.

## Context

`scnehaux/codex` defines governance framework semantics and is also the
candidate repository whose pull requests must be evaluated. If the effective
authority runtime and deployment path were controlled by the same candidate
revision being evaluated, the trust relationship would be circular.

## Local implementation decision

The external governance authority is developed and promoted from
`scnehaux/codex-authority`, an independently administered repository.

`scnehaux/codex` may declare expected authority identity and consume resulting
checks, but it cannot select or auto-deploy the effective authority deployment.

Authority credentials are runtime secrets and are not stored in either
repository.

This note exists only to preserve bootstrap implementation context until the
corresponding normative architecture artifact is established in
`scnehaux/codex-architecture`.
