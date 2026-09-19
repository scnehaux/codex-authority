from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "governance" / "evidence" / "pr24-status-reconciliation-001.json"


class Pr24StatusReconciliationEvidenceTests(unittest.TestCase):
    def test_exact_provider_binding_and_conservative_claim(self):
        data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["kind"], "codex-status-reconciliation-publication-evidence")
        candidate = data["candidate"]
        self.assertEqual(candidate["repository"], "scnehaux/codex")
        self.assertEqual(candidate["pull_request"], 24)
        self.assertEqual(candidate["head_sha"], "3deeb147dc3cff647021357dfedf1fc3faf3bde4")
        self.assertEqual(candidate["merge_commit_sha"], "107f0dc53e873ef6d24a9f12cd28da7348f79331")
        provider = data["provider"]
        self.assertEqual(provider["ruleset_id"], 23193929)
        self.assertEqual(provider["required_check_app_id"], 4864946)
        self.assertEqual(provider["check_run_id"], 105959467617)
        self.assertEqual(provider["check_app_id"], 4864946)
        self.assertEqual(provider["check_conclusion"], "success")
        self.assertTrue(provider["token_revoked"])
        self.assertFalse(data["lifecycle"]["bootstrap_enabled"])
        self.assertTrue(data["lifecycle"]["permanent_runtime_promoted"])
        self.assertTrue(data["lifecycle"]["publication_disarmed_after_use"])
        self.assertTrue(data["claims"]["status_reconciliation_merge_proven"])
        self.assertFalse(data["claims"]["effective_enforcement_proven"])


if __name__ == "__main__":
    unittest.main()
