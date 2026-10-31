# Codex PR #49: disarm expired activation

Recorded: 2026-11-01 (Asia/Jakarta). Implementation-local, non-normative.

Activation [#128](https://github.com/scnehaux/codex-authority/pull/128) bound Codex PR #49 head `e2c6583bfa40071e282581ea548326f6bfc15aaf` and permit `49152d7293ff392b43880d235f7242026dcfe83e11ffe93863fbea1238be707a` for the window 2026-10-31T17:39:25Z through 2026-10-31T17:54:25Z. The offline preview from the exported `1bb0dd5` publisher returned `controlled_publication_preview` with zero remote mutations. The single `--write` invocation ran after the window closed and stopped with `activation-expired-or-early` before the attempt journal was reserved: no credential was read, no installation token was issued and no check was posted. The local publication-state directory is empty.

This change restores the disabled state and null activation exactly as left by disarm [#123](https://github.com/scnehaux/codex-authority/pull/123). The permit, evidence and receipt in the expired window are not reused. Publication for Codex PR #49 requires a fresh permit issued on the resulting `main` and a new fifteen-minute activation, as with PR 40 (#87, #88, #89).

No standing publication capability, GDC approval or admission is granted.
