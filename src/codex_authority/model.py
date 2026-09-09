from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath
import re


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _require_sha(value: str, name: str) -> None:
    if SHA_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a lowercase 40-character Git SHA")


def _require_path(value: str) -> None:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("changed_files must contain repository-relative POSIX paths")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("changed_files must contain repository-relative POSIX paths")


class AuthorityDecision(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class CandidateRef:
    repository: str
    pull_request: int
    head_sha: str

    def __post_init__(self) -> None:
        if REPOSITORY_RE.fullmatch(self.repository) is None:
            raise ValueError("repository must be an owner/name identifier")
        if type(self.pull_request) is not int or self.pull_request <= 0:
            raise ValueError("pull_request must be a positive integer")
        _require_sha(self.head_sha, "head_sha")


@dataclass(frozen=True, slots=True)
class CandidateSnapshot:
    repository: str
    pull_request: int
    base_sha: str
    head_sha: str
    state: str
    changed_files: tuple[str, ...]

    def __post_init__(self) -> None:
        CandidateRef(self.repository, self.pull_request, self.head_sha)
        _require_sha(self.base_sha, "base_sha")
        if self.base_sha == self.head_sha:
            raise ValueError("base_sha and head_sha must differ")
        if self.state not in {"open", "closed"}:
            raise ValueError("state must be open or closed")
        if not self.changed_files:
            raise ValueError("changed_files must not be empty")
        if len(set(self.changed_files)) != len(self.changed_files):
            raise ValueError("changed_files must not contain duplicates")
        for item in self.changed_files:
            _require_path(item)


@dataclass(frozen=True, slots=True)
class RuntimeDecisionEnvelope:
    """Decision produced by an independently verified promoted Codex runtime."""

    snapshot: CandidateSnapshot
    decision: AuthorityDecision
    reasons: tuple[str, ...]
    runtime_source_revision: str
    evaluator_source_revision: str
    source_identity_verified: bool
    facts_collected_independently: bool
    candidate_code_executed: bool
    credentials_used: bool

    def __post_init__(self) -> None:
        if self.decision not in (AuthorityDecision.PASS, AuthorityDecision.FAIL):
            raise ValueError("runtime decision must be pass or fail")
        if any(not isinstance(reason, str) or not reason for reason in self.reasons):
            raise ValueError("reasons must be non-empty strings")
        if self.decision is AuthorityDecision.FAIL and not self.reasons:
            raise ValueError("failed runtime decision requires at least one reason")
        _require_sha(self.runtime_source_revision, "runtime_source_revision")
        _require_sha(self.evaluator_source_revision, "evaluator_source_revision")
        if self.source_identity_verified is not True:
            raise ValueError("runtime source identity must be verified")
        if self.facts_collected_independently is not True:
            raise ValueError("candidate facts must be collected independently")
        if self.candidate_code_executed is not False:
            raise ValueError("candidate code execution is forbidden")
        if self.credentials_used is not False:
            raise ValueError("trusted evaluation runtime must remain credential-free")


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    request: CandidateRef
    decision: AuthorityDecision
    reasons: tuple[str, ...]
    snapshot: CandidateSnapshot | None = None
    runtime_source_revision: str | None = None
    evaluator_source_revision: str | None = None

    def __post_init__(self) -> None:
        if any(not isinstance(reason, str) or not reason for reason in self.reasons):
            raise ValueError("reasons must be non-empty strings")
        if self.decision is not AuthorityDecision.PASS and not self.reasons:
            raise ValueError("non-passing evidence requires at least one reason")
        if self.decision is AuthorityDecision.PASS:
            if self.snapshot is None:
                raise ValueError("passing evidence requires a candidate snapshot")
            if self.runtime_source_revision is None or self.evaluator_source_revision is None:
                raise ValueError("passing evidence requires explicit source identities")
        if self.runtime_source_revision is not None:
            _require_sha(self.runtime_source_revision, "runtime_source_revision")
        if self.evaluator_source_revision is not None:
            _require_sha(self.evaluator_source_revision, "evaluator_source_revision")


@dataclass(frozen=True, slots=True)
class AuthorityOutcome:
    request: CandidateRef
    decision: AuthorityDecision
    reasons: tuple[str, ...]
    snapshot: CandidateSnapshot | None = None
    runtime_source_revision: str | None = None
    evaluator_source_revision: str | None = None
    evidence_recorded: bool = False

    def __post_init__(self) -> None:
        if any(not isinstance(reason, str) or not reason for reason in self.reasons):
            raise ValueError("reasons must be non-empty strings")
        if self.decision is not AuthorityDecision.PASS and not self.reasons:
            raise ValueError("non-passing outcome requires at least one reason")
        if self.decision is AuthorityDecision.PASS:
            if self.snapshot is None:
                raise ValueError("passing outcome requires a candidate snapshot")
            if self.evidence_recorded is not True:
                raise ValueError("passing outcome requires durable evidence")
            if self.runtime_source_revision is None or self.evaluator_source_revision is None:
                raise ValueError("passing outcome requires explicit source identities")
            _require_sha(self.runtime_source_revision, "runtime_source_revision")
            _require_sha(self.evaluator_source_revision, "evaluator_source_revision")
