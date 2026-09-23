from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "governance/evidence/phase11-slice11.6-publication-stop-001.json"


class Slice116PublicationStopTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_candidate_and_qualification_are_exactly_bound(self):
        candidate = self.record["candidate"]
        self.assertEqual(candidate["repository"], "scnehaux/codex")
        self.assertEqual(candidate["pull_request"], 32)
        self.assertEqual(candidate["base_sha"], "bfea97e841616a2880e28d2cfa177712209520f6")
        self.assertEqual(candidate["head_sha"], "fa733509974b048c587e9066690cfa7267313b77")
        self.assertEqual(candidate["changed_file_count"], 18)
        self.assertFalse(candidate["merged"])
        q = self.record["evaluation"]["qualification"]
        self.assertEqual(q["head_sha"], candidate["head_sha"])
        self.assertEqual(q["check_run_id"], 107343701998)
        self.assertEqual(q["conclusion"], "success")
        self.assertTrue(q["source_verified"])

    def test_pass_does_not_hide_original_privilege_failure(self):
        evaluation = self.record["evaluation"]
        self.assertEqual(evaluation["initial_decision"], "fail")
        self.assertEqual(evaluation["initial_reasons"], ["runtime-critical-mutation-requires-privileged-validation"])
        self.assertEqual(evaluation["after_attestation_decision"], "pass")
        self.assertEqual(evaluation["attestation_status"], "verified")
        self.assertFalse(evaluation["candidate_code_executed"])
        self.assertFalse(evaluation["credentials_used"])
        self.assertEqual(self.record["authority"]["attestation_merge_revision"], "49416a36cae7df0671cc307c5faf40ecf2a97f6d")

    def test_stopped_execution_is_not_a_publication_or_completion(self):
        publication = self.record["publication"]
        self.assertEqual(publication["status"], "not-published")
        self.assertFalse(publication["check_post_attempted"])
        self.assertIsNone(publication["check_run_id"])
        self.assertEqual(publication["observed_authority_check_count"], 0)
        self.assertEqual(publication["local_attempt_journal_count"], 0)
        self.assertFalse(publication["token_issued"])
        self.assertIsNone(publication["token_revoked"])
        self.assertFalse(publication["blind_retry_performed"])
        self.assertTrue(all(value is False for value in self.record["claims"].values()))

    def test_disarm_and_resume_boundaries_are_explicit(self):
        lifecycle = self.record["lifecycle"]
        self.assertEqual(lifecycle["checked_in_publication_target_state"], "disabled")
        self.assertIsNone(lifecycle["checked_in_activation_target"])
        self.assertTrue(lifecycle["exported_operational_copy_disabled"])
        self.assertTrue(lifecycle["resume_requires_new_separately_authorized_activation"])
        self.assertFalse(self.record["authority"]["privileged_bootstrap_enabled"])
        self.assertEqual(self.record["bundle"]["permit_digest"], "054a0b79f324caecb4093be4406fa874f02e348165087df04f7ecb991deb2e8e")


if __name__ == "__main__":
    unittest.main()
