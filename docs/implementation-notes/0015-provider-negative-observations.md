# Disposable provider-negative observations

Recorded: 2026-09-20 (Asia/Jakarta). Implementation-local, non-normative.

## Scope and admission

The owner completed the explicit GitHub CLI browser login and requested continuation.
The CLI reported the active operator account authenticated with keyring storage;
repository metadata confirmed admin access. No credential value was extracted,
printed, copied into evidence, or supplied to the Codex evaluation runtime. The
production Authority App key and installation scope were not used or changed.

This executes the bounded acceptance procedure in
[0014](0014-provider-negative-acceptance-plan.md), especially REC-D-016/017.
Codex remained at `107f0dc53e873ef6d24a9f12cd28da7348f79331`; Authority baseline
was `bc60bd147ac76cabfd9d740b60b95f5a3d247ba5`. Source ruleset `23193929`
remained active with no bypass actors and the original App source binding.

Run: `20260919t215355z-fd04cae4`.
Fixture: `scnehaux/codex-provider-proof-20260919t215355z-fd04cae4`.
Fixture repository ID: `1377645819`.
A new public synthetic-only repository was created; no private project content,
real attestation, permit, credential, or production source code was copied there.

## Full-mirror admission failed; it was not silently weakened

Request `0040` attempted the complete copied ruleset, including the original
`Codex Governance Authority` integration ID `4864946`. GitHub returned HTTP 422:
`Invalid integration ids` in `required_status_checks`. No full mirror was installed.
The failed response and its request ID are retained. This is an admission failure,
not a provider-negative test PASS and not evidence of full equivalence.

As prescribed by the plan, the App installation was not widened and the source
binding was not replaced with a user status to make a mirror pass. Separate named
branches received copied deletion, non-fast-forward, and pull-request controls,
with exact parameter readback and no bypass actors. Each had only its stated
active rule. The repository-level merge methods all remained allowed, as in the
source repository; the pull-request rule itself allowed only squash.

One additional fixture used a clearly synthetic `Provider Proof Qualification`
status to isolate failure-gate mechanics. It intentionally omits the real Codex
check identities and App source constraint. This is not a Codex qualification run,
not App authority, and not a substitute for the rejected full mirror.

All writes were scoped to the newly created fixture name and numeric ID.
Production endpoints were read-only. The proof uses REST ref/merge operations and
GraphQL thread resolution, not a claim about every Git receive-pack transport.

## Observed operations and causal controls

Record numbers refer to `provider-negative-001.responses.json`.

| Mechanism | Negative observation | Positive/control observation and limit |
| --- | --- | --- |
| Direct ref update | `0059`: 422, changes must use a pull request. | `0055`: same actor updates an unprotected control; protected SHA unchanged. Named-branch isolated PR rule, not production main. |
| Non-fast-forward | `0074`: 422, cannot force-push; request genuinely used `force=true` to an ancestor. | `0067`: ordinary forward update allowed; `0071`: identical forced rollback allowed on a control ref. Protected SHA unchanged. |
| Custom deletion | `0080`: 422, cannot delete this branch. | `0077`: control ref deletion succeeds; protected ref remains. Named non-default branch. |
| Native default deletion | `0085`: 422, cannot delete the default branch. | `0083`: no active custom rule applies to that fixture default branch. This proves the native guard, not the custom deletion rule. |
| Unresolved thread | `0097`: 405, a conversation must be resolved. | `0101` resolves the same thread; `0104` merges the unchanged candidate using squash. No other required check interfered. |
| Merge methods | `0120` and `0123`: merge and rebase return 405. | `0126`: squash succeeds for the same candidate; repository settings allow all methods, so the isolated PR rule supplies the restriction. |
| Failing required check | `0146`: 405, synthetic required status is failing. | Only that status changes from failure to success; `0154` merges the same candidate. Provider mechanics only, not real Codex/App evaluation. |

The zero-required-approval configuration is observed in the copied PR parameters;
the method test had no approval reviews and the permitted squash succeeded.
That does not establish independent human approval or stale-approval dismissal.
No production ref was force-updated, deleted, or otherwise mutated by this run.

## Parity, evidence retention, and cleanup

Before/after authenticated reads show unchanged production main, complete ruleset,
applicable rules, inherited-rule listing, and repository merge settings. The
existing Codex policy projection and live observer both completed successfully:
INSTALLED, ACTIVE, ALIGNED, and behavioral proof NOT CLAIMED. The public observer
could not read legacy branch protection (401); the separate authenticated
preflight returned 404, `Branch not protected`. Do not conflate that limitation
with a failure of the active ruleset or silently call the observer comprehensive.

All three synthetic PRs completed their positive controls. No PR remained open.
After observation capture, request `0160` archived the ID-verified fixture;
`0161` confirmed the same repository archived. Its rules/history are retained,
not deleted. No production rule, bootstrap, runtime promotion, or standing
publication activation was changed.

`provider-negative-001.json` summarizes the observations and remaining gaps.
`provider-negative-001.responses.json` retains 166 intent/outcome pairs with UTC
times, GitHub request IDs, scoped inputs, and minimized response projections.
Full errors and rule parameters remain; irrelevant repository/user metadata is
omitted. Digests link the projections to the complete operator-local capture.
This is recorded operator evidence, not a provider signature or an unforgeable
independent audit. Original local captures and the execution-wrapper digest are
retained for reconciliation; no token or authorization header was captured.

## Remaining acceptance work

Stale approval remains PENDING: no separately authorized non-author reviewer was
provided for this run. No approval or dismissal event was manufactured. The zero
required count does not waive this row. A future bounded exercise needs a real
eligible reviewer; the current fixture was archived rather than left writable.

Full-mirror admission remains BLOCKED by the integration-ID rejection. Final
acceptance must explicitly map the isolated observations, current production
configuration, existing source-bound App denial evidence, and governed maintenance
proofs to each Phase 10 obligation. This record does not claim that combination
has already been accepted or that isolated tests are production equivalence.
The semantic framework and provider-adapter qualification remain separate evidence.

`effective_enforcement_proven` stays false. Stage D maintenance liveness remains
at its existing proven/disarmed state. No phase or proof flag is advanced here.
Regression tests validate artifact digests, operation scope, negative/positive
pairs, cleanup, and conservative claims. They do not re-execute provider tests.

## Primary references

The API behaviors and their limits were checked against the GitHub documentation:
https://docs.github.com/en/rest/repos/rules
https://docs.github.com/en/rest/git/refs
https://docs.github.com/en/rest/pulls/pulls
https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets

## Data representation and verification

The checked-in response artifact is JSON data, not an executable pinned package.
Its digest is explicitly defined over sorted compact ASCII JSON plus one LF.
Tests reconstruct that serialization, reject duplicate keys, and distinguish data
changes from Git's Windows checkout line endings. Original operator-local capture
hashes are retained separately. This applies the REC-D-014 distinction without
weakening any historical runtime, publisher, or raw Git-object source check.

On the operator machine, the initial twelve evidence tests passed and the complete
suite ran 146 tests: 145 passed, one host-restricted symlink case skipped. The
privileged-maintenance and append-only history verifiers and diff check passed.
Two additional tests cover portable JSON serialization and duplicate-key rejection.
Final local discovery ran 148 tests: 147 passed and one host-restricted symlink
case was skipped. All fourteen new evidence tests passed. The final CI result
is recorded on the PR after observation. The known historical
Windows checkout-byte verifier limitation is not silently reclassified as success;
the unchanged full foundation gate must pass in GitHub CI before merge.
