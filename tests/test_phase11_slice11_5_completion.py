from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "governance/evidence/phase11-slice11.5-completion-001.json"


class Slice115CompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_exact_candidate_and_merge(self):
        candidate = self.data["candidate"]
        self.assertEqual(candidate["pull_request"], 31)
        self.assertEqual(
            candidate["head_sha"],
            "6adf528b294360a0253b7f2f9fef8d95e6aedce6",
        )
        self.assertEqual(
            candidate["merge_commit_sha"],
            "bfea97e841616a2880e28d2cfa177712209520f6",
        )
    def test_publication_is_exact_app_success_and_revoked(self):
        publication = self.data["publication"]
        self.assertEqual(publication["check_run_id"], 107120857771)
        self.assertEqual(publication["app_id"], 4864946)
        self.assertEqual(publication["app_slug"], "scnehaux-codex-authority")
        self.assertEqual(publication["conclusion"], "success")
        self.assertIs(publication["token_revoked"], True)

    def test_schema_and_candidate_boundaries_are_recorded(self):
        boundary = self.data["validation_boundary"]
        self.assertIs(boundary["json_schema_structural_only"], True)
        self.assertIs(boundary["runtime_policy_from_executable_framework"], True)
        self.assertIs(boundary["typed_source_document"], True)
        self.assertIs(boundary["typed_parsed_artifact"], True)
        self.assertIs(boundary["typed_artifact_candidate"], True)
        self.assertIs(boundary["deterministic_validation_report"], True)
        self.assertIs(boundary["invalid_candidate_promotion_blocked"], True)
        self.assertIs(boundary["repository_model_requires_promoted_candidates"], True)
    def test_scope_claims_do_not_overstate_phase(self):
        claims = self.data["claims"]
        self.assertIs(claims["slice11_5_completed"], True)
        self.assertIs(claims["schema_boundary_slice_completed"], True)
        self.assertIs(claims["candidate_validation_pipeline_established"], True)
        self.assertIs(claims["provenance_bound_git_ingestion_completed"], False)
        self.assertIs(claims["validated_repository_snapshot_completed"], False)
        self.assertIs(claims["phase11_completed"], False)
        self.assertIs(claims["publication_standing_capability"], False)

    def test_framework_identity_is_recorded(self):
        framework = self.data["framework"]
        self.assertEqual(
            framework["contract_sha256"],
            "817147fa79781ff593f59504ed01f6bd6272ec856715e5295568abb27c660333",
        )
        self.assertEqual(
            framework["semantic_sha256"],
            "2f8c498fbc951e756d1ca6e9179a967a966f9f8edf3b02b45ca62568a8fa3a65",
        )
        self.assertEqual(framework["runtime_authority"], "executable-framework")
    def test_post_merge_observer_and_ci_are_green(self):
        post = self.data["post_merge"]
        self.assertEqual(post["observer_installed_state"], "installed")
        self.assertEqual(post["observer_enforcement_state"], "active")
        self.assertEqual(post["observer_drift_state"], "aligned")
        self.assertEqual(len(post["push_ci"]), 3)
        self.assertTrue(all(run["conclusion"] == "success" for run in post["push_ci"]))

    def test_completion_record_captures_disarm_snapshot(self):
        lifecycle = self.data["lifecycle"]
        self.assertEqual(lifecycle["checked_in_publication_target_state"], "disabled")
        self.assertIsNone(lifecycle["checked_in_activation_target"])
        self.assertIs(lifecycle["disarm_requires_this_pr_merge"], True)

    def test_privileged_bootstrap_remains_disabled(self):
        maintenance = json.loads(
            (ROOT / "governance/privileged-maintenance.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIs(maintenance["bootstrap"]["enabled"], False)


if __name__ == "__main__":
    unittest.main()
