from __future__ import annotations

import json
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
)
from codex_authority.publication import (  # noqa: E402
    PublicationPermit,
    issue_publication_permit,
)


BASE = "1" * 40
HEAD = "2" * 40
RUNTIME = "cbd64f78c8f72f28880d4673729a796b249d8eae"
EVALUATOR = "23b05a855419b86b61b0c9266805bb66b143c366"
AUTHORITY = "5" * 40


def passing_outcome(*, request: CandidateRef | None = None, snapshot: CandidateSnapshot | None = None):
    request = request or CandidateRef("scnehaux/codex", 17, HEAD)
    snapshot = snapshot or CandidateSnapshot(
        repository="scnehaux/codex",
        pull_request=17,
        base_sha=BASE,
        head_sha=HEAD,
        state="open",
        changed_files=("README.md",),
    )
    return AuthorityOutcome(
        request=request,
        decision=AuthorityDecision.PASS,
        reasons=(),
        snapshot=snapshot,
        runtime_source_revision=RUNTIME,
        evaluator_source_revision=EVALUATOR,
        evidence_recorded=True,
    )


class PublicationPermitTests(unittest.TestCase):
    def test_evidenced_pass_issues_exact_success_only_permit(self):
        permit = issue_publication_permit(
            passing_outcome(), authority_service_source_revision=AUTHORITY
        )
        self.assertIsNotNone(permit)
        assert permit is not None
        self.assertEqual(permit.candidate.repository, "scnehaux/codex")
        self.assertEqual(permit.candidate.head_sha, HEAD)
        self.assertEqual(permit.base_sha, BASE)
        self.assertEqual(permit.runtime_source_revision, RUNTIME)
        self.assertEqual(permit.evaluator_source_revision, EVALUATOR)
        self.assertEqual(permit.authority_service_source_revision, AUTHORITY)
        self.assertEqual(permit.decision, AuthorityDecision.PASS)
        self.assertEqual(permit.check_context, "Codex Governance Authority")
        self.assertEqual(permit.expected_integration_id, 4864946)
        self.assertEqual(permit.conclusion, "success")
        self.assertEqual(len(permit.digest), 64)

    def test_json_round_trip_is_strict_and_digest_stable(self):
        permit = issue_publication_permit(
            passing_outcome(), authority_service_source_revision=AUTHORITY
        )
        assert permit is not None
        restored = PublicationPermit.from_json(permit.to_json())
        self.assertEqual(restored, permit)
        self.assertEqual(restored.digest, permit.digest)

    def test_extra_or_mutated_capability_fields_fail_closed(self):
        permit = issue_publication_permit(
            passing_outcome(), authority_service_source_revision=AUTHORITY
        )
        assert permit is not None
        data = permit.to_mapping()
        cases = []
        extra = json.loads(json.dumps(data))
        extra["candidate"]["ref"] = "main"
        cases.append(extra)
        fail = json.loads(json.dumps(data))
        fail["decision"] = "fail"
        cases.append(fail)
        context = json.loads(json.dumps(data))
        context["publication"]["check_context"] = "Anything Else"
        cases.append(context)
        app = json.loads(json.dumps(data))
        app["publication"]["expected_integration_id"] = 1
        cases.append(app)
        evidence = json.loads(json.dumps(data))
        evidence["evidence"]["recorded"] = False
        cases.append(evidence)
        for mutated in cases:
            with self.subTest(mutated=mutated):
                with self.assertRaises(ValueError):
                    PublicationPermit.from_mapping(mutated)

    def test_non_passing_or_wrong_identity_never_issues_permit(self):
        failed = AuthorityOutcome(
            request=CandidateRef("scnehaux/codex", 17, HEAD),
            decision=AuthorityDecision.FAIL,
            reasons=("policy-failed",),
            evidence_recorded=True,
        )
        self.assertIsNone(
            issue_publication_permit(failed, authority_service_source_revision=AUTHORITY)
        )

        mismatch = passing_outcome(
            request=CandidateRef("scnehaux/codex", 17, "6" * 40)
        )
        self.assertIsNone(
            issue_publication_permit(mismatch, authority_service_source_revision=AUTHORITY)
        )

        closed = passing_outcome(
            snapshot=CandidateSnapshot(
                repository="scnehaux/codex",
                pull_request=17,
                base_sha=BASE,
                head_sha=HEAD,
                state="closed",
                changed_files=("README.md",),
            )
        )
        self.assertIsNone(
            issue_publication_permit(closed, authority_service_source_revision=AUTHORITY)
        )

    def test_authority_service_source_identity_is_mandatory(self):
        self.assertIsNone(
            issue_publication_permit(
                passing_outcome(), authority_service_source_revision="main"
            )
        )


if __name__ == "__main__":
    unittest.main()
