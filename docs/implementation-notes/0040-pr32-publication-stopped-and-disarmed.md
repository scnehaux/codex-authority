# PR #32 publication stopped; controlled activation disarmed

Recorded: 2026-09-24 (Asia/Jakarta). Implementation-local, non-normative.

Codex Slice 11.6 is submitted as PR #32, exact head
`fa733509974b048c587e9066690cfa7267313b77`, base
`bfea97e841616a2880e28d2cfa177712209520f6`. It remains OPEN and UNMERGED.
GitHub Governance Qualification succeeded. Exact attestation PR #51 merged and
the promoted credential-free runtime then produced a fresh PASS with durable
evidence, linking receipt and permit. Activation PR #52 merged separately.

The first local publisher invocation stopped while resolving its default key
location in a minimal Windows environment. Its fallback evaluates Path.home()
even when LOCALAPPDATA is set. An offline diagnostic reproduced the RuntimeError
before `_publish` was called. The attempt journal stayed empty and GitHub showed
zero Codex Governance Authority checks on this head.

A corrected invocation using the existing explicit-path option was blocked by the
execution tool's safety check before execution. No alternate publication route,
credential workaround, blind POST retry, or forced merge was attempted. No token
was issued, no check was posted, and token revocation is not claimed.

This change returns checked-in controlled publication to disabled/null and restores
the checked-in disabled-state test. The exported operational configuration was also
disabled immediately. The append-only attestation and historical activation remain
in Git history; source-pinned production publisher bytes and all historical proof
hashes are unchanged. Privileged bootstrap and generic publication remain disabled.

`governance/evidence/phase11-slice11.6-publication-stop-001.json` records the exact
candidate, qualification, source revisions, bundle digests, and limitations. Full
local runtime evidence, receipts, diagnostic, and tool-operation logs remain in the
submission evidence directory. This is a stop/disarm record, NOT Slice 11.6 completion.

Resume requires an explicitly authorized execution path, fresh verification of PR
base/head and qualification, and a new separately governed short-lived activation.
Do not reuse an old activation or bypass a tool restriction. Do not advance to
Slice 11.7 or architecture admission merely because CI and evaluation passed.
