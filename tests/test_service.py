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
    RuntimeDecisionEnvelope,
)
from codex_authority.policy import load_authority_policy  # noqa: E402
from codex_authority.service import AuthorityService  # noqa: E402


BASE = "1" * 40
HEAD = "2" * 40
OTHER = "3" * 40
RUNTIME = "4" * 40
EVALUATOR = "5" * 40


class Runtime:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = 0

    def evaluate(self, request):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


class Evidence:
    def __init__(self, fail=False):
        self.fail = fail
        self.records = []

    def append(self, record):
        if self.fail:
            raise OSError("unavailable")
        self.records.append(record)


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


def envelope(
    *,
    candidate=None,
    decision=AuthorityDecision.PASS,
    reasons=(),
):
    return RuntimeDecisionEnvelope(
        snapshot=candidate or snapshot(),
        decision=decision,
        reasons=reasons,
        runtime_source_revision=RUNTIME,
        evaluator_source_revision=EVALUATOR,
        source_identity_verified=True,
        facts_collected_independently=True,
        candidate_code_executed=False,
        credentials_used=False,
    )


class AuthorityServiceTests(unittest.TestCase):
    def setUp(self):
        self.policy = load_authority_policy(ROOT / "governance/authority.json")

    def service(self, runtime, evidence=None):
        return AuthorityService(
            self.policy,
            runtime,
            evidence or Evidence(),
        )

    def test_authorized_open_candidate_can_pass_after_evidence_is_recorded(self):
        runtime = Runtime(envelope())
        evidence = Evidence()
        outcome = self.service(runtime, evidence).evaluate(request())

        self.assertEqual(outcome.decision, AuthorityDecision.PASS)
        self.assertTrue(outcome.evidence_recorded)
        self.assertEqual(outcome.runtime_source_revision, RUNTIME)
        self.assertEqual(outcome.evaluator_source_revision, EVALUATOR)
        self.assertFalse(hasattr(outcome, "publishable_success"))
        self.assertEqual(len(evidence.records), 1)

    def test_unknown_repository_is_blocked_without_runtime_execution(self):
        runtime = Runtime(envelope())
        outcome = self.service(runtime).evaluate(request(repository="other/repo"))

        self.assertEqual(outcome.decision, AuthorityDecision.BLOCKED)
        self.assertEqual(outcome.reasons, ("candidate-repository-not-authorized",))
        self.assertEqual(runtime.calls, 0)

    def test_runtime_failure_is_blocked(self):
        runtime = Runtime(error=OSError("github unavailable"))
        outcome = self.service(runtime).evaluate(request())

        self.assertEqual(outcome.decision, AuthorityDecision.BLOCKED)
        self.assertEqual(outcome.reasons, ("trusted-runtime-failed",))

    def test_malformed_runtime_return_is_blocked(self):
        runtime = Runtime(result=None)
        outcome = self.service(runtime).evaluate(request())

        self.assertEqual(outcome.decision, AuthorityDecision.BLOCKED)
        self.assertEqual(outcome.reasons, ("trusted-runtime-invalid-output",))

    def test_exact_head_binding_is_required(self):
        runtime = Runtime(envelope(candidate=snapshot(head_sha=OTHER)))
        outcome = self.service(runtime).evaluate(request())

        self.assertEqual(outcome.decision, AuthorityDecision.BLOCKED)
        self.assertEqual(outcome.reasons, ("candidate-head-identity-mismatch",))

    def test_closed_pull_request_is_blocked(self):
        runtime = Runtime(envelope(candidate=snapshot(state="closed")))
        outcome = self.service(runtime).evaluate(request())

        self.assertEqual(outcome.decision, AuthorityDecision.BLOCKED)
        self.assertEqual(outcome.reasons, ("candidate-pull-request-not-open",))

    def test_runtime_fail_verdict_is_preserved(self):
        runtime = Runtime(
            envelope(
                decision=AuthorityDecision.FAIL,
                reasons=("candidate-qualification-failed",),
            )
        )
        outcome = self.service(runtime).evaluate(request())

        self.assertEqual(outcome.decision, AuthorityDecision.FAIL)
        self.assertEqual(outcome.reasons, ("candidate-qualification-failed",))
        self.assertTrue(outcome.evidence_recorded)

    def test_evidence_failure_cannot_return_pass(self):
        runtime = Runtime(envelope())
        outcome = self.service(runtime, Evidence(fail=True)).evaluate(request())

        self.assertEqual(outcome.decision, AuthorityDecision.BLOCKED)
        self.assertEqual(outcome.reasons, ("authority-evidence-write-failed",))
        self.assertFalse(outcome.evidence_recorded)


if __name__ == "__main__":
    unittest.main()
