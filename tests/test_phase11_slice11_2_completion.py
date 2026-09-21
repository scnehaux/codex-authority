from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "governance/evidence/phase11-slice11.2-completion-001.json"


class Slice112CompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_exact_candidate_and_merge(self):
        candidate = self.data["candidate"]
        self.assertEqual(candidate["pull_request"], 28)
        self.assertEqual(candidate["head_sha"], "fc75857f281641215db91b9fd2bcdb1ef5768a8b")
        self.assertEqual(candidate["merge_commit_sha"], "3ea9cb421dc5d44d57ca5242d06615fb1950758f")

    def test_publication_is_source_bound_and_revoked(self):
        publication = self.data["publication"]
        self.assertEqual(publication["check_run_id"], 106448709626)
        self.assertEqual(publication["app_id"], 4864946)
        self.assertEqual(publication["conclusion"], "success")
        self.assertIs(publication["token_revoked"], True)
    def test_recovery_was_pre_side_effect_and_not_blind_retry(self):
        recovery = self.data["publisher_export_recovery"]
        self.assertIs(recovery["first_write_reached_durable_attempt"], False)
        self.assertIs(recovery["first_write_reached_key_or_network"], False)
        self.assertIs(recovery["object_byte_export_verified_before_retry"], True)
        self.assertIs(recovery["blind_retry"], False)
        self.assertEqual(recovery["recommendation_applied"], "REC-D-014")

    def test_post_merge_state_and_ci_are_green(self):
        post = self.data["post_merge"]
        self.assertEqual(post["observer_drift_state"], "aligned")
        self.assertEqual(post["observer_enforcement_state"], "active")
        self.assertEqual(post["observer_installed_state"], "installed")
        self.assertEqual(len(post["push_ci"]), 3)
        self.assertTrue(all(run["conclusion"] == "success" for run in post["push_ci"]))

    def test_scope_claims_do_not_overstate_phase(self):
        claims = self.data["claims"]
        self.assertIs(claims["slice11_2_completed"], True)
        self.assertIs(claims["artifact_layout_lifecycle_runtime_authority_migrated"], True)
        self.assertIs(claims["relationship_runtime_authority_migrated"], False)
        self.assertIs(claims["executable_framework_compiled"], False)
        self.assertIs(claims["phase11_completed"], False)
    def test_framework_boundary_names_next_migration(self):
        framework = self.data["framework"]
        self.assertEqual(
            framework["runtime_authority"],
            "declarative-artifact-lifecycle-python-relationships-until-11.3",
        )
        self.assertEqual(
            framework["canonical_sha256"],
            "051625a811cb91f1d920af3fb66fe716a48ff7b498e5df7b23fdee374d1544e7",
        )

    def test_completion_record_captures_disarm_without_freezing_future_config(self):
        lifecycle = self.data["lifecycle"]
        self.assertEqual(lifecycle["checked_in_publication_target_state"], "disabled")
        self.assertIsNone(lifecycle["checked_in_activation_target"])
        self.assertIs(lifecycle["disarm_requires_this_pr_merge"], True)
        self.assertIs(self.data["claims"]["publication_standing_capability"], False)

    def test_privileged_bootstrap_remains_disabled(self):
        maintenance = json.loads(
            (ROOT / "governance/privileged-maintenance.json").read_text(encoding="utf-8")
        )
        self.assertIs(maintenance["bootstrap"]["enabled"], False)


if __name__ == "__main__":
    unittest.main()
