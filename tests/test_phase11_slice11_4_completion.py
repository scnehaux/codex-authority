from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "governance/evidence/phase11-slice11.4-completion-001.json"


class Slice114CompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_exact_candidate_and_merge(self):
        candidate = self.data["candidate"]
        self.assertEqual(candidate["pull_request"], 30)
        self.assertEqual(candidate["head_sha"], "a4e8454588aed0a6393774141d09593c61298e0e")
        self.assertEqual(candidate["merge_commit_sha"], "f71a51f38aba87a33d8a529400bde6584c9d403d")

    def test_publication_is_exact_app_success_and_revoked(self):
        publication = self.data["publication"]
        self.assertEqual(publication["check_run_id"], 106484885476)
        self.assertEqual(publication["app_id"], 4864946)
        self.assertEqual(publication["conclusion"], "success")
        self.assertIs(publication["token_revoked"], True)
    def test_compiled_framework_identity_is_recorded(self):
        framework = self.data["framework"]
        self.assertEqual(
            framework["contract_sha256"],
            "cbaebcf32b9391eb3d2cf8cbc6d508141006c83307c4165772008c4217a8c2ef",
        )
        self.assertEqual(
            framework["semantic_sha256"],
            "6f7e79c82aea1342d7f8eed9d2181383bb52b349f30af3cdf7ea3c609cf14980",
        )
        self.assertEqual(framework["runtime_authority"], "executable-framework")

    def test_scope_claims_do_not_overstate_phase(self):
        claims = self.data["claims"]
        self.assertIs(claims["slice11_4_completed"], True)
        self.assertIs(claims["executable_framework_compiled"], True)
        self.assertIs(claims["single_framework_runtime_composition_root"], True)
        self.assertIs(claims["schema_boundary_slice_completed"], False)
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
