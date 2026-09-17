# Controlled publication and retained bootstrap evidence

Recorded: 2026-09-17 (Asia/Jakarta). Implementation-local, non-normative.

## Scope and reviewed baseline

The project owner instructed us to continue from the review of Authority PR #14.
That PR was reviewed for its disabled staging scope and squash-merged at
`e4b6c52f5d1ad60008bdf85f860cbdadc7e56ed8`. The review is an assistant code review,
not a claim of independent human approval. Codex PR #22 remains the installing
candidate at `eaa5b41cd84fcc77fd1ff464120d4be83c57d1cd`; it is not promoted or merged
by this work.

Read [the recommendation ledger](0002-stage-d-recommendation-ledger.md),
[the v2 handover note](0003-attested-runtime-handover.md), and
[the maintenance lifecycle](../privileged-maintenance.md) with this record.
The plan's intent and repo responsibilities do not change. This increment closes
implementation gaps between evidence preparation and a controlled publication
attempt; it does not supply live activation or claim Stage D completion.

## Findings and selected implementation

The old `issue_privileged_permit.py` writes a legacy decision record and prints
the attestation digest, but does not retain the original runtime JSON and the
committed attestation together in that decision evidence. Separately, the old
publisher's `Config.load` deliberately pins the old runtime revision. Merely
passing an offline parser preview is not a live publication implementation.

`controlled_evidence.py` supplies an additive evidenced bootstrap wrapper, using
only the four historically promoted Codex files. It verifies their raw blobs,
runs a private byte snapshot through the bounded runner, validates the original
FAIL and independent qualification, and uses the existing privilege-only
attestation authorization semantics. It does not evaluate the installing
candidate using its new reader, nor introduce a new path-classification engine.

The public bootstrap preparation function still reads the fixed existing
`governance/privileged-maintenance.json`. Disabled stops before Git access,
runtime execution, attestation reads, and output writes. When separately enabled,
the authority checkout must be clean main matching origin/main and the expected
origin URL. Attestation and maintenance bytes must match regular-file Git tree
entries at that exact Authority revision. The original JSON, approval origin,
policy bytes, final decision, and package identities enter evidence; a receipt
links evidence and permit before a permit is returned. Remote tracking freshness,
administrator identity and host trust remain operator obligations, not properties
proved by a local Git command.

`issue_controlled_permit.py` exports a permit only after evidence and receipt
preparation succeeds. Its two modes call the fixed-policy public preparation
functions for bootstrap-v1 and attested-v2. There is no caller-supplied facts or
source-pin option and no publisher key. The old issuer is retained for historical
compatibility; it is not the issuer for the new receipt-required publication
contract.

`controlled_publisher.py` introduces an explicit new configuration contract rather
than weakening the historical publisher loader. It supports both evidence forms,
verifies the complete evidence/receipt/permit relationship from one in-memory
snapshot, revalidates the full v2 result or original bootstrap result and approval,
and preserves the actual runtime revision in the permit. It reuses the old
publisher's narrowly scoped App authentication, installation verification,
transport and check-response verification. No candidate/runtime execution occurs
in this credential-bearing boundary.

All default governance remains disabled. `governance/controlled-publication.json`
contains no activation or binding. The CLI defaults to preview and a disabled
configuration performs no input, key, journal or provider work. No active config,
real attestation, credential, proof artifact or enabled bootstrap is added.

## Publication activation contract and operation

A separately reviewed `candidate-proof` activation must bind the exact repository,
PR, base and head; bootstrap-v1 or attested-v2; full runtime package; Authority
service revision; publisher revision and the entire enumerated source/dependency
closure; and permit, evidence and receipt digests. The fixed repository, context,
App and installation identities are not caller-selectable. Source manifests are
integrity checks within a trusted operator export, not signatures or proof that
an attacker-supplied configuration has been approved.

An active window has explicit UTC not-before and expiry times, at most 900 seconds.
This is a conservative implementation choice for a serialized proof, not a
latency SLO or a universal best practice. It may require a new reviewed activation
when preparation takes longer. No timestamps are populated in the checked-in
config. Time is rechecked immediately before the check POST; the trusted clock,
provider call duration and residual check-to-use race are explicit assumptions.

Live execution requires an independently trusted export outside every Git
checkout and exact repository/SHA confirmations in addition to `--write`. The
public CLI has no alternate config, endpoint, conclusion or runtime identity flag.
All enumerated publisher source/dependency files are checked before credential
access. Installed interpreter/dependency trust and approved source-to-commit
binding remain deployment responsibilities; source hashes do not prove them.

The public qualification read checks the exact latest successful GitHub Actions
check ID retained in evidence; a rerun, missing/ambiguous check, wrong source or
failure stops publication. This adds only a credential-free fixed-host GET, not
another governance evaluator. The PR must still be open, non-draft, same-repository,
and bound to the exact base/head. The existing scoped App token permissions and
one check POST are retained. Token revocation is attempted even when validation
after token issuance fails.

## REC-D-013 — Reserve before side effects; reconcile ambiguous outcomes

Status: selected for this implementation candidate, not operationally adopted.
Proposer: assistant. Owner: project owner; operational reviewer unassigned.
Review lenses: first principles, systems thinking, evolutionary architecture.
References: the AWS Builders' Library retry discussion [retries], GitHub's check
creation contract [checks], and Python's filesystem primitives [fsync].

The publisher writes an exclusive, durable attempt record before key access.
It is keyed by repository, PR and head in the designated export's existing
`publication-state/` directory. It then writes a separate outcome; it never deletes
or overwrites the attempt. Concurrent/repeated use of that candidate in the same
state directory cannot blindly issue another POST. A timeout after a possible
write is `publication_uncertain`; a verified check followed by cleanup failure is
`published_cleanup_failed` with the known check ID retained. An outcome write
failure still leaves the attempt reservation. Secrets and upstream bodies are
not written to this journal.

The alternative, automatic POST retry, can duplicate a side effect after a lost
response. A distributed deduplication service would be larger than the current
single-operator requirement. The selected local journal deliberately trades
availability for inspectable fail-closed recovery. It is NOT provider-side or
global exactly-once behavior. Copying the export, choosing another state directory,
or privileged deletion defeats local deduplication; one designated host/state
location and operator serialization are required. GitHub's `external_id` is not
assumed to be an idempotency key. Do not erase attempts to retry; reconcile the
provider observation, receipt, candidate and any token-cleanup uncertainty under
a separately reviewed recovery decision.

Revisit on hosting, concurrent operators, multiple machines, replay/revocation
requirements, provider behavior, or activation-window changes. Tests cover lost
response, wrong-source response, qualification/candidate drift, token cleanup
failure, source tampering, failed attempt/outcome writes, replay and strict inputs.
These are synthetic fault tests, not evidence of a real production incident or a
claim of battle-tested operation.

## Other recommendation dispositions

REC-D-004: explicit new publication contract accepts the actual v2 runtime identity
and the evidenced bootstrap-v1 form; the old loader/proof stays unchanged.
REC-D-005: evidence retains original FAIL, approval and original source bytes;
receipt links are verified again by the publication boundary, not just preview.
REC-D-006/007: disabled defaults, scoped activation, expiry, persistent attempt and
abort/reconciliation behavior are implemented; live disarm is still not performed.
REC-D-008: actual Codex source is exercised with synthetic APIs and mocked publisher
calls; live post-disarm maintenance is still a separate acceptance obligation.
REC-D-001/002/003/012: source and exact-candidate binding, strict parsing and bounded
private execution remain. No currently promoted package is silently replaced.
REC-D-009/010/011: no new status database, hosting, queue, generalized engine or
administrative model. Current permissions, operator independence and deployment
provenance must be reviewed before any activation; no such proof is invented here.

## Evidence, recovery and durability limits

Decision, receipt, permit, attempt and outcome are additive files with exclusive
creation, file fsync and POSIX directory sync/readback. Windows has no portable
directory-sync guarantee here. Disk/hardware loss, retention, replication and
untrusted filesystem semantics are outside the demonstrated guarantees. A failure
can leave an orphan record; absence of a final record is not permission to rerun.
Neither a plain permit nor a receipt is a cryptographically unforgeable capability.
Only a trusted independently administered activation binding the exact digests
allows this publisher to use the App credential.

Before a real bootstrap: complete code and exact-candidate review; verify merged
trusted Authority source, the unchanged legacy runtime package, and the controlled
export; approve the actual operator/credential boundary; prepare the exact
attestation and bootstrap activation through review; run the controlled issuer;
review captured evidence and bind a short-lived publication activation to its
exact digests. Do not pre-approve guessed future hashes. A failed prerequisite
means stop, not removal of required checks.

After publication: retain the provider result and cleanup observation, merge Codex
only through the required source-bound check, and promptly disable the completed
activation/bootstrap through reviewed changes. Independently promote the merged
new runtime package and prove a subsequent protected maintenance operation with
the bootstrap disabled. Keep the old safe package available for fail-closed
recovery; it may not restore maintenance availability. All applicable Phase 10
proofs remain required. No destructive operation on a default branch is performed
or authorized by this implementation PR.

## Verification record

Local syntax compilation was performed. A full local clone failed because the
container could not resolve github.com; no local full-suite PASS is claimed.
The added unit tests run in standard Authority Foundation discovery. The existing
read-only compatibility workflow is extended, without removing any old step, to
exercise actual Codex reader and legacy collector outputs through both controlled
chains using synthetic API facts and a fake publisher transport. Its successful
`published` test result is a mocked outcome, not a real GitHub check.
CI results and final source hashes must be recorded on the PR after observation.

## Primary references

[retries]: https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/
[checks]: https://docs.github.com/en/rest/checks/runs#create-a-check-run
[tokens]: https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app
[fsync]: https://docs.python.org/3.13/library/os.html#os.fsync

The token-scoping behavior used here follows the App installation-token mechanism
[tokens]. These sources explain mechanisms and failure modes; they do not certify
this code, eliminate the operator trust boundary, or demonstrate live enforcement.
