from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from codex_authority.model import (  # noqa: E402
    AuthorityDecision,
    AuthorityOutcome,
    CandidateRef,
    CandidateSnapshot,
    RuntimeDecisionEnvelope,
)


BASE = "1" * 40
HEAD = "2" * 40
RUNTIME = "3" * 40
EVALUATOR = "4" * 40


def snapshot(*, changed_files=("README.md",)):
    return CandidateSnapshot(
        repository="scnehaux/codex",
        pull_request=17,
        base_sha=BASE,
        head_sha=HEAD,
        state="open",
        changed_files=changed_files,
    )


def envelope(**overrides):
    values = {
        "snapshot": snapshot(),
        "decision": AuthorityDecision.PASS,
        "reasons": (),
        "runtime_source_revision": RUNTIME,
        "evaluator_source_revision": EVALUATOR,
        "source_identity_verified": True,
        "facts_collected_independently": True,
        "candidate_code_executed": False,
        "credentials_used": False,
    }
    values.update(overrides)
    return RuntimeDecisionEnvelope(**values)


class ModelInvariantTests(unittest.TestCase):
    def test_runtime_envelope_requires_verified_source_identity(self):
        with self.assertRaises(ValueError):
            envelope(source_identity_verified=False)

    def test_runtime_envelope_forbids_candidate_execution(self):
        with self.assertRaises(ValueError):
            envelope(candidate_code_executed=True)

    def test_runtime_envelope_forbids_credentials_in_evaluation_runtime(self):
        with self.assertRaises(ValueError):
            envelope(credentials_used=True)

    def test_runtime_envelope_requires_independent_facts(self):
        with self.assertRaises(ValueError):
            envelope(facts_collected_independently=False)

    def test_runtime_envelope_cannot_be_blocked(self):
        with self.assertRaises(ValueError):
            envelope(decision=AuthorityDecision.BLOCKED)

    def test_candidate_snapshot_rejects_parent_traversal(self):
        with self.assertRaises(ValueError):
            snapshot(changed_files=("../secret",))

    def test_candidate_snapshot_rejects_duplicate_paths(self):
        with self.assertRaises(ValueError):
            snapshot(changed_files=("README.md", "README.md"))

    def test_passing_outcome_requires_durable_evidence(self):
        request = CandidateRef("scnehaux/codex", 17, HEAD)
        with self.assertRaises(ValueError):
            AuthorityOutcome(
                request=request,
                decision=AuthorityDecision.PASS,
                reasons=(),
                snapshot=snapshot(),
                runtime_source_revision=RUNTIME,
                evaluator_source_revision=EVALUATOR,
                evidence_recorded=False,
            )


if __name__ == "__main__":
    unittest.main()
