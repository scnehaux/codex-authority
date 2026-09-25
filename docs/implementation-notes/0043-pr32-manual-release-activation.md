# PR #32 manual release activation

Recorded: 2026-09-25T06:18:04Z. Implementation-local, non-normative.

This change enables one short-lived attested-v2 publication for Codex PR #32 at
exact head fa733509974b048c587e9066690cfa7267313b77 and base
bfea97e841616a2880e28d2cfa177712209520f6.

Authority and publisher source are pinned to
fe8c93c3ec9b9ee99ac9f524d20fe7d629538821. Permit, evidence and receipt are
bound to the fresh credential-free PASS prepared for the same candidate.

Activation window: 2026-09-25T06:25:04Z through 2026-09-25T06:40:04Z UTC (15 minutes).
The generic publisher and privileged bootstrap remain disabled. Publication must
use the canonical controlled publisher, one durable attempt journal, fresh
candidate/qualification verification, and token revocation. The operator must
disarm this activation after success or abort.
