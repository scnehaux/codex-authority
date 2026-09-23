# Offline publisher environment preflight

Recorded: 2026-09-24 (Asia/Jakarta). Implementation-local, non-normative.

## Problem and scope

PR #32 publication stopped before the publisher was called. The pinned Windows
resolver evaluates the Path.home() fallback passed to os.environ.get even when
LOCALAPPDATA is set. A minimal process without home variables can therefore fail
before a publication-attempt journal exists. The separate execution-tool denial
is NOT a Python defect and is not resolved or overridden by this change.

This slice closes the missing pre-activation diagnosis and regression-test gap.
It does not alter the historical resolver, publisher source, source pins, evidence,
runtime promotion, attestation, provider ruleset, or activation state. A production
resolver change still requires its own reviewed source-evolution/promotion decision.
No live publisher invocation or alternative credential route is added.

## Offline command

```text
python -I -B scripts/check_publisher_environment.py
```

The command verifies Python 3.13+, reuses the existing publisher-proof source pins,
and calls only the existing default-location resolver. It requires an absolute,
non-traversing location with no control characters. Output is redacted JSON;
exit 0 means this limited environment check passed, exit 2 means it is blocked.
The resolved location, environment values and raw exception messages are not output.

No key is opened, inspected for existence or permissions, or authenticated. No
network request, token issuance, evidence/permit issuance, activation mutation,
subprocess launch or publication occurs. The CLI deliberately has no --write,
--private-key, activation, or publication option.

A PASS applies only to the interpreter and environment of this invocation. It is
NOT qualification of a later sanitized child environment, a key/ACL/dependency
check, an approval, a publication permit, or a workaround for execution restrictions.
Operators must diagnose the actual intended environment before requesting a fresh
governed activation; the tool does not prepare or run that activation.

## Regression and CI

Tests exercise the historical eager-home failure using synthetic inputs on either
OS and a real Windows subprocess with LOCALAPPDATA but no home variables. Other
cases reject wrong types, relative/drive-relative paths, traversal, control
characters, unverified source and unsupported CLI arguments. Errors are redacted.
A subprocess audit hook forbids key-file opens, socket activity and child-process
launches during the actual diagnostic. Synthetic nonexistent home paths are used;
no operator key is needed for any test.

The existing Ubuntu Authority Foundation check retains its name and permissions.
It runs the diagnostic before its full suite. A supplemental Windows job runs the
same diagnostic, the full suite and all existing verifiers with read-only contents
permissions and no retained checkout credentials. It does not add a ruleset,
automatic deployment or publication. Test results are separate from operational
qualification and must not be presented as a successful live publication.

## References and remaining gate

Python specifies eager evaluation of call arguments and Path.home() raises
RuntimeError when a home cannot be resolved:

- https://docs.python.org/3.13/reference/expressions.html#calls
- https://docs.python.org/3.13/library/pathlib.html#pathlib.Path.home

Historical stop: note 0040 and
`governance/evidence/phase11-slice11.6-publication-stop-001.json`.

Codex PR #32 remains pending the required dedicated-App check and governed merge.
An allowed execution path, fresh candidate/qualification checks and a separately
authorized short-lived activation remain necessary. This diagnostic neither repairs
nor bypasses the execution-tool restriction. Slice 11.7 and architecture admission
are not advanced by this maintenance slice.
