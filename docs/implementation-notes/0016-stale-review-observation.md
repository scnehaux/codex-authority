# Automatic stale-approval dismissal observed

Recorded: 2026-09-20 (Asia/Jakarta). Implementation-local, non-normative.

## Scope and baseline

This completes the isolated stale-approval experiment prepared after the owner
requested adding `scnehaux-org` as reviewer. It follows the provider acceptance
plan in [0014](0014-provider-negative-acceptance-plan.md) and supplements, rather
than rewrites, the earlier pending observation in
[0015](0015-provider-negative-observations.md).

Authority baseline: `6c8d8edfd1cf15c8383c646ac9a1f5b990b92f78`.
Codex main remained `107f0dc53e873ef6d24a9f12cd28da7348f79331`.
Fixture: `scnehaux/codex-provider-proof-20260919t224050z-0478aef8`, ID
`1377674304`, PR #1. This is synthetic data, not production maintenance approval.

The fixture used only the copied pull-request rule, including all its parameters,
from production ruleset `23193929`. Fixture ruleset `23711520` was active with no
bypass actors and targeted `isolate-stale-approval`. Its rule was compared to the
production rule before the push and verified unchanged afterward. Deletion,
non-fast-forward, linear-history and status-check rules were not part of this
isolation fixture. This is not a full production mirror.

## Actual approval and dismissal

The user submitted review `5258210954` through account `scnehaux-org` (ID
`261198920`) at `2026-09-19T23:03:00Z`. The PR author was `anshacerbia2` (ID
`108260133`). The reviewer had Write permission when the approval was observed.
The assistant did not submit an approval as either account.

Before changing the candidate, the operator captured `APPROVED` on exact head
`c2bbd8664bfdef3d377703f7dd0a1826722a3419`, base
`f4b5a66248cf340a51e65c313ccaa0a31f2f2436`. The approval snapshot was saved before
creating or pushing the next commit. A new reviewable change to `fixture.txt` was
then appended as commit `5f890322f22f9c86498d2a3fad6f2ae99819f2c0`; the ref update
was a normal fast-forward, not a force push. The target base and rule stayed fixed.

The first read after the push still reported `APPROVED`; the next reported
`DISMISSED` for the same review ID. GitHub's `review_dismissed` event
`31463296946`, created at `2026-09-19T23:05:47Z`, names the new commit as
`dismissal_commit_id` and the original review ID. No manual dismissal endpoint or
review mutation was invoked. The provider event was also re-read independently
through the GitHub connector after capture.

The recorded result is **automatic stale-approval dismissal observed in the
isolated fixture**, not merely configuration presence or a generic merge error.

## Why the author cannot approve, and what this proves

GitHub does not allow a pull-request author to approve their own PR [REVIEWS].
Therefore `anshacerbia2` could comment on this PR but could not approve it. This
is not evidence of missing admin rights or an incorrectly configured reviewer.
The same account can review other people's PRs subject to its access permissions.

The provider distinguishes account identity. The user reported operating
`scnehaux-org` for this review, so distinct account IDs are not proof of separately
controlled human reviewers. `independent_human_review_proven` stays false.
A future requirement for independent human approval must not be satisfied by
relabeling this two-account mechanism test as organizational independence.

The copied active policy requires **zero** approving reviews. Dismissing an
existing stale review and requiring an approval before merge are separate controls.
This experiment verifies the first. It does not claim the PR was blocked after
dismissal, does not add a one-approval requirement, and does not change the review
bootstrap. The fixture PR was closed without merge once evidence was captured.

This applies REC-D-016/017: observe a state transition tied to a reviewable commit,
preserve the exact scope, and do not confuse account separation with an independent
administrative trust boundary. No new policy or acceptance waiver is introduced.

## Cleanup and record

After capturing the result and timeline, the operator closed fixture PR #1 without
merge, confirmed no open PRs, removed only the direct Write grant added for
`scnehaux-org`, and verified its remaining effective permission was Read. No
organization/team membership or production repository access was changed.
The ID-verified fixture was then archived, not deleted; its main ref and its
review/test history were retained. The earlier fixture remains archived too.

Production main and the full production ruleset were read again and matched the
pre-push observations. Bootstrap and controlled publication remain disabled, and
the existing permanent-maintenance proof is not altered.

`governance/evidence/provider-stale-review-001.json` is a selected observation
summary including identities, before/after states, commit-bound provider event,
cleanup and explicit non-claims. The full operator-local session retains 80
intent/outcome pairs with request IDs/timestamps and four before/after/timeline/
cleanup snapshot files. The checked-in summary is not a byte-for-byte copy of that
complete capture, a provider signature, or a new publication permit. History in
`provider-negative-001.json` remains unchanged: stale review was still pending
at the time of that earlier run.

## Remaining acceptance

This resolves the missing non-author-account observation for the isolated
stale-review mechanism. It does not resolve the rejected full-mirror admission
(`Invalid integration ids`) or automatically accept a mapping from isolated tests
plus existing production evidence to all Phase 10 obligations. App installation
scope has not been widened. `effective_enforcement_proven` remains false until
that acceptance work is explicitly reviewed; this record does not waive it.

Artifact tests check the review/commit/event linkage, timestamps, unchanged base,
zero-approval scope, retained capture references, cleanup, and conservative claims.
They validate the recorded artifact, not a new live test. CI results belong in
the PR verification comment after observation; no local full-suite result is
asserted by this document.

## Primary sources

[REVIEWS]: https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-proposed-changes-in-a-pull-request
[RULES]: https://docs.github.com/en/enterprise-cloud@latest/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
[EVENT]: https://api.github.com/repos/scnehaux/codex-provider-proof-20260919t224050z-0478aef8/issues/events/31463296946
[PR]: https://github.com/scnehaux/codex-provider-proof-20260919t224050z-0478aef8/pull/1

GitHub documents self-approval restrictions [REVIEWS] and stale-review dismissal
[RULES]; the actual commit-bound observation is retained in the [event][EVENT]
and [fixture PR][PR]. Documentation alone is not evidence that a control executed.
