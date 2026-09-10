from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from codex_authority.model import AuthorityDecision, CandidateRef  # noqa: E402
from codex_authority.adapters import promoted_runtime as target  # noqa: E402


BASE = "1" * 40
HEAD = "2" * 40


def result(*, decision="pass", evaluator_reasons=None, runtime_reasons=None):
    evaluator_reasons = [] if evaluator_reasons is None else evaluator_reasons
    runtime_reasons = [] if runtime_reasons is None else runtime_reasons
    return {
        "schema_version": 1,
        "status": "runtime_evaluation_complete",
        "repository": "scnehaux/codex",
        "pull_request": 17,
        "base_sha": BASE,
        "candidate_sha": HEAD,
        "authority_source_revision": target.EVALUATOR_SOURCE_REVISION,
        "runtime_source_promoted": False,
        "facts_collected_independently": True,
        "facts_provenance_verified": False,
        "candidate_manifest": {
            "schema_version": 1,
            "repository": "scnehaux/codex",
            "pull_request": 17,
            "base_sha": BASE,
            "head_sha": HEAD,
            "changed_files": [".gitignore"],
        },
        "collected_facts": {"schema_version": 1},
        "candidate_evidence": {
            "source": "github-pull-request-api",
            "pull_state": "open",
            "base_ref": "main",
            "identity_verified": True,
            "changed_files_verified": True,
        },
        "qualification_evidence": {
            "source": "github-checks-api",
            "name": "Governance Qualification",
            "head_sha": HEAD,
            "status": "completed",
            "conclusion": "success" if decision == "pass" else "failure",
            "app_id": 15368,
            "app_slug": "github-actions",
            "source_verified": True,
        },
        "runtime_only_protected_mutations": [],
        "runtime_failure_reasons": runtime_reasons,
        "evaluator_result": {
            "governance_decision": decision,
            "failure_reasons": evaluator_reasons,
        },
        "governance_decision": decision,
        "candidate_code_executed": False,
        "credentials_used": False,
        "publish_enabled": False,
        "authority_binding_advanced": False,
        "effective_enforcement_proven": False,
        "notice": "conservative promoted runtime self-report",
    }


class PromotedRuntimeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.request = CandidateRef("scnehaux/codex", 17, HEAD)

    def test_pass_maps_to_verified_authority_envelope(self):
        envelope = target._parse_runtime_result(result(), self.request)
        self.assertEqual(envelope.decision, AuthorityDecision.PASS)
        self.assertEqual(envelope.reasons, ())
        self.assertEqual(envelope.snapshot.base_sha, BASE)
        self.assertEqual(envelope.snapshot.changed_files, (".gitignore",))
        self.assertEqual(
            envelope.runtime_source_revision,
            target.RUNTIME_SOURCE_REVISION,
        )
        self.assertEqual(
            envelope.evaluator_source_revision,
            target.EVALUATOR_SOURCE_REVISION,
        )
        self.assertTrue(envelope.source_identity_verified)
        self.assertTrue(envelope.facts_collected_independently)
        self.assertFalse(envelope.candidate_code_executed)
        self.assertFalse(envelope.credentials_used)

    def test_fail_preserves_deterministic_failure_reasons(self):
        envelope = target._parse_runtime_result(
            result(
                decision="fail",
                evaluator_reasons=["qualification-failed"],
                runtime_reasons=["runtime-policy-failed"],
            ),
            self.request,
        )
        self.assertEqual(envelope.decision, AuthorityDecision.FAIL)
        self.assertEqual(
            envelope.reasons,
            ("qualification-failed", "runtime-policy-failed"),
        )

    def test_exact_candidate_and_conservative_flags_are_required(self):
        cases = [
            ("candidate_sha", "3" * 40),
            ("facts_collected_independently", False),
            ("candidate_code_executed", True),
            ("credentials_used", True),
            ("runtime_source_promoted", True),
            ("publish_enabled", True),
        ]
        for field, value in cases:
            with self.subTest(field=field):
                payload = result()
                payload[field] = value
                with self.assertRaises(target.RuntimeAdapterError):
                    target._parse_runtime_result(payload, self.request)

    def test_pass_cannot_hide_failure_reasons(self):
        with self.assertRaises(target.RuntimeAdapterError):
            target._parse_runtime_result(
                result(evaluator_reasons=["hidden-failure"]),
                self.request,
            )

    def test_exported_runtime_requires_exact_raw_blobs(self):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp) / "runtime"
            package.mkdir()
            for name in ("runtime.py", "evaluator.py", "promotion.json"):
                (package / name).write_text("fixture", encoding="utf-8")
            (package / "runtime-promotion.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "repository": target.REPOSITORY,
                        "runtime_source_revision": target.RUNTIME_SOURCE_REVISION,
                        "runtime_source_path": "integrations/github-governance-evaluator/runtime.py",
                        "runtime_source_blob": target.RUNTIME_SOURCE_BLOB,
                        "evaluator_source_revision": target.EVALUATOR_SOURCE_REVISION,
                        "evaluator_source_blob": target.EVALUATOR_SOURCE_BLOB,
                        "promotion": {
                            "mode": "privileged-explicit",
                            "state": "runtime-source-pinned",
                            "candidate_may_select_effective_revision": False,
                            "auto_deploy_from_candidate": False,
                        },
                        "runtime": {
                            "execution_location": "external",
                            "exported_copy_required": True,
                            "live_instance_proven": False,
                            "facts_provenance_verified": False,
                            "publish_enabled": False,
                            "authority_binding_advanced": False,
                            "effective_enforcement_proven": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            with (
                patch.object(target, "_inside_git", return_value=False),
                patch.object(
                    target,
                    "_git_blob_sha",
                    side_effect=[
                        target.RUNTIME_SOURCE_BLOB,
                        target.EVALUATOR_SOURCE_BLOB,
                    ],
                ),
            ):
                target.verify_exported_runtime(package)

            with (
                patch.object(target, "_inside_git", return_value=False),
                patch.object(target, "_git_blob_sha", return_value="0" * 40),
            ):
                with self.assertRaises(target.RuntimeAdapterError):
                    target.verify_exported_runtime(package)

    def test_runtime_adapter_contract_matches_promoted_codex_identity(self):
        contract = json.loads(
            (ROOT / "governance/runtime-adapter.json").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["candidate_repository"], target.REPOSITORY)
        self.assertEqual(
            contract["runtime"]["source_revision"],
            target.RUNTIME_SOURCE_REVISION,
        )
        self.assertEqual(
            contract["runtime"]["source_blob"],
            target.RUNTIME_SOURCE_BLOB,
        )
        self.assertEqual(
            contract["evaluator"]["source_revision"],
            target.EVALUATOR_SOURCE_REVISION,
        )
        self.assertEqual(
            contract["evaluator"]["source_blob"],
            target.EVALUATOR_SOURCE_BLOB,
        )
        self.assertFalse(contract["execution"]["credentials_allowed"])
        self.assertFalse(contract["execution"]["candidate_code_execution"])
        self.assertTrue(contract["permit_issuance"]["durable_evidence_before_permit"])


if __name__ == "__main__":
    unittest.main()
