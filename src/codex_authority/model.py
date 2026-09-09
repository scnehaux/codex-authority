from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re


SHA_RE = re.compile(r"^[0-9a-f]{40}$")


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
        if not self.repository or "/" not in self.repository:
            raise ValueError("repository must be an owner/name identifier")
        if type(self.pull_request) is not int or self.pull_request <= 0:
            raise ValueError("pull_request must be a positive integer")
        if SHA_RE.fullmatch(self.head_sha) is None:
            raise ValueError("head_sha must be a lowercase 40-character Git SHA")


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
        if SHA_RE.fullmatch(self.base_sha) is None:
            raise ValueError("base_sha must be a lowercase 40-character Git SHA")
        if self.base_sha == self.head_sha:
            raise ValueError("base_sha and head_sha must differ")
        if not self.state:
            raise ValueError("state is required")
        if not self.changed_files or any(not item for item in self.changed_files):
            raise ValueError("changed_files must contain non-empty paths")


@dataclass(frozen=True, slots=True)
class EvaluationVerdict:
    decision: AuthorityDecision
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.decision not in (AuthorityDecision.PASS, AuthorityDecision.FAIL):
            raise ValueError("evaluator verdict must be pass or fail")
        if any(not reason for reason in self.reasons):
            raise ValueError("reasons must be non-empty strings")


@dataclass(frozen=True, slots=True)
class AuthorityOutcome:
    request: CandidateRef
    decision: AuthorityDecision
    reasons: tuple[str, ...]
    snapshot: CandidateSnapshot | None = None

    @property
    def publishable_success(self) -> bool:
        return self.decision is AuthorityDecision.PASS and self.snapshot is not None
