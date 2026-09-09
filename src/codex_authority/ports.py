from __future__ import annotations

from typing import Protocol

from .model import AuthorityOutcome, CandidateRef, CandidateSnapshot, EvaluationVerdict


class CandidateCollector(Protocol):
    def collect(self, request: CandidateRef) -> CandidateSnapshot:
        """Collect independently observed candidate facts."""


class GovernanceEvaluator(Protocol):
    def evaluate(self, snapshot: CandidateSnapshot) -> EvaluationVerdict:
        """Evaluate a verified candidate snapshot without publishing."""


class EvidenceSink(Protocol):
    def append(self, outcome: AuthorityOutcome) -> None:
        """Persist or emit an append-only authority outcome."""
