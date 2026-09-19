# Phase 10 provider-negative acceptance plan

Recorded: 2026-09-20 (Asia/Jakarta). Implementation-local, non-normative.

## Baseline and actual scope

The owner requested continuation of the remaining Phase 10 provider-negative
proofs. This increment supplies a non-executing planner and its regression tests,
plus the operator admission and acceptance procedure. It does not create a test
repository, install a ruleset, issue a permit, use an App key, or run live attacks.

Reviewed baselines:

- Codex main: `107f0dc53e873ef6d24a9f12cd28da7348f79331`.
- Authority main: `ad1327bcee00a1e2622916b77a209dcec8b8c14a`.
- Production rule source: `scnehaux/codex`, `main-governance`, ID `23193929`.
- Current production selector: `~DEFAULT_BRANCH`; active; no bypass actors.
- External check: `Codex Governance Authority`, integration ID `4864946`.
- Stage D maintenance liveness remains proven by the existing PR #23 evidence.
- Bootstrap and standing controlled publication remain disabled.

The ten existing Phase 10 exit obligations in [PLAN] and [ROADMAP] are not changed.
A configuration read is not a rejection test, and a disposable test is not itself
an observation of the production branch. `effective_enforcement_proven` stays false.

## Administrative path

Use the operator's explicit GitHub CLI browser login. Do not obtain a password or
token by reading Git Credential Manager, browser profiles, `.env`, or private keys.
The credential-bearing admin client is separate from the credential-free evaluator
and the dedicated App publisher. Creating a repository ruleset needs repository
Administration write permission [RULES-API]; logging in does not grant permissions
that the account does not already have.

On the authorized Windows host, GitHub CLI 2.101.0 was installed as a portable
binary under the project's LOCALAPPDATA operational directory. The release ZIP
SHA-256 matched the official release checksum:
`bc6c814367b193cd8e713611d61e36013c0ef843b8f516458fe3eda039192794`.
This verifies release-byte integrity under the official HTTPS/release trust
assumption; it is not an independent software audit. No PATH change or Git
credential-helper replacement was made. The observed auth preflight was not logged
in. A separate visible login window was opened for the operator; that is not proof
that login succeeded.

The ordinary browser flow stores credentials in the system credential store when
available, but the CLI can fall back to a plaintext file [CLI-AUTH]. Check the
reported storage before admitting live admin execution; do not use an insecure
storage flag or print/export the credential. Normal OAuth permissions can be wider
than one disposable repo, so the transport must also constrain every mutation to
the recorded disposable repository name and numeric ID. Do not request organization
administration, `delete_repo`, or additional App installation scope for these tests.

## Scope preparation and admission

`scripts/prepare_provider_acceptance.py` consumes an operator-captured ruleset JSON,
its associated Codex revision, and a unique run ID. It emits one new plan file.
There is no network client, credential access, `--write`, or `--execute` option.
It validates this reviewed baseline and refuses source identity, bypass, selector,
review, check-source, or rule-type drift. It retains extra provider rule fields
rather than silently dropping them. Future policy changes require a new review.

Example, using already captured local data:

```powershell
python -I scripts/prepare_provider_acceptance.py `
  --source-ruleset <captured-ruleset-json> `
  --source-revision 107f0dc53e873ef6d24a9f12cd28da7348f79331 `
  --run-id <yyyymmddThhmmssZ-lowercase-plus-eight-hex-suffix> `
  --output <new-plan-file>
```

The actual run-ID grammar is lowercase `yyyymmddthhmmssz-xxxxxxxx`.
The input revision and snapshot are caller-supplied observations, not cryptographic
proof of their relationship. Plan hashes bind content, not approval or freshness.
The planner's exclusive file creation prevents accidental overwrite; this is not
the crash-durable operational evidence writer used by Authority.

Admission for a separate live execution requires:

1. Re-read production main, repository merge settings, effective branch rules,
   inherited rules and bypass state. Retain raw public snapshots with timestamp,
   request ID, source revision and content digests. Run the existing Codex observer.
2. Create a NEW synthetic-only repository named
   `scnehaux/codex-provider-proof-<run-id>`. Never reuse an existing repository.
   Record its numeric ID and a unique fixture marker before later mutations.
   A public fixture may be used for Free-plan ruleset availability [RULES-CREATE];
   never copy private project content, actual credentials or operational permits.
3. Install the complete mirror on its real default branch and read it back.
   Compare every copied rule and parameter, selector, active state and bypass list.
   Record repository-level and inherited-policy differences separately. A successful
   create response alone is insufficient.
4. Preserve the App integration ID in the mirror. If GitHub will not accept that
   binding without installation, record exact-mirror setup as BLOCKED. Do not widen
   the production App installation or replace it with a user status.
5. For isolating a control's effect, use explicitly labeled separate fixture
   branches and only that control's copied rule. Record all omitted controls and
   the selector delta. These are mechanism tests, not fully equivalent deployments.

Generated payloads cover the full mirror and deletion, non-fast-forward and
pull-request isolation fixtures. They are planned payloads only. Failure-check
fixtures and live orchestration are not implemented by this planner.

## REC-D-016 — Demonstrate which control rejected the operation

Status: selected for acceptance planning; live execution pending. Proposer:
assistant. Owner: project owner. Lenses: first principles, systems thinking,
evolutionary fitness functions. This refines evidence quality, not existing policy.

A generic 403, 422 or blocked merge may be caused by invalid authentication,
insufficient permissions, missing required checks, invalid payloads or an unrelated
rule. A negative test passes only with a rule-specific observation or a controlled
before/after contrast. Retain the preconditions, attempted request without secrets,
response status and sanitized reason, unchanged target identity, and positive
control. A timeout or missing response is UNKNOWN, never a negative-test PASS.

The default-branch deletion API documents rejection of default-branch deletion
independently of the custom ruleset [REFS]. Therefore one such rejection must not
be labeled proof that the custom deletion rule fired. Test the copied deletion
rule on a non-default fixture branch as well. Force-update probes must be genuine
non-fast-forward changes with `force=true`; a no-op or ordinary fast-forward
rejection does not exercise that mechanism.

Alternatives rejected: destructive probes on production, treating every failure as
success, and relaxing production checks to isolate a test. Separate fixtures cost
more setup but avoid both production risk and misleading causal claims. Revisit
if GitHub exposes trustworthy per-rule evaluation results that remove ambiguity.

## Acceptance matrix (all new live rows initially pending)

| Existing obligation | Required observation and scope limit |
| --- | --- |
| Direct push rejected | Complete mirror rejects a genuine new default-branch update; same actor can mutate a control ref; target SHA remains unchanged. |
| Force push rejected | Genuine non-fast-forward forced update is rejected by the mirrored or isolated non-fast-forward rule; ordinary permissions and payload validity are independently demonstrated. |
| Default-branch deletion rejected | Disposable real default branch deletion is rejected; separately prove the custom deletion rule on a named non-default branch with an unprotected deletion control. Never attempt production deletion. |
| Failing governance PR cannot merge | Observe a failing required check and a rule-attributed denial. Synthetic status fixtures prove provider mechanics only, not real Codex qualification or App authority. Use existing source-bound production evidence separately. |
| Review behavior matches active policy | Verify active zero-approval bootstrap, current merge restrictions and successful governed path. Do not claim the normative independent-review target is already achieved. |
| Required unresolved thread blocks merge | Hold candidate and other gates constant; unresolved thread denies merge; resolving that thread allows the otherwise-valid operation. A PR already blocked by missing checks is inconclusive. |
| Stale approval handling | An independently authorized non-author reviewer approves; a reviewable new commit follows; retain before/after review identity and dismissal observation. With no reviewer, keep this PENDING, not implicitly waived by a zero required count. |
| Disallowed merge methods | Test merge/rebase rejection with a valid candidate and inspect both repository settings and ruleset; squash positive control. Distinguish repository-level denial from ruleset attribution. |
| Desired/effective parity | Re-run the existing production observer before/after the fixture exercise; preserve revision and any observation limitations. ALIGNED is configuration evidence, not all behavioral evidence. |
| Provider cannot redefine neutral semantics | Link the existing Codex semantic/adapter qualification and Authority trust evidence; fixture success does not replace those controls. |

## REC-D-017 — Bound disposable evidence and completion claims

Status: selected for acceptance planning; operational adoption pending. Proposer:
assistant. Owner: project owner. Lenses: systems thinking and evolutionary
architecture. Preserve `REC-D-008` and `REC-D-011` rather than inventing a new policy
engine or a permanent test platform.

Separate full-mirror readback, individual isolated-control behavior, production
configuration parity, and actual production governed merges in the final evidence
map. Unknown inherited rules or App-source differences must not disappear during
normalization. A copied ruleset on another repo is not literally the same trust
boundary. The final acceptance review must explicitly assess that mapping.

Admin capability alone does not resolve every prerequisite. In particular, a
stale-review experiment requires an actual eligible second reviewer. One assistant
operating both repositories is not independent human approval. Keep any missing
row pending unless a separately reviewed governance decision changes applicability;
do not silently turn it into NOT APPLICABLE or advance the overall proof flag.

Trade-off: this keeps completion conservative and may require another operator.
It avoids a convincing but unsupported claim of production equivalence. Review
again on changes to rules, roles, provider behavior, inherited policies or topology.
This is not a claim that the new planner is battle-tested.

## Evidence retention, abort and cleanup

Before each live mutation, persist a sanitized intent identifying the fixture repo
ID, resource, precondition SHA and expected result. Retain its outcome separately.
Never retry an ambiguous mutation blindly or erase its journal. An unexpected
allowed operation stops that test sequence; preserve the fixture for diagnosis.

After success, close synthetic PRs and archive only the newly created, ID-verified
repository after exporting observations. Preserve the fixture's rules and history
for inspection; repository deletion and `delete_repo` scope are unnecessary. Do not
change production rules, disable production checks, install the authority App in
the fixture, or use its key to manufacture synthetic successful checks. A cleanup
failure remains open work and cannot be hidden by the final report.

The existing maintenance-path proof stays true only under its existing invariants;
this increment does not modify it. No phase closes and no proof flag advances until
the actual evidence matrix, applicability decisions and cleanup are reviewed.

## Verification and references

The added unit tests use explicitly synthetic rule snapshots. They test identity
and policy drift rejection, full-rule preservation, isolation labels, deterministic
output, duplicate/invalid JSON, exclusive output and false proof claims. The
standard Authority Foundation discovery runs them without new workflow privileges.
CI and operator-machine results belong in the PR verification record.

[PLAN]: https://github.com/scnehaux/codex/blob/107f0dc53e873ef6d24a9f12cd28da7348f79331/PLAN.md
[ROADMAP]: https://github.com/scnehaux/codex/blob/107f0dc53e873ef6d24a9f12cd28da7348f79331/ROADMAP.md
[RULES-API]: https://docs.github.com/en/rest/repos/rules
[RULES-CREATE]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository
[REFS]: https://docs.github.com/en/rest/git/refs
[CLI-AUTH]: https://cli.github.com/manual/gh_auth_login

Provider review/merge semantics are documented at
https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets .
These references describe mechanisms, not certification of this implementation.

## Operator verification observation

On the existing Windows checkout, unittest discovery ran 134 tests: 133 passed
and one host-restricted symlink case was skipped. Foundation, staged publisher,
privileged-maintenance and attestation-history verifiers passed. The historical
`verify_publisher_proof.py` stopped on checkout-byte drift in
`integrations/github-app-publisher/github_app_publisher.py`: working blob
`e304f29b46804e6e02672fae4d55093d80698697`, committed blob
`4ee2e9937b17bb157b702bcc8f6d10a33ca71e6c`. The file contained CRLF and converting
only CRLF to LF produced the committed bytes exactly.

No historical verifier, publisher source or proof hash was modified to hide that
result. This is the checkout representation distinction already discussed in
[REC-D-014](0006-git-object-byte-portability.md). It is not a full Windows gate PASS.
The unchanged historical gate must still pass in the repository's GitHub CI;
operational publisher exports continue to require exact committed bytes.
