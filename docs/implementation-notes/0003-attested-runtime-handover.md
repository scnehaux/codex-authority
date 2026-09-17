# Staged attested-runtime handover

Recorded: 2026-09-17 (Asia/Jakarta). Implementation-local, non-normative.

## Scope, authority, and baseline

The project owner's instruction to proceed follows the proposal to prepare the
Authority integration for Codex PR #22 while leaving activation disabled. This
record selects implementation details for review, not privileged approval,
independent human review, operational promotion, or an enforcement claim.

Authority baseline is `62ef870399e295bfba70fa5b73b54261a6828a79` (documentation
PR #13). The Codex test input is PR #22 at
`eaa5b41cd84fcc77fd1ff464120d4be83c57d1cd`; its reader blob is
`c9a0c3bf2fd3c33be4deb1b1e5fc624d1b0b796a`. The installing candidate remains
unmerged and must not become its own effective authority.

Read the [recommendation ledger](0002-stage-d-recommendation-ledger.md), the
[existing maintenance lifecycle](../privileged-maintenance.md), and the
[reader contract][reader] with this record. These remain separate from normative
architecture artifacts, which belong in `scnehaux/codex-architecture`.

## What is implemented in this slice

`attested_contract.py` parses the explicit version-2 result into immutable wire
data. It rejects unknown shapes/versions, ambiguous JSON, non-boolean claims,
source-dependency drift, inconsistent candidate/qualification identities, and
unauthorized verdict rewriting. It validates the reported protected-path
partition and verdict consistency but does not independently classify policy
paths or collect GitHub facts. Governance evaluation still belongs to Codex.
Parsing data alone is not source verification, promotion, or publication authority.

`adapters/attested_runtime.py` verifies all five package files against independently
supplied identities before execution. It rejects extra/missing files, symlinks,
Git-checkout execution, and candidate-as-runtime identity. It executes a private
copy of the verified bytes with isolated Python, a small environment allowlist,
closed stdin, and bounded stdout/stderr. The interpreter and host remain trusted;
this is not an operating-system sandbox against a compromised trusted operator.

`attested_handover.py` connects that adapter to the existing `AuthorityService`
and version-1 permit issuer. The new evidence record retains the exact runtime
JSON bytes, original FAIL, final verdict, approval record, Authority snapshot,
source package, and decision summary. A separate receipt links the evidence
file digest, runtime output digest, candidate/source identities, and permit digest.
The permit is not returned until both writes succeed. Legacy evidence and permit
schemas are not rewritten.

The public `prepare_attested_permit` entrypoint reads a fixed Authority policy.
The checked-in policy is `staged-disabled`, with execution false and no runtime
package binding. It rejects a call before Git commands, runtime package reads,
execution, or operational evidence creation. A hypothetical enabled contract is
validated in tests only; no enabled configuration is committed. Later promotion
must explicitly bind a reviewed merged source revision and the complete five-file
package. It cannot use the current unmerged review head or the candidate's head.
Before execution it also requires a clean Authority main matching origin/main.
The privileged operator must fetch/verify the trusted origin before running it;
a local tracking reference alone is not proof of remote freshness or administration.

`attested_preview.py` verifies the permit/evidence/receipt links and reuses the
historical publisher's permit parser through a permanently disabled in-memory
configuration. It performs no HTTP request, loads no key, exposes no write flag,
and does not export that configuration as a live publisher configuration.

**Important limitation:** the historical publisher's `Config.load` still rejects
new runtime source revisions. Offline permit compatibility is not live publisher
compatibility. A separately reviewed credential-bearing v2 publisher/configuration
and receipt-verification integration is still required before permanent-path
publication. This slice does not silently relax the old source pin or pass the
new reader off as the historical runtime. The bootstrap publisher/proof issuer
also needs its own evidence-preserving activation review; this new v2 evidence
sink does not retrofit the old bootstrap adapter's original-result retention.

## State and source contracts

`governance/attested-handover.json` records the reviewed input separately from the
unbound effective runtime. Publication is `offline-preview-only`; both proof
claims remain false. No existing bootstrap flag, attestation record, generic
publisher configuration, historical source pin, or provider rule changes.
The new configuration is a narrowly scoped staging/promotion boundary, not a
second framework policy authority or a new general deployment platform.

The runtime and evaluator self-reports remain conservatively false. The adapter's
source verification comes from verified package bytes, not from changing those
self-reports. The reader's approval origin was collected through its pinned
Git-object API path. The Authority parser validates the evidence shape and canonical
attestation digest; it does not independently re-fetch that Git tree or recompute
the raw approval blob from a reformatted semantic object. The original raw blob
identity remains source-bound reader evidence, not a standalone signature.

## Decisions, alternatives, and plan impact

| Recommendation | Decision within this candidate and remaining limit |
| --- | --- |
| REC-D-001 | Preserve historical runtime/evaluator and use an additive adapter. Reviewed input metadata is not an effective source pin. |
| REC-D-002/003 | Consume snapshot-bound evidence with strict v2 validation. No new Authority-side network collector or policy classifier. |
| REC-D-004 | Exercise v2 result, existing service, durable evidence, v1 permit, and offline publisher parser together. Live v2 publisher/config compatibility is not yet delivered. |
| REC-D-005 | Add full-result evidence plus a permit receipt; preserve the pre-approval failure. Failure before receipt completion yields no returned permit. Bootstrap-v1 evidence extension is still a separate review item. |
| REC-D-006 | Keep execution/publication disabled; record abort, recovery, and post-merge promotion checkpoints below. No disarm or handover proof is claimed. |
| REC-D-007 | One-shot adapter/sink and exclusive output creation reject reuse of the same attempt. Different output locations are not a global replay-prevention mechanism. Serialized operation and ambiguous-write reconciliation remain required. |
| REC-D-008 | Add synthetic negative and positive integration tests. A real post-disarm protected maintenance operation remains required. |
| REC-D-009 | Do not conflate this slice with PLAN/ROADMAP status reconciliation. |
| REC-D-010/011 | No worker, queue, database, extra credentials, second policy engine, or new administration model. Actual operator/deployment independence remains a pre-activation obligation. |

The alternative was to expand the legacy runtime-result and publisher contracts
in place. That would couple new unpromoted code to historical proof verifiers and
obscure what the earlier proof actually established. Additive components cost
more files and later retirement work, but keep review scope and historical
compatibility explicit. Neither approach authorizes candidate self-promotion.

### REC-D-012 — Bound execution and preserve verified bytes

Status: selected for this implementation candidate; operational adoption pending
review. Proposer: assistant. Decision scope: new adapter only. Revisit on package,
interpreter, host, output-shape, or timeout changes.

Reasoning: a size check after unbounded buffering does not bound memory while the
child runs. Verifying a mutable file and later reopening it also needlessly widens
the verification-to-execution gap. The new adapter drains both pipes with a cap,
terminates on excess output, and executes its private verified byte snapshot.
Python documents that `communicate()` buffers data in memory [subprocess]. This
motivates a bounded implementation; it does not prove this runner secure.

The selected new budgets are 120 seconds waiting for the process and 512,000 bytes
per pipe. Per-file input is at most 1,000,000 bytes; the evidence writer retains
its existing 1,000,000-byte cap. These are fail-closed implementation limits, not
SLOs, worst-case latency guarantees, or changes to the old runtime budget. Process
creation and cleanup can add platform overhead. Oversized legitimate candidates
may be rejected and need an explicitly reviewed budget change, never an implicit
truncation of candidate paths or approval evidence.

Acceptance exercised locally: excess stdout and stderr, nonempty stderr, timeout,
exit/verdict mismatch, source tampering, missing/extra files, symlink paths,
ambient tokens/proxies/Python paths, and mutation of the original entrypoint after
verification. Tests use harmless synthetic programs, not candidate operational
execution. Host compromise and process-tree sandboxing are outside this proof.

## Evidence durability and recovery limits

Output directories must already exist outside every Git checkout. New files use
the existing exclusive-create writer with flush and file fsync. The new wrapper
also syncs the containing directory on POSIX and verifies the written bytes before
reporting success. Python documents the flush-before-fsync sequence [os]. Windows
has file flush/fsync but no equivalent portable directory-sync claim here.
Replication, hardware-loss tolerance, long-term retention, and filesystem-specific
power-loss behavior are not established by these tests.

A failure after decision evidence but before the receipt can leave an orphan
record. Keep it for diagnosis; do not overwrite it or pretend it completed a
transaction. No permit is returned/exported by this wiring when receipt creation
fails or execution is interrupted. Reusing the same output paths fails closed.
Different directories can still represent repeated attempts. This is not global
exactly-once issuance or publication, and it does not make an ambiguous GitHub POST
safe to retry. The version-1 permit remains unsigned data within a trusted operator
boundary; a digest and receipt are integrity links, not cryptographic authorization.

Before any live activation: resolve candidate review findings and freeze the exact
base/head/changed paths; review the bootstrap-v1 evidence and additive proof
lifecycle; finish the required publisher integration without overwriting proof
history; identify the privileged operator and trusted export; establish abort and
publication-reconciliation procedures. Only then may a separate exact-candidate
attestation/activation be proposed.

After a legitimate Codex merge: independently bind the new package; verify the
complete chain and source identities; disarm the bootstrap; then prove a subsequent
protected maintenance candidate succeeds without bootstrap while invalid ones
remain blocked. Map every applicable Phase 10 obligation rather than assuming
these local tests or two destructive-rule tests close effective enforcement.
Destructive tests require an explicitly approved disposable scope, never a force
update or deletion of the production default branch for convenience.

## Verification and its limits

Local Python 3.13.5: 37 test methods passed. The existing model, service, evidence,
policy, ports, publication module, and publisher contract/config were materialized
from connector reads and checked against their Git blob IDs before testing.
Network DNS prevented a local clone, so this was a verified-module local test
checkout, not a full clean-clone reproduction of every repository gate.

```bash
python -I -m unittest discover -s tests -p test_attested_handover.py -v
```

The added `Attested Handover Compatibility` workflow checks out the exact Codex
review input with read-only job permissions and without retained checkout
credentials. Its script verifies the input commit and all five blobs, runs the
actual reader using synthetic candidate/Authority APIs, then exercises the new
consumer/service/evidence/permit/offline preview. Cases cover approved mixed and
runtime-only paths, unprotected changes, missing approval, failed qualification,
and wrong-base approval. No key, token, live approval, or provider mutation is used
by the tests. Existing workflows and required checks are unchanged.

```bash
python -I scripts/verify_attested_compatibility.py --codex-root /path/to/pinned/codex-test-input
```

That cross-repository script cannot run locally without the full Codex checkout;
its actual GitHub CI result must be observed and recorded on the PR. The standard
Authority Foundation suite discovers the new local tests without replacing old
tests. Passing CI is not independent human approval, production promotion,
bootstrap completion, post-disarm liveness, or battle-tested operation.

[reader]: https://github.com/scnehaux/codex/blob/eaa5b41cd84fcc77fd1ff464120d4be83c57d1cd/integrations/github-governance-evaluator/ATTESTED_RUNTIME.md
[subprocess]: https://docs.python.org/3.13/library/subprocess.html#subprocess.Popen.communicate
[os]: https://docs.python.org/3.13/library/os.html#os.fsync
