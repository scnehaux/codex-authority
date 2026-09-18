from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "governance" / "evidence" / "permanent-maintenance-proof-001.json"


class PermanentMaintenanceEvidenceTests(unittest.TestCase):
    def test_post_disarm_path_is_exact_and_effective_enforcement_stays_conservative(self):
        data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["kind"], "codex-permanent-maintenance-proof-evidence")
        self.assertEqual(data["candidate"]["pull_request"], 23)
        self.assertEqual(data["candidate"]["head_sha"], "d681a8f311cbb3a0bc69b795639112918e57a85f")
        self.assertEqual(data["candidate"]["merge_commit_sha"], "362d5c072fe407c915e2307bc455720739b20154")
        self.assertFalse(data["authority"]["bootstrap_enabled"])
        self.assertEqual(data["authority"]["mode"], "attested-v2")
        self.assertEqual(data["publication"]["check_run_id"], 105585648922)
        self.assertEqual(data["publication"]["app"]["id"], 4864946)
        self.assertEqual(data["publication"]["conclusion"], "success")
        self.assertTrue(data["publication"]["token_revoked"])
        self.assertTrue(data["provider_enforcement"]["merge_completed"])
        self.assertEqual(data["provider_enforcement"]["ruleset_id"], 23193929)
        self.assertEqual(data["provider_enforcement"]["required_check_integration_id"], 4864946)
        self.assertTrue(data["claims"]["privileged_governance_maintenance_path_proven"])
        self.assertFalse(data["claims"]["effective_enforcement_proven"])


if __name__ == "__main__":
    unittest.main()
