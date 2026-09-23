# Windows publisher checkout byte integrity

## Scope

Local checkout repair discovered on 2026-09-24 against Authority main
`cf72f87e7f123c28c1c687ec46e4380bdc647c6a`. This is an implementation note,
not a normative architecture artifact, approval, new live proof or promotion.

## Observed failure

The working tree was Git-clean with `core.autocrlf=true`, but
`python -I scripts/verify_publisher_proof.py` failed because checkout converted
all three source-pinned publisher Python files from LF to CRLF. Their committed
blob identities still matched the immutable proof record. The source logic and
historical evidence had not changed; the physical checkout bytes had changed.

## Correction

The repository now owns `*.py text eol=lf` in `.gitattributes`. This preserves
canonical source bytes on fresh checkouts without changing a developer's global
Git configuration. Existing affected files were backed up, checked to differ from
their committed objects only by CRLF, then restored to those exact object bytes.
No publisher source blob, expected digest or historical evidence was modified.

An older clone may retain CRLF until affected files are re-checked out. Save any
local edits before doing so. A Git-clean status alone is insufficient evidence
of byte identity when checkout conversion is enabled.

## Regression boundary

`tests/test_publisher_checkout.py` exercises a real disposable Git repository
with `core.autocrlf=true`, commits the publisher sources and repository attributes,
removes only the disposable copies and checks them out again. All three physical
file hashes must match the existing proof-bound source hashes. The regression
fails for all three sources without the attributes policy.

Additional tests retain exact-byte hashing and verify that CRLF changes, real
source changes, missing paths and nonregular paths are not silently accepted.
Production hash verification is unchanged and performs no newline normalization.

## Qualification and authority limits

Run the full verification sequence in README from the exact candidate checkout,
including unittest, foundation, publisher, proof, maintenance and append-only
attestation-history checks. Local results do not replace GitHub CI or independent
candidate-bound authorization. Publication and privileged bootstrap remain disabled;
no source promotion, provider ruleset change, attestation or merge is authorized
by this checkout correction. Codex Slice 11.6 remains a separate candidate.
