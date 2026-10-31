# Codex PR #48: disarm unedited activation

Recorded: 2026-10-31 (Asia/Jakarta). Implementation-local, non-normative.

Authority [#120](https://github.com/scnehaux/codex-authority/pull/120) was intended to activate publication for Codex PR #48 but was merged as `f48b8d2` without its values being edited. Its `governance/controlled-publication.json` and checked-in test are byte-identical to the Codex PR #47 activation from [#117](https://github.com/scnehaux/codex-authority/pull/117) (`15f9255`): PR 47, head `f8a145d00a885d8c4d606550d4efa05b19c10846`, permit `2fd61913d637b89428e0f88339faef264d2ab7c81c787a259861d98bf501fc56`, window 2026-10-25T20:50:46Z through 2026-10-25T21:05:46Z.

The activation was never usable. Its window had expired six days earlier, Codex PR #47 was already merged, its single permit was already consumed, and its outcome is retained in `governance/publications/f8a145d00a885d8c4d606550d4efa05b19c10846.json`. No preview, publication attempt, credential access or check post was made against it. It does not bind the Codex PR #48 permit.

This change restores the disabled state and null activation exactly as left by disarm [#118](https://github.com/scnehaux/codex-authority/pull/118), together with its disabled-configuration test. The PR #48 attestation from [#119](https://github.com/scnehaux/codex-authority/pull/119) is unaffected. Publication for PR #48 requires a fresh permit issued on the resulting `main` and a new, correctly bound fifteen-minute activation; the permit prepared on `f5e26b0` is not reused.

No standing publication capability, GDC approval or admission is granted.
