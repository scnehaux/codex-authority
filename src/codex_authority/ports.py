from __future__ import annotations

from typing import Protocol

from .model import CandidateRef, EvidenceRecord, RuntimeDecisionEnvelope


class TrustedRuntime(Protocol):
    def evaluate(self, request: CandidateRef) -> RuntimeDecisionEnvelope:
        """Run an independently promoted Codex runtime and return a verified envelope."""


class EvidenceSink(Protocol):
    def append(self, record: EvidenceRecord) -> None:
        """Persist or emit an append-only authority record."""
