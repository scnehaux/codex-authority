#!/usr/bin/env python3
"""Issue one bootstrap publication permit for an exact, separately attested Codex candidate."""

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
from codex_authority.evidence import (  # noqa: E402
    EvidenceWriteError,
    SingleRecordEvidenceSink,
    write_new_json_file,
)
from codex_authority.privileged import (  # noqa: E402
    PrivilegedBootstrapRuntime,
    PrivilegedMaintenanceError,
    PrivilegedValidationAttestation,
    load_maintenance_policy,
)


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ATTESTATION_DIR = ROOT / "governance" / "privileged-validations"
MAINTENANCE_POLICY = ROOT / "governance" / "privileged-maintenance.json"


class PrivilegedPermitIssueError(Exception):
    pass


def _run_git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(ROOT), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        raise PrivilegedPermitIssueError("authority Git identity could not be verified") from None


def _authority_source_revision(head_sha: str) -> tuple[str, Path]:
    revision = _run_git("rev-parse", "HEAD")
    origin_main = _run_git("rev-parse", "origin/main")
    branch = _run_git("branch", "--show-current")
    drift = _run_git("status", "--porcelain", "--untracked-files=all")
    if SHA_RE.fullmatch(revision) is None or revision != origin_main or branch != "main" or drift:
        raise PrivilegedPermitIssueError(
            "privileged permit issuer must run from clean main exactly matching origin/main"
        )

    attestation = ATTESTATION_DIR / f"{head_sha}.json"
    try:
        relative = attestation.relative_to(ROOT).as_posix()
    except ValueError:
        raise PrivilegedPermitIssueError("attestation path escaped the authority repository") from None

    tracked = _run_git("ls-files", "--error-unmatch", relative)
    if tracked != relative:
        raise PrivilegedPermitIssueError("privileged attestation is not tracked at the authority revision")
    _run_git("cat-file", "-e", f"HEAD:{relative}")
    return revision, attestation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", type=Path, required=True)
    parser.add_argument("--pull-request", type=int, required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--evidence-out", type=Path, required=True)
    parser.add_argument("--permit-out", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        if SHA_RE.fullmatch(args.head_sha) is None:
            raise PrivilegedPermitIssueError("head SHA must be exact lowercase 40-character Git SHA")
        authority_revision, attestation_path = _authority_source_revision(args.head_sha)
        maintenance = load_maintenance_policy(MAINTENANCE_POLICY)
        bootstrap = maintenance["bootstrap"]
        candidate = bootstrap["candidate"]
        if (
            bootstrap["enabled"] is not True
            or not isinstance(candidate, dict)
            or candidate.get("pull_request") != args.pull_request
            or candidate.get("head_sha") != args.head_sha
        ):
            raise PrivilegedPermitIssueError(
                "governed privileged bootstrap is not enabled for this exact candidate"
            )

        attestation = PrivilegedValidationAttestation.load(attestation_path)
        if (
            attestation.candidate.pull_request != args.pull_request
            or attestation.candidate.head_sha != args.head_sha
        ):
            raise PrivilegedPermitIssueError("tracked attestation does not match the requested candidate")

        policy = load_authority_policy(ROOT / "governance" / "authority.json")
        request = CandidateRef(
            repository=policy.candidate_repository,
            pull_request=args.pull_request,
            head_sha=args.head_sha,
        )
        runtime = PrivilegedBootstrapRuntime(args.runtime_dir, attestation, maintenance)
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
            raise PrivilegedPermitIssueError(
                "passing privileged authority outcome did not produce a publication permit"
            )
        write_new_json_file(args.permit_out, permit.to_mapping())
        print(
            json.dumps(
                {
                    "status": "privileged_publication_permit_issued",
                    "repository": permit.candidate.repository,
                    "pull_request": permit.candidate.pull_request,
                    "base_sha": permit.base_sha,
                    "head_sha": permit.candidate.head_sha,
                    "runtime_source_revision": permit.runtime_source_revision,
                    "evaluator_source_revision": permit.evaluator_source_revision,
                    "authority_service_source_revision": permit.authority_service_source_revision,
                    "attestation_digest": attestation.digest,
                    "permit_digest": permit.digest,
                    "evidence_recorded": True,
                },
                sort_keys=True,
            )
        )
        return 0
    except (
        EvidenceWriteError,
        PrivilegedMaintenanceError,
        PrivilegedPermitIssueError,
        TypeError,
        ValueError,
    ) as exc:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "code": "privileged-permit-issue-failed",
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
                    "code": "privileged-permit-unexpected-failure",
                    "message": "Privileged permit issuance failed closed.",
                },
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
