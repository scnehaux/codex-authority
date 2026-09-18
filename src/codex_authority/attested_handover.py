"""Disabled-by-default handover wiring with evidence before permit release.

No CLI accepts caller-supplied facts or effective source identities. This module
never publishes a GitHub check or activates the separately governed bootstrap.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import subprocess

from .adapters.attested_runtime import AttestedCodexRuntime, RuntimePackage, read_regular
from .attested_contract import (
    DEPENDENCY_BLOBS, EVALUATOR_REVISION, HandoverError, MAX_RESULT_BYTES, REPOSITORY,
    canonical, decode_object, object_fields, require, sha,
)
from .evidence import _record_mapping, write_new_json_file
from .model import AuthorityDecision, AuthorityOutcome, CandidateRef, EvidenceRecord
from .policy import AuthorityPolicy, load_authority_policy
from .publication import PublicationPermit, issue_publication_permit
from .service import AuthorityService

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "governance" / "attested-handover.json"
REVIEW_HEAD = "eaa5b41cd84fcc77fd1ff464120d4be83c57d1cd"
REVIEW_BLOB = "c9a0c3bf2fd3c33be4deb1b1e5fc624d1b0b796a"


@dataclass(frozen=True, slots=True)
class HandoverPolicy:
    package: RuntimePackage | None
    timeout_seconds: int

    @classmethod
    def load(cls, path: Path) -> HandoverPolicy:
        data = object_fields(decode_object(read_regular(path, 16_384), 16_384), {
            "schema_version", "kind", "state", "candidate_repository", "reviewed_input",
            "runtime_package", "execution", "publication", "claims",
        }, "handover-policy-fields")
        require(type(data["schema_version"]) is int and data["schema_version"] == 1
                and data["kind"] == "codex-attested-runtime-handover"
                and data["candidate_repository"] == REPOSITORY, "handover-policy-identity")
        require(data["reviewed_input"] == {"pull_request": 22, "head_sha": REVIEW_HEAD,
                "entrypoint_blob": REVIEW_BLOB, "result_schema_version": 2}, "handover-review-binding")
        review = data["reviewed_input"]
        require(type(review["pull_request"]) is int and type(review["result_schema_version"]) is int, "handover-review-types")
        execution = object_fields(data["execution"], {
            "enabled", "timeout_seconds", "max_output_bytes", "candidate_code_execution", "credentials_allowed",
        }, "handover-execution")
        require(execution["candidate_code_execution"] is False and execution["credentials_allowed"] is False,
                "handover-isolation")
        require(type(execution["timeout_seconds"]) is int and 1 <= execution["timeout_seconds"] <= 300
                and type(execution["max_output_bytes"]) is int
                and execution["max_output_bytes"] == MAX_RESULT_BYTES, "handover-budgets")
        publication = object_fields(data["publication"], {"write_enabled", "mode"}, "handover-publication")
        require(publication["write_enabled"] is False and publication["mode"] == "offline-preview-only", "handover-publication")
        claims = object_fields(data["claims"], {
            "privileged_governance_maintenance_path_proven", "effective_enforcement_proven",
        }, "handover-claims")
        require(
            type(claims["privileged_governance_maintenance_path_proven"]) is bool
            and type(claims["effective_enforcement_proven"]) is bool
            and claims["effective_enforcement_proven"] is False,
            "handover-claims",
        )
        package = None
        if execution["enabled"] is False:
            require(data["state"] == "staged-disabled" and data["runtime_package"] is None, "handover-disabled-binding")
        else:
            require(execution["enabled"] is True and data["state"] == "runtime-promoted", "handover-activation")
            source = object_fields(data["runtime_package"], {"repository", "source_revision", "entrypoint", "blobs"}, "handover-package")
            require(source["repository"] == REPOSITORY and source["entrypoint"] == "attested_runtime.py", "handover-package")
            require(source["source_revision"] != REVIEW_HEAD, "unmerged-review-source")
            require(source["blobs"] == {"attested_runtime.py": REVIEW_BLOB, **dict(DEPENDENCY_BLOBS)}, "handover-package-blobs")
            package = RuntimePackage(sha(source["source_revision"]), REVIEW_BLOB)
        if claims["privileged_governance_maintenance_path_proven"] is True:
            require(
                execution["enabled"] is True and package is not None and data["state"] == "runtime-promoted",
                "handover-claims",
            )
        return cls(package, execution["timeout_seconds"])


def _write_bound(path: Path, value: dict) -> str:
    # Require an existing operational directory: no new directory chain to fsync.
    require(path.parent.is_dir(), "evidence-directory")
    raw = canonical(value) + b"\n"
    write_new_json_file(path, value)
    if os.name == "posix":
        try:
            fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        except OSError:
            raise HandoverError("evidence-directory-sync") from None
    require(read_regular(path, 1_000_000) == raw, "evidence-readback")
    return sha256(raw).hexdigest()


class AttestedEvidenceSink:
    """Retain original wire bytes and their source, without changing legacy evidence."""
    def __init__(self, path: Path, runtime: AttestedCodexRuntime, service_revision: str) -> None:
        self.path = path
        self.runtime = runtime
        self.service_revision = sha(service_revision)
        self.record_digest: str | None = None
        self._used = False

    def append(self, record: EvidenceRecord) -> None:
        require(not self._used, "evidence-already-used")
        self._used = True
        result = self.runtime.result
        if record.decision in (AuthorityDecision.PASS, AuthorityDecision.FAIL):
            require(result is not None, "evidence-runtime-missing")
            require(record.snapshot == result.snapshot and record.decision == result.decision
                    and record.reasons == result.reasons, "evidence-outcome-binding")
            require(record.request.repository == result.snapshot.repository
                    and record.request.pull_request == result.snapshot.pull_request
                    and record.request.head_sha == result.snapshot.head_sha, "evidence-request-binding")
            require(record.runtime_source_revision == self.runtime.package.source_revision
                    and record.evaluator_source_revision == EVALUATOR_REVISION, "evidence-source-binding")
        else:
            require(result is None, "blocked-runtime-evidence")
        value = {
            "schema_version": 1, "kind": "codex-authority-attested-decision-evidence",
            "authority_service_source_revision": self.service_revision,
            "runtime_package": self.runtime.package.to_mapping(),
            "decision_record": _record_mapping(record),
            "runtime_result_json": result.raw.decode("utf-8") if result is not None else None,
            "runtime_result_sha256": result.raw_digest if result is not None else None,
        }
        self.record_digest = _write_bound(self.path, value)


@dataclass(frozen=True, slots=True)
class PreparedAttestedOutcome:
    outcome: AuthorityOutcome
    permit: PublicationPermit | None
    evidence_digest: str | None
    receipt_digest: str | None


def _evaluate_and_prepare(request: CandidateRef, runtime: AttestedCodexRuntime,
                          authority_policy: AuthorityPolicy, service_revision: str,
                          evidence_path: Path, receipt_path: Path) -> PreparedAttestedOutcome:
    """Internal wiring also used with explicitly synthetic test backends. No live writes."""
    sha(service_revision)
    require(service_revision != request.head_sha, "candidate-as-service")
    sink = AttestedEvidenceSink(evidence_path, runtime, service_revision)
    outcome = AuthorityService(authority_policy, runtime, sink).evaluate(request)
    if outcome.decision is not AuthorityDecision.PASS:
        return PreparedAttestedOutcome(outcome, None, sink.record_digest, None)
    require(sink.record_digest is not None and runtime.result is not None, "evidence-not-recorded")
    permit = issue_publication_permit(outcome, authority_service_source_revision=service_revision)
    require(permit is not None, "permit-rejected")
    receipt = {
        "schema_version": 1, "kind": "codex-attested-permit-receipt",
        "candidate": permit.to_mapping()["candidate"], "source": permit.to_mapping()["source"],
        "evidence_sha256": sink.record_digest, "runtime_result_sha256": runtime.result.raw_digest,
        "permit_digest": permit.digest,
    }
    # The permit is not returned or exported until the linking receipt is durable.
    receipt_digest = _write_bound(receipt_path, receipt)
    return PreparedAttestedOutcome(outcome, permit, sink.record_digest, receipt_digest)


def _authority_revision() -> str:
    def git(*args: str) -> str:
        try:
            return subprocess.run(["git", "-C", str(ROOT), *args], check=True, text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            raise HandoverError("authority-git-identity") from None
    revision = sha(git("rev-parse", "HEAD"))
    require(git("remote", "get-url", "origin") in {
        "https://github.com/scnehaux/codex-authority.git", "git@github.com:scnehaux/codex-authority.git",
    }, "authority-origin")
    require(git("branch", "--show-current") == "main" and git("rev-parse", "origin/main") == revision
            and not git("status", "--porcelain", "--untracked-files=all"), "authority-clean-main")
    return revision


def prepare_attested_permit(request: CandidateRef, runtime_dir: str | Path,
                            evidence_path: str | Path, receipt_path: str | Path) -> PreparedAttestedOutcome:
    """Public entrypoint: fixed governed policy only, no caller-selected promotion or facts.

    Currently stops before Git commands, package reads, execution, or evidence writes.
    A later separately reviewed promotion may bind a merged package; publication
    remains outside this function and outside this change.
    """
    policy = HandoverPolicy.load(POLICY_PATH)
    if policy.package is None:
        raise HandoverError("handover-disabled")
    revision = _authority_revision()
    authority_policy = load_authority_policy(ROOT / "governance" / "authority.json")
    runtime = AttestedCodexRuntime(runtime_dir, policy.package, timeout_seconds=policy.timeout_seconds)
    return _evaluate_and_prepare(request, runtime, authority_policy, revision,
                                 Path(evidence_path), Path(receipt_path))
