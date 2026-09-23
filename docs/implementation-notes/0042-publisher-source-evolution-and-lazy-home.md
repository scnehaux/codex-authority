# REC-D-019 - Publisher source evolution and lazy home resolution

Recorded: 2026-09-24 (Asia/Jakarta). Implementation-local, non-normative.
Proposer/implementer: assistant. Decision owner: project owner.
Status: source-maintenance proposal implemented and tested for protected PR review;
no independent human review, runtime promotion or publication authorization claimed.

## Observation and invariant

Authority baseline `beba31cd9404c4cd0921fe029fb7a18fcc2dbd44` contains two distinct
problems. `publisher_transport.default_key_path` eagerly evaluates `Path.home()`
inside the default argument of `os.environ.get`, even when LOCALAPPDATA is present.
The historical proof verifier also compares today's checkout against PR #17's
publisher hashes, conflating historical evidence integrity with current source
qualification. Fixing the resolver therefore fails the old check even though the
original Git commit and evidence remain unchanged.

Preserve immutable evidence and exact current source verification, while allowing
reviewed source evolution. Source changes must never imply effective promotion.
The prior execution-tool restriction is independent and remains in force.

## Smallest coherent change selected for source review

Fix the existing resolver in place. Query the home directory only when LOCALAPPDATA
is absent. A present but blank, relative, drive-relative, traversal-bearing or
control-character location fails closed instead of silently selecting another
credential location. Valid absolute locations, spaces, Unicode and the POSIX
home-based default retain their meaning. No filesystem read or authentication is
introduced by resolution. The existing private-key and transport boundaries remain.

Keep `PUBLISHER_FILES` and `AUTHORITY_REVISION` unchanged as the historical proof
identity. `read_historical_publisher_source` now verifies original commit/path,
regular-file mode, blob ID, bounded size and raw bytes using Git objects. Replacement
objects and inherited GIT_* redirection are disabled. Fixed process-local protocol
and prompt denial prevent lazy-fetch transport, including on Git 2.39. Missing history fails closed;
there is no fallback to HEAD, checkout content or network fetching.

`CURRENT_PUBLISHER_FILES` separately pins development-checkout bytes. Its only
changed source is the resolver-containing transport file. Proof verification checks
both historical and current identities. The offline diagnostic and LF checkout test
consume these current pins, not historical ones. Neither pin set is a publication
capability or a new operational promotion mechanism.

The dedicated-App publisher still requires an independently bound candidate,
evidence/receipt/permit, complete source manifest from an exact selected revision,
valid activation window, explicit execution authorization and a single journaled
attempt. This change performs none of those operations. Old exports and activations
are not updated or reused.

## Alternatives and consequences

Doing nothing preserves the bug and makes the preflight merely diagnose failure.
Adding another publisher/resolver path preserves every old checkout pin but creates
parallel live logic and retirement work. Rewriting old expected hashes would falsify
which source the historical proof actually exercised. This in-place change retains
one current resolver while separating two legitimately different source identities.

Costs: the historical verifier now needs local Git and the original commit's objects.
CI already checks out full history. A shallow/missing-history clone must not claim
historical verification. The current source pin must be deliberately updated in
future source-maintenance PRs; activation remains separately pinned and gated.

## Acceptance and evidence

Eight resolver tests reproduce failure before the fix and pass after it, including
a native minimal Windows process with LOCALAPPDATA but no home variables. Invalid
explicit configuration and absence of both supported locations remain blocked.
Eleven source-evolution tests preserve original hashes and test current-file mutation,
missing history, bad tree/mode/path/blob/size, redacted Git errors and real commit/blob
replacement refs. The offline preflight's missing-both-locations denial is explicit.
All tests use synthetic locations and do not access operator credentials.

Local evidence is under `temp/codex-resolver-evolution-20260924-032329` in the parent
workspace. Test-only results are not live publication evidence. PR/CI and final
qualification identities must be read from their actual records, not inferred here.
No historical evidence, attestation, governance activation, promotion, provider rule,
Codex candidate or architecture-admission state is modified.

## Abort and next boundary

Keep publication disabled. A source merge does not deploy the resolver or lift the
execution-tool restriction. Historical stop evidence remains valid. Do not attempt
live execution through a different tool or credential path to evade that restriction.
Any operational source selection requires a new separately authorized lifecycle.
Slice 11.6 remains open until its actual required App check and governed merge exist;
this work neither starts Slice 11.7 nor claims Governance 1.0 readiness.

## Primary references and limits

Python documents that Path.home can raise RuntimeError when home cannot be resolved:
https://docs.python.org/3.13/library/pathlib.html#pathlib.Path.home
Git documents object inspection and replacement-object controls:
https://git-scm.com/docs/git-cat-file
https://git-scm.com/docs/git-replace
https://git-scm.com/docs/git/2.39.0 (GIT_ALLOW_PROTOCOL)
These references support the mechanics, not this project's operational readiness.
This recommendation refines REC-D-001/004; it does not supersede their separation
between source changes, promotion and effective execution.
