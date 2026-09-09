from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from codex_authority.model import (  # noqa: E402
    AuthorityDecision,
    CandidateRef,
    CandidateSnapshot,
    EvaluationVerdict,
)
from codex_authority.policy import load_authority_policy  # noqa: E402
from codex_authority.service import AuthorityService  # noqa: E402


BASE = "1" * 40
HEAD = "2" * 40
OTHER = "3" * 40


class Collector:
    def __init__(self, snapshot=None, error=None):
        self.snapshot = snapshot
        self.error = error
        self.calls = 0

    def collect(self, request):
        self.calls += 1
        if self.error:
            raise self.error
        return self.snapshot


class Evaluator:
    def __init__(self, verdict=None, error=None):
        self.verdict = verdict
        self.error = error
        self.calls = 0

    def evaluate(self, snapshot):
        self.calls += 1
        if self.error:
            raise self.error
        return self.verdict


class Evidence:
    def __init__(self, fail=False):
        self.fail = fail
        self.records = []

    def append(self, outcome):
        if self.fail:
            raise OSError("unavailable")
        self.records.append(outcome)


def snapshot(
    *, repository="scnehaux/codex", pull_request=17, head_sha=HEAD, state="open"
):
    return CandidateSnapshot(
        repository=repository,
        pull_request=pull_request,
        base_sha=BASE,
        head_sha=head_sha,
        state=state,
        changed_files=("README.md",),
    )


def request(*, repository="scnehaux/codex", pull_request=17, head_sha=HEAD):
    return CandidateRef(repository, pull_request, head_sha)


class AuthorityServiceTests(unittest.TestCase):
    def setUp(self):
        self.policy = load_authority_policy(ROOT / "governance/authority.json")

    def service(self, collector, evaluator, evidence=None):
        return AuthorityService(
            self.policy,
            collector,
            evaluator,
            evidence or Evidence(),
        )

    def test_authorized_open_candidate_can_pass(self):
        collector = Collector(snapshot())
        evaluator = Evaluator(EvaluationVerdict(AuthorityDecision.PASS))
        evidence = Evidence()
        outcome = self.service(collector, evaluator, evidence).evaluate(request())

        self.assertEqual(outcome.decision, AuthorityDecision.PASS)
        self.assertTrue(outcome.publishable_success)
        self.assertEqual(len(evidence.records), 1)

    def test_unknown_repository_is_blocked_without_collection(self):
        collector = Collector(snapshot())
        evaluator = Evaluator(EvaluationVerdict(AuthorityDecision.PASS))
        outcome = self.service(collector, evaluator).evaluate(
            request(repository="other/repo")
        )

        self.assertEqual(outcome.decision, AuthorityDecision.BLOCKED)
        self.assertEqual(outcome.reasons, ("candidate-repository-not-authorized",))
        self.assertEqual(collector.calls, 0)
        self.assertEqual(evaluator.calls, 0)

    def test_collector_failure_is_blocked(self):
        collector = Collector(error=OSError("github unavailable"))
        evaluator = Evaluator(EvaluationVerdict(AuthorityDecision.PASS))
        outcome = self.service(collector, evaluator).evaluate(request())

        self.assertEqual(outcome.decision, AuthorityDecision.BLOCKED)
        self.assertEqual(outcome.reasons, ("candidate-facts-collection-failed",))
        self.assertEqual(evaluator.calls, 0)

    def test_exact_head_binding_is_required(self):
        collector = Collector(snapshot(head_sha=OTHER))
        evaluator = Evaluator(EvaluationVerdict(AuthorityDecision.PASS))
        outcome = self.service(collector, evaluator).evaluate(request())

        self.assertEqual(outcome.decision, AuthorityDecision.BLOCKED)
        self.assertEqual(outcome.reasons, ("candidate-head-identity-mismatch",))
        self.assertEqual(evaluator.calls, 0)

    def test_closed_pull_request_is_blocked(self):
        collector = Collector(snapshot(state="closed"))
        evaluator = Evaluator(EvaluationVerdict(AuthorityDecision.PASS))
        outcome = self.service(collector, evaluator).evaluate(request())

        self.assertEqual(outcome.decision, AuthorityDecision.BLOCKED)
        self.assertEqual(outcome.reasons, ("candidate-pull-request-not-open",))
        self.assertEqual(evaluator.calls, 0)

    def test_evaluator_failure_is_blocked(self):
        collector = Collector(snapshot())
        evaluator = Evaluator(error=RuntimeError("broken evaluator"))
        outcome = self.service(collector, evaluator).evaluate(request())

        self.assertEqual(outcome.decision, AuthorityDecision.BLOCKED)
        self.assertEqual(outcome.reasons, ("governance-evaluator-failed",))

    def test_evidence_failure_cannot_return_pass(self):
        collector = Collector(snapshot())
        evaluator = Evaluator(EvaluationVerdict(AuthorityDecision.PASS))
        outcome = self.service(collector, evaluator, Evidence(fail=True)).evaluate(
            request()
        )

        self.assertEqual(outcome.decision, AuthorityDecision.BLOCKED)
        self.assertEqual(outcome.reasons, ("authority-evidence-write-failed",))
        self.assertFalse(outcome.publishable_success)


if __name__ == "__main__":
    unittest.main()
