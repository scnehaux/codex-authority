from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "governance/evidence/phase11-slice11.3-completion-001.json"


class Slice113CompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_exact_candidate_and_merge(self):
        candidate = self.data["candidate"]
        self.assertEqual(candidate["pull_request"], 29)
        self.assertEqual(
            candidate["head_sha"],
            "da5294a8d90e2a94b68dd897e0729236bfc85ada",
        )
        self.assertEqual(
            candidate["merge_commit_sha"],
            "c26a80d791be2c65b3b4c628435a1e4ee1fdc4c4",
        )
    def test_publication_is_exact_app_success_and_revoked(self):
        publication = self.data["publication"]
        self.assertEqual(publication["check_run_id"], 106464580892)
        self.assertEqual(publication["app_id"], 4864946)
        self.assertEqual(publication["app_slug"], "scnehaux-codex-authority")
        self.assertEqual(publication["conclusion"], "success")
        self.assertIs(publication["token_revoked"], True)

    def test_framework_records_relationship_cutover(self):
        framework = self.data["framework"]
        self.assertEqual(
            framework["canonical_sha256"],
            "ca26aeaa2ebfdcc046c96061d741c01ac8ef65dc9e32d6015d9d3f151ae012bc",
        )
        self.assertEqual(
            framework["relationship_ontology_sha256"],
            "7fa6c8a1114986f6a3d2095933b0f3cd8536f3012bedeb751438bf4ed4189e07",
        )
        self.assertEqual(
            framework["runtime_authority"],
            "declarative-artifact-lifecycle-relationships-until-11.4",
        )
    def test_scope_claims_do_not_overstate_phase(self):
        claims = self.data["claims"]
        self.assertIs(claims["slice11_3_completed"], True)
        self.assertIs(
            claims["artifact_layout_lifecycle_runtime_authority_migrated"], True
        )
        self.assertIs(claims["relationship_runtime_authority_migrated"], True)
        self.assertIs(claims["executable_framework_compiled"], False)
        self.assertIs(claims["phase11_completed"], False)
        self.assertIs(claims["publication_standing_capability"], False)

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
