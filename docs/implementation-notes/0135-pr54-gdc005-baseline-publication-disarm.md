# Codex PR #54: gdc005-baseline publication disarm

Recorded: 2026-11-10 (Asia/Jakarta). Implementation-local, non-normative.

The dedicated App published exact-head success check [129759956098](https://github.com/scnehaux/codex/runs/129759956098) and revoked its installation token. The retained outcome is [the immutable candidate record](../../governance/publications/bf684b4783bf07c51bd1beacc589add94bc69883.json), copied byte for byte from the sole durable journal outcome. The local attempt/outcome and permit/evidence/receipt stay outside Git and are never overwritten or replayed.

Restore disabled state and null activation. No standing publication capability, release, GDC approval or admission is granted.

- Codex [#54](https://github.com/scnehaux/codex/pull/54) squash merged at `fda84648ac11937f72487c8afbd6fcc7789b5b26`.
- Permit digest `728b393cb23f44300c42d888b46048ace4ac10f564a4527e5d682a7b319d58d3`; activation digest `05f9bf69f88e09fc89c75da0004f12727dc33d47a263f1188dfe5fc456dd3ddd`.
- Offline preview: `controlled_publication_preview`, `remote_mutations: 0`; one published attempt; `token_revoked: true`.
