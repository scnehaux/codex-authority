# ARB approval gate before permit export

Recorded: 2026-10-31 (Asia/Jakarta). Implementation-local, non-normative.

Codex PR #48 promoted GDC-000 to `approved` / `1.0.0` and was published and merged before the owner's ARB approval record required by Codex PLAN REC-13-003 existed. The record was added afterwards in [#124](https://github.com/scnehaux/codex-authority/pull/124). The procedure relied on the operator remembering the rule; this change makes it fail closed.

`scripts/issue_controlled_permit.py` now runs `codex_authority.arb_gate.check` after a PASS evaluation and before `permit.json` is written. The candidate's changed files, base and head come from the runtime snapshot. For every changed `governance/GDC-*.md` whose head `doc_meta` is `status: approved` with a version that differs from the base (a promotion, a new approved GDC, or a new version of an approved GDC), the gate requires `governance/arb-approvals/<GDC>-<version>-<head>.json` on this checkout. The record must bind the repository, PR, exact head, document, version and `approved` status, carry `decision: approve`, a GDC-002 score of at least 9/10, a review date, a named approver and the review-exception status. Otherwise the permit is withheld with an `arb-approval-record-missing:` or `arb-approval-record-invalid:` reason; the evidence and receipt already written remain as a record of the blocked attempt.

GDC contents are read from local Git objects of the `scnehaux/codex` clone (default: sibling `codex` folder, override with `--codex-repo`) with inherited `GIT_*` variables removed and replacement objects disabled. Missing commits, a removed GDC or unreadable metadata fail closed. No network access, credential or candidate execution is added.

The gate module is not imported by the controlled publisher and is not among its pinned source blobs, so `publisher_source_blobs` and the promoted runtime are unchanged. Replaying the gate on Codex #48 blocks it without the #124 record and passes with it; the GDC-001 draft edit in #47 needs no record.

This is a tooling safeguard. It does not create, replace or relax any ARB approval, and it grants no publication capability.
