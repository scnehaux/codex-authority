#!/usr/bin/env python3
"""Evaluate one exact Codex PR and issue a proof permit only after durable PASS evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from codex_authority import (  # noqa: E402
    AuthorityDecision,
    AuthorityService,
    CandidateRef,
    issue_publication_permit,
    load_authority_policy,
)
from codex_authority.adapters import PromotedCodexRuntime  # noqa: E402
from codex_authority.evidence import (  # noqa: E402
    EvidenceWriteError,
    SingleRecordEvidenceSink,
    write_new_json_file,
)

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ProofIssueError(Exception):
    pass


def _authority_source_revision() -> str:
    try:
        revision = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        ).stdout.strip()
        drift = subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=all"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        raise ProofIssueError("authority source revision could not be verified") from None
    if SHA_RE.fullmatch(revision) is None or drift:
        raise ProofIssueError(
            "authority proof issuer must run from one exact clean committed revision"
        )
    return revision


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", type=Path, required=True)
    parser.add_argument("--pull-request", type=int, required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--evidence-out", type=Path, required=True)
    parser.add_argument("--permit-out", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        authority_revision = _authority_source_revision()
        policy = load_authority_policy(ROOT / "governance/authority.json")
        request = CandidateRef(
            repository=policy.candidate_repository,
            pull_request=args.pull_request,
            head_sha=args.head_sha,
        )
        runtime = PromotedCodexRuntime(args.runtime_dir)
        evidence = SingleRecordEvidenceSink(args.evidence_out)
        service = AuthorityService(policy, runtime, evidence)
        outcome = service.evaluate(request)
        if outcome.decision is not AuthorityDecision.PASS:
            print(
                json.dumps(
                    {
                        "status": "blocked",
                        "decision": outcome.decision.value,
                        "reasons": list(outcome.reasons),
                        "evidence_recorded": outcome.evidence_recorded,
                    },
                    sort_keys=True,
                )
            )
            return 2

        permit = issue_publication_permit(
            outcome,
            authority_service_source_revision=authority_revision,
        )
        if permit is None:
            raise ProofIssueError("passing authority outcome did not produce a permit")
        write_new_json_file(args.permit_out, permit.to_mapping())
        print(
            json.dumps(
                {
                    "status": "proof_permit_issued",
                    "repository": permit.candidate.repository,
                    "pull_request": permit.candidate.pull_request,
                    "base_sha": permit.base_sha,
                    "head_sha": permit.candidate.head_sha,
                    "runtime_source_revision": permit.runtime_source_revision,
                    "evaluator_source_revision": permit.evaluator_source_revision,
                    "authority_service_source_revision": permit.authority_service_source_revision,
                    "permit_digest": permit.digest,
                    "evidence_recorded": True,
                },
                sort_keys=True,
            )
        )
        return 0
    except (EvidenceWriteError, ProofIssueError, TypeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "code": "proof-permit-issue-failed",
                    "message": str(exc),
                },
                sort_keys=True,
            )
        )
        return 2
    except Exception:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "code": "proof-permit-unexpected-failure",
                    "message": "Proof permit issuance failed closed.",
                },
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
