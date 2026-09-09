from __future__ import annotations

from .model import (
    AuthorityDecision,
    AuthorityOutcome,
    CandidateRef,
    CandidateSnapshot,
    EvidenceRecord,
    RuntimeDecisionEnvelope,
)
from .policy import AuthorityPolicy
from .ports import EvidenceSink, TrustedRuntime


class AuthorityService:
    """Fail-closed orchestration around an independently promoted Codex runtime."""

    def __init__(
        self,
        policy: AuthorityPolicy,
        runtime: TrustedRuntime,
        evidence: EvidenceSink,
    ) -> None:
        self._policy = policy
        self._runtime = runtime
        self._evidence = evidence

    def evaluate(self, request: CandidateRef) -> AuthorityOutcome:
        if request.repository != self._policy.candidate_repository:
            return self._record(
                EvidenceRecord(
                    request=request,
                    decision=AuthorityDecision.BLOCKED,
                    reasons=("candidate-repository-not-authorized",),
                )
            )

        try:
            envelope = self._runtime.evaluate(request)
        except Exception:
            return self._record(
                EvidenceRecord(
                    request=request,
                    decision=AuthorityDecision.BLOCKED,
                    reasons=("trusted-runtime-failed",),
                )
            )

        if not isinstance(envelope, RuntimeDecisionEnvelope):
            return self._record(
                EvidenceRecord(
                    request=request,
                    decision=AuthorityDecision.BLOCKED,
                    reasons=("trusted-runtime-invalid-output",),
                )
            )

        identity_reason = self._identity_failure(request, envelope.snapshot)
        if identity_reason is not None:
            return self._record(
                EvidenceRecord(
                    request=request,
                    decision=AuthorityDecision.BLOCKED,
                    reasons=(identity_reason,),
                    snapshot=envelope.snapshot,
                    runtime_source_revision=envelope.runtime_source_revision,
                    evaluator_source_revision=envelope.evaluator_source_revision,
                )
            )

        if envelope.snapshot.state != "open":
            return self._record(
                EvidenceRecord(
                    request=request,
                    decision=AuthorityDecision.BLOCKED,
                    reasons=("candidate-pull-request-not-open",),
                    snapshot=envelope.snapshot,
                    runtime_source_revision=envelope.runtime_source_revision,
                    evaluator_source_revision=envelope.evaluator_source_revision,
                )
            )

        return self._record(
            EvidenceRecord(
                request=request,
                decision=envelope.decision,
                reasons=envelope.reasons,
                snapshot=envelope.snapshot,
                runtime_source_revision=envelope.runtime_source_revision,
                evaluator_source_revision=envelope.evaluator_source_revision,
            )
        )

    @staticmethod
    def _identity_failure(
        request: CandidateRef,
        snapshot: CandidateSnapshot,
    ) -> str | None:
        if snapshot.repository != request.repository:
            return "candidate-repository-identity-mismatch"
        if snapshot.pull_request != request.pull_request:
            return "candidate-pull-request-identity-mismatch"
        if snapshot.head_sha != request.head_sha:
            return "candidate-head-identity-mismatch"
        return None

    def _record(self, record: EvidenceRecord) -> AuthorityOutcome:
        try:
            self._evidence.append(record)
        except Exception:
            return AuthorityOutcome(
                request=record.request,
                decision=AuthorityDecision.BLOCKED,
                reasons=("authority-evidence-write-failed",),
                snapshot=record.snapshot,
                runtime_source_revision=record.runtime_source_revision,
                evaluator_source_revision=record.evaluator_source_revision,
                evidence_recorded=False,
            )

        return AuthorityOutcome(
            request=record.request,
            decision=record.decision,
            reasons=record.reasons,
            snapshot=record.snapshot,
            runtime_source_revision=record.runtime_source_revision,
            evaluator_source_revision=record.evaluator_source_revision,
            evidence_recorded=True,
        )
