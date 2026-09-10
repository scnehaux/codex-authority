from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any, Mapping

from .model import AuthorityDecision, AuthorityOutcome, CandidateRef


PERMIT_CONTRACT_VERSION = 1
PERMIT_KIND = "codex-governance-publication-permit"
CANDIDATE_REPOSITORY = "scnehaux/codex"
CHECK_CONTEXT = "Codex Governance Authority"
EXPECTED_INTEGRATION_ID = 4864946
PROVIDER = "github"
SUCCESS_CONCLUSION = "success"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _require_sha(value: object, name: str) -> str:
    if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a lowercase 40-character Git SHA")
    return value


def _object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], name: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{name} fields do not match the publication permit contract")


@dataclass(frozen=True, slots=True)
class PublicationPermit:
    """Narrow success-only capability created after durable authority evidence."""

    candidate: CandidateRef
    base_sha: str
    runtime_source_revision: str
    evaluator_source_revision: str
    authority_service_source_revision: str
    decision: AuthorityDecision = AuthorityDecision.PASS
    evidence_recorded: bool = True
    provider: str = PROVIDER
    check_context: str = CHECK_CONTEXT
    expected_integration_id: int = EXPECTED_INTEGRATION_ID
    conclusion: str = SUCCESS_CONCLUSION

    def __post_init__(self) -> None:
        if self.candidate.repository != CANDIDATE_REPOSITORY:
            raise ValueError("publication permit is bound to scnehaux/codex")
        _require_sha(self.base_sha, "base_sha")
        if self.base_sha == self.candidate.head_sha:
            raise ValueError("publication permit base and head SHA must differ")
        _require_sha(self.runtime_source_revision, "runtime_source_revision")
        _require_sha(self.evaluator_source_revision, "evaluator_source_revision")
        _require_sha(
            self.authority_service_source_revision,
            "authority_service_source_revision",
        )
        if self.decision is not AuthorityDecision.PASS:
            raise ValueError("only a passing authority outcome may become a publication permit")
        if self.evidence_recorded is not True:
            raise ValueError("publication permit requires durable authority evidence")
        if self.provider != PROVIDER:
            raise ValueError("publication provider is fixed to GitHub")
        if self.check_context != CHECK_CONTEXT:
            raise ValueError("publication check context is fixed")
        if type(self.expected_integration_id) is not int or self.expected_integration_id != EXPECTED_INTEGRATION_ID:
            raise ValueError("publication permit is bound to the dedicated GitHub App")
        if self.conclusion != SUCCESS_CONCLUSION:
            raise ValueError("publication permit can only authorize a success conclusion")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "contract_version": PERMIT_CONTRACT_VERSION,
            "kind": PERMIT_KIND,
            "candidate": {
                "repository": self.candidate.repository,
                "pull_request": self.candidate.pull_request,
                "base_sha": self.base_sha,
                "head_sha": self.candidate.head_sha,
            },
            "decision": self.decision.value,
            "source": {
                "runtime_source_revision": self.runtime_source_revision,
                "evaluator_source_revision": self.evaluator_source_revision,
                "authority_service_source_revision": self.authority_service_source_revision,
            },
            "evidence": {"recorded": self.evidence_recorded},
            "publication": {
                "provider": self.provider,
                "check_context": self.check_context,
                "expected_integration_id": self.expected_integration_id,
                "conclusion": self.conclusion,
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), indent=2, sort_keys=True) + "\n"

    @property
    def digest(self) -> str:
        raw = json.dumps(
            self.to_mapping(),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(raw).hexdigest()

    @classmethod
    def from_mapping(cls, value: object) -> PublicationPermit:
        data = _object(value, "permit")
        _exact_keys(
            data,
            {
                "contract_version",
                "kind",
                "candidate",
                "decision",
                "source",
                "evidence",
                "publication",
            },
            "permit",
        )
        if data["contract_version"] != PERMIT_CONTRACT_VERSION or data["kind"] != PERMIT_KIND:
            raise ValueError("unsupported publication permit contract")

        candidate = _object(data["candidate"], "candidate")
        _exact_keys(
            candidate,
            {"repository", "pull_request", "base_sha", "head_sha"},
            "candidate",
        )
        source = _object(data["source"], "source")
        _exact_keys(
            source,
            {
                "runtime_source_revision",
                "evaluator_source_revision",
                "authority_service_source_revision",
            },
            "source",
        )
        evidence = _object(data["evidence"], "evidence")
        _exact_keys(evidence, {"recorded"}, "evidence")
        publication = _object(data["publication"], "publication")
        _exact_keys(
            publication,
            {"provider", "check_context", "expected_integration_id", "conclusion"},
            "publication",
        )
        if data["decision"] != AuthorityDecision.PASS.value:
            raise ValueError("publication permit decision must be pass")

        return cls(
            candidate=CandidateRef(
                repository=candidate["repository"],
                pull_request=candidate["pull_request"],
                head_sha=candidate["head_sha"],
            ),
            base_sha=candidate["base_sha"],
            runtime_source_revision=source["runtime_source_revision"],
            evaluator_source_revision=source["evaluator_source_revision"],
            authority_service_source_revision=source[
                "authority_service_source_revision"
            ],
            decision=AuthorityDecision.PASS,
            evidence_recorded=evidence["recorded"],
            provider=publication["provider"],
            check_context=publication["check_context"],
            expected_integration_id=publication["expected_integration_id"],
            conclusion=publication["conclusion"],
        )

    @classmethod
    def from_json(cls, text: str) -> PublicationPermit:
        if not isinstance(text, str) or len(text.encode("utf-8")) > 32_768:
            raise ValueError("publication permit JSON exceeds the supported size")
        try:
            value = json.loads(text)
        except (ValueError, UnicodeError):
            raise ValueError("publication permit is not valid JSON") from None
        return cls.from_mapping(value)


def issue_publication_permit(
    outcome: AuthorityOutcome,
    *,
    authority_service_source_revision: str,
) -> PublicationPermit | None:
    """Convert exactly one evidenced PASS into a narrow, immutable success permit."""
    if not isinstance(outcome, AuthorityOutcome):
        return None
    if outcome.decision is not AuthorityDecision.PASS or outcome.evidence_recorded is not True:
        return None
    snapshot = outcome.snapshot
    if snapshot is None or snapshot.state != "open":
        return None
    if (
        snapshot.repository != outcome.request.repository
        or snapshot.pull_request != outcome.request.pull_request
        or snapshot.head_sha != outcome.request.head_sha
        or snapshot.repository != CANDIDATE_REPOSITORY
        or outcome.runtime_source_revision is None
        or outcome.evaluator_source_revision is None
    ):
        return None
    try:
        return PublicationPermit(
            candidate=outcome.request,
            base_sha=snapshot.base_sha,
            runtime_source_revision=outcome.runtime_source_revision,
            evaluator_source_revision=outcome.evaluator_source_revision,
            authority_service_source_revision=authority_service_source_revision,
        )
    except (TypeError, ValueError):
        return None
