# Git object bytes for committed governed inputs

Recorded: 2026-09-18 (Asia/Jakarta). Implementation-local, non-normative.

## Observation

The first real PR #22 bootstrap preparation on the authorized Windows operator
machine failed closed with `bootstrap-committed-blob` before any evidence or
permit file was produced.

The Authority checkout was clean and exactly on reviewed `main`, but Git checkout
filters had materialized text files with Windows line endings. The previous
implementation compared those working-tree bytes to the exact committed Git blob
ID. A clean checkout can therefore be semantically unchanged while its materialized
text bytes differ from the object database bytes.

Changing operator-wide `core.autocrlf`, normalizing files ad hoc, or weakening the
blob check would make deployment correctness depend on local Git settings. Those
alternatives are rejected for this boundary.

## REC-D-014 — Read committed governed bytes from immutable Git objects

Status: selected for this portability fix; operational proof resumes only after
review and CI. The repository path and regular-file mode are still verified from
the exact Authority revision with `git ls-tree`.
After resolving that tree entry to its blob ID, the implementation checks the
committed object size against the existing bound and reads the exact blob bytes
from Git's object database. The blob hash is recomputed before use.

Working-tree cleanliness, branch identity, origin URL, and `origin/main` equality
remain separate preconditions. The working policy is parsed only to fail fast when
the bootstrap is disabled; after source verification, the committed policy bytes
become the bytes retained in operational evidence. Semantic canonical equality
checks that the clean materialized policy still represents the committed policy.

This follows the principle that an identity claim should be verified at the layer
that defines that identity: Git blob identity belongs to the Git object database,
not to a platform-dependent checkout representation.

## Trade-offs and acceptance

This adds two bounded Git object reads (`cat-file -s` and `cat-file blob`) for each
committed governed input. Git and the local object database remain trusted parts
of the operator boundary; this is not a signature or independent remote proof.

Regression coverage requires `_committed_file` to return exact object bytes even
when a working-tree read would fail. The original mode/path negative test remains.
The real Windows bootstrap must then pass this precondition without changing Git
line-ending configuration.

The earlier failed preparation directories are retained as non-authorizing local
artifacts. They contain no issued permit or publication record and must not be
reused as operational state.
