from __future__ import annotations

from .model import (
    AuthorityDecision,
    AuthorityOutcome,
    CandidateRef,
    CandidateSnapshot,
)
from .policy import AuthorityPolicy
from .ports import CandidateCollector, EvidenceSink, GovernanceEvaluator


class AuthorityService:
    """Fail-closed evaluation orchestration with no publication capability."""

    def __init__(
        self,
        policy: AuthorityPolicy,
        collector: CandidateCollector,
        evaluator: GovernanceEvaluator,
        evidence: EvidenceSink,
    ) -> None:
        self._policy = policy
        self._collector = collector
        self._evaluator = evaluator
        self._evidence = evidence

    def evaluate(self, request: CandidateRef) -> AuthorityOutcome:
        if request.repository != self._policy.candidate_repository:
            return self._record(
                AuthorityOutcome(
                    request=request,
                    decision=AuthorityDecision.BLOCKED,
                    reasons=("candidate-repository-not-authorized",),
                )
            )

        try:
            snapshot = self._collector.collect(request)
        except Exception:
            return self._record(
                AuthorityOutcome(
                    request=request,
                    decision=AuthorityDecision.BLOCKED,
                    reasons=("candidate-facts-collection-failed",),
                )
            )

        identity_reason = self._identity_failure(request, snapshot)
        if identity_reason is not None:
            return self._record(
                AuthorityOutcome(
                    request=request,
                    decision=AuthorityDecision.BLOCKED,
                    reasons=(identity_reason,),
                    snapshot=snapshot,
                )
            )

        if snapshot.state != "open":
            return self._record(
                AuthorityOutcome(
                    request=request,
                    decision=AuthorityDecision.BLOCKED,
                    reasons=("candidate-pull-request-not-open",),
                    snapshot=snapshot,
                )
            )

        try:
            verdict = self._evaluator.evaluate(snapshot)
        except Exception:
            return self._record(
                AuthorityOutcome(
                    request=request,
                    decision=AuthorityDecision.BLOCKED,
                    reasons=("governance-evaluator-failed",),
                    snapshot=snapshot,
                )
            )

        return self._record(
            AuthorityOutcome(
                request=request,
                decision=verdict.decision,
                reasons=verdict.reasons,
                snapshot=snapshot,
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

    def _record(self, outcome: AuthorityOutcome) -> AuthorityOutcome:
        try:
            self._evidence.append(outcome)
        except Exception:
            return AuthorityOutcome(
                request=outcome.request,
                decision=AuthorityDecision.BLOCKED,
                reasons=("authority-evidence-write-failed",),
                snapshot=outcome.snapshot,
            )
        return outcome
