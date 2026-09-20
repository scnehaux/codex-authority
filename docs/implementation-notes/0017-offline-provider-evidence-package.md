# Offline provider evidence review package

Prepared: 2026-09-20. Implementation-local, non-normative.
Status at preparation: sandbox review package; not applied to the repository.

## Scope

This package prepares selected evidence files and read-only regression tests for
`scnehaux/codex-authority`, against the observed baseline
`11d13b4ec7b9dd0051116d73e33d785f3d2651fa`.
The observed Codex baseline is
`107f0dc53e873ef6d24a9f12cd28da7348f79331`.

The underlying operations occurred earlier. This packaging step does not run a
new provider experiment, execute candidate or publisher code, access a private
key, issue a capability, approve a PR, alter rules, or advance acceptance.

A local branch-creation call through Desktop Commander was denied before execution.
It was not retried through another execution path. Read-only capture retrieval
remained available. The files in this package were therefore created and tested in
the ChatGPT sandbox, not in the operator checkout or GitHub. The exact reason for
the tool denial was not supplied; it is not diagnosed here as a false positive,
GitHub permission failure, or evidence that all file writing is prohibited.

## Files and provenance

The package adds four JSON files under `governance/evidence/`:

- `provider-qualification-negative-001.json`: selected observation of Codex PR #25,
  its actual failing check, Authority refusal, normal merge denial and unchanged main.
- `provider-qualification-negative-001.runtime.json`: the returned Authority
  envelope, with the embedded runtime wire string checksum-verified against the
  original capture. The enclosing JSON has been reserialized.
- `provider-git-transport-001.json`: selected native Git transcripts, exclusions,
  unknown API outcomes and cleanup observations from the disposable fixture.
- `provider-evidence-package-001.json`: canonical-data digests and explicit
  packaging-time status and non-claims.

Source records were read from the previously authorized operator directories:
`runs/pr25-qualification-failure-e1b58e8-01/` and
`runs/provider-negative-20260920t144552z-7ef80d36/`, below the project's operational
LOCALAPPDATA directory. Relative capture filenames are retained in the JSON.
These are selected projections from returned file content, not an assertion that
all original local file bytes were copied into this archive. Irrelevant personal
metadata, account avatars and unrelated provider response fields are omitted.

The ten qualification request/outcome pairs and eighty transport API pairs remain
in the original local recordings. The package does not claim to contain all of
those pairs. Repository IDs, candidate SHA values, selected provider request IDs,
HTTP outcomes, stdout/stderr observations and original limitations remain visible.

## Qualification failure chain

Codex PR #25 had exact head
`e1b58e898fe2428faebbc8f5aba2941fc7ef9b1e`. Its real `Governance Qualification`
job `106095659722`, run `35517446154`, failed at `Validate document formatting`.
The intentionally unformatted Markdown file was the only changed path. The setup,
SCM checks and Python quality steps succeeded; subsequent qualification steps were
skipped. This is not a claim that the full framework suite ran on that candidate.

The promoted credential-free runtime reported `candidate-qualification-failed`.
The issuer recorded FAIL evidence but did not create a receipt, permit or Authority
check. A normal exact-head squash request returned HTTP 405. That denial involved
one failing required check and one expected check; it is not falsely attributed
to the candidate qualification gate alone. Existing isolated status controls are
separate supporting evidence, not implicit acceptance of the entire production chain.

The original runtime wire checksum is:

```text
11fc9baebef84a6f56fe4aca4e7ef2b02a90c635ece797f40dec6fbe1e48f811
```

The embedded string reproduced from returned content matches that SHA-256 exactly.
Its CRLF bytes are retained. Only the outer envelope's JSON representation changes.
A matching hash establishes content consistency with the captured checksum, not
provider signature, independent audit, or authority to publish a successful check.

## Native Git observations and excluded results

Fixture: `scnehaux/codex-provider-proof-20260920t144552z-7ef80d36`, ID `1378442804`.
The selected data retains five completed native Git observations: an unprotected
update, a default-branch direct-update denial, creation of a fresh force control,
a successful forced rollback on that control, and denial of the same rollback on
the isolated protected force branch. The errors identify GH013 and the applicable
PR/non-fast-forward control. Production main is not a target in these transcripts.

The hung earlier Git client has no proof credit. The deletion attempt with client
error and subsequent absent ref also has no positive-proof credit. Null HTTP
responses and timeouts remain UNKNOWN; they are not translated to successful
provider rejections. The final native deletion sequence was tool-blocked before
execution, so native default-deletion proof remains unclaimed. Existing REST
custom-deletion/native-default-guard evidence is not rewritten or relabeled.

The archived fixture identity and zero-open-PR readback are retained with selected
request IDs and timestamps. This is historical cleanup observation, not a claim
that the sandbox performed cleanup or freshly changed any repository.

## Serialization and verification

Manifest data hashes use sorted compact ASCII JSON with separators `,` and `:`,
non-finite values rejected, followed by one LF. Tests reject duplicate keys and
bound input size. This makes outer JSON formatting and checkout line endings
independent of the data hash. The embedded raw runtime string has its own byte hash;
normalizing that string's CRLF would correctly fail its checksum test.

`tests/test_provider_evidence_package_001.py` uses the Python standard library and
reads these files only. It has no Git, shell, provider API or credential client.
Thirty tests passed in the ChatGPT sandbox. They check recorded-data integrity,
linked identities, original FAIL preservation, no permit/publication, negative
and positive comparisons, timestamps, excluded outcomes, cleanup, path restrictions
and conservative scope claims. They do not establish fresh live behavior or perform
a complete repository qualification. See the package-level verification files.

The packaging-time `integration_state` and false CI/acceptance claims are historical
observations. A later integration or acceptance decision requires its own record;
this package must not silently present those outcomes as already completed.

## Acceptance and pending integration

REC-D-018 remains Proposed. This package does not resolve or waive full-mirror
admission, evidence transfer to production, independent-review requirements, or
any remaining Phase 10 obligation. `effective_enforcement_proven` stays false.
Historical evidence, governance contracts, workflows and runtime source are unchanged.

Repository application, review, and the unchanged full CI gates remain pending.
No script in this package automatically applies files, creates a branch, submits
a PR, merges changes, or retries the denied tool operation. The companion review
note separates these remaining steps from the completed sandbox data preparation.

## Source discussion records

- Acceptance record: https://github.com/scnehaux/codex-authority/issues/28
- Actual qualification probe: https://github.com/scnehaux/codex/pull/25
- Probe observation: https://github.com/scnehaux/codex/pull/25#issuecomment-5750631347
- Prior isolated observations: https://github.com/scnehaux/codex-authority/pull/26
- Stale-review observation: https://github.com/scnehaux/codex-authority/pull/27

These links and capture references identify the source record; they do not turn
this offline archive into a provider-signed or independently approved artifact.

## Repository integration follow-up

The preceding sections and the manifest describe the original packaging-time
checkpoint, not a live integration status. After the owner explicitly requested
integration of these reviewed files, the narrowly scoped local branch operation
succeeded through Desktop Commander on `evidence/offline-package-001`. No safety
setting, permission, credential or alternative transport was changed for that
operation. The cause of the earlier denial remains unknown; this observation does
not retroactively diagnose it or authorize any previously blocked live test.

The qualification and Git JSON projections were rebuilt directly from the named
operator captures and checked against all three canonical digests in the original
ZIP before exclusive file creation. Each selected Git intent/outcome was compared
to its individual capture file. The runtime wire retained its original checksum.
The manifest and test source were also matched byte-for-byte to the reviewed ZIP.
The original package files are otherwise unchanged; this follow-up and a README
link provide current navigation without rewriting historical observation claims.

The original manifest intentionally retains `not_applied_to_repository` and its
packaging-time false CI field. Those fields are historical, not a condition that
must keep this PR unmerged. Actual integration and unchanged full CI outcomes are
recorded in the integration PR and its verification comment after they occur.
Issue #28 remains the separate acceptance decision record. Merging these files
resolves this selected evidence-package integration only, not Phase 10 acceptance.

### Integration verification on the operator checkout

The 30 package tests passed on the Windows operator checkout after integration.
Full Authority unittest discovery ran 186 tests: 185 passed and the existing
host-restricted symlink case was skipped. Foundation, staged-publisher,
privileged-maintenance, attestation-history and diff checks passed.

The unchanged historical `verify_publisher_proof.py` failed on checkout bytes of
`github_app_publisher.py`. A read-only comparison confirmed the working bytes
become exactly the committed bytes when CRLF is represented as LF. No source,
checker, expected blob, Git setting or proof flag was changed to suppress that
failure. Therefore this is not a full local-gate PASS. The unchanged historical
gate must pass in GitHub CI before merge. Detailed local logs are retained under
`runs/evidence-package-integration-20260920T180640Z/` in the operational directory.
